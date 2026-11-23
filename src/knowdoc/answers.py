import re
import time

from knowdoc.config import settings
from knowdoc.facts import extract_profile_fact
from knowdoc.providers import ProviderError, generate
from knowdoc.retrieval import search

UNSAFE_INSTRUCTION = re.compile(
    r"(?:ignore|override|disregard)\b.{0,100}\b(?:previous instructions|system prompt|system instructions)"
    r"|(?:reveal|exfiltrate|send)\b.{0,100}\b(?:credentials|secrets|private documents|api keys)"
    r"|(?:invent|forge)\b.{0,100}\bcitation"
    r"|claim\b.{0,50}\banswer is guaranteed",
    re.IGNORECASE | re.DOTALL,
)


def validate_claims(candidate: dict, passages: list[dict]) -> tuple[list[dict], bool]:
    if not isinstance(candidate, dict):
        return [], False
    lookup = {p["id"]: p for p in passages}
    claims = candidate.get("claims", [])
    if not isinstance(claims, list) or len(claims) > 12:
        return [], False
    checked = []
    for claim in claims:
        if not isinstance(claim, dict):
            return [], False
        ids, quote, text = claim.get("citation_ids"), claim.get("quote"), claim.get("text")
        if (not isinstance(ids, list) or not ids or not isinstance(quote, str)
                or len(quote.strip()) < 10 or not isinstance(text, str) or not text.strip()
                or any(not isinstance(i, str) or i not in lookup for i in ids)):
            return [], False
        # Source inspection remains intact. Do not promote a copied role/exfiltration
        # command into a generated factual claim. This narrow filter is not a complete
        # injection defense; authorization is enforced independently in SQL.
        if UNSAFE_INSTRUCTION.search(text) or UNSAFE_INSTRUCTION.search(quote):
            return [], False
        # Only whitespace may normalize. Resolve the actual stored span, never fuzzy wording.
        pattern = r"\s+".join(re.escape(token) for token in quote.split())
        spans = []
        for cid in ids:
            match = re.search(pattern, lookup[cid]["text"])
            if not match:
                return [], False
            spans.append({"citation_id": cid, "start": match.start(), "end": match.end(),
                          "quote": match[0], "offset_basis": "stored_chunk"})
        checked.append({"text": text[:3000], "citation_ids": ids, "quote": spans[0]["quote"],
                        "citation_spans": spans})
    return checked, True


def conflicts(passages: list[dict]) -> list[dict]:
    """Conservative numeric policy conflicts; this is not general contradiction detection.

    Only match identical sentence templates with differing numeric values and explicit units.
    Code blocks, dates, arbitrary similar sentences, and model-generated facts are not compared.
    """
    observed = {}
    found = []
    pattern = re.compile(r"\b([A-Z][A-Za-z -]{8,100}?(?:is|are|must be|shall be))\s+(\d+)\s+(days|hours|minutes|seconds|MB|GB)\b[^.\n]*\.")
    for passage in passages:
        for match in pattern.finditer(passage["text"]):
            key = (match[1].strip().lower(), match[3].lower())
            previous = observed.get(key)
            if previous and previous["value"] != match[2] and previous["id"] != passage["id"]:
                found.append({"citation_ids": [previous["id"], passage["id"]],
                              "quotes": [previous["quote"], match[0]],
                              "versions": [previous["version"], passage["version"]],
                              "reason": "Same policy statement has different numeric values; scope or versions may explain this."})
            observed[key] = {"value": match[2], "id": passage["id"], "version": passage["version"], "quote": match[0]}
    return found[:5]


def answer(db, user_id, question, *, mode="generate", **filters):
    started = time.perf_counter()
    result = search(db, user_id, question, **filters)
    passages = result["passages"]
    # A deterministic lexical relevance gate avoids sending unrelated dense-only hits to generation.
    words = set(re.findall(r"[a-z][a-z0-9_]{2,}", question.lower())) - {
        "what", "how", "the", "does", "are", "can", "for", "with", "which", "about", "and",
        "best", "better", "good", "should", "could", "would", "will", "your", "you", "our",
        "their", "its", "have", "has", "had", "this", "that", "there", "here", "any", "use"}
    relevant = [p for p in passages if words & set(re.findall(r"[a-z][a-z0-9_]{2,}", p["text"].lower()))]
    response = {"status": "insufficient_evidence", "answer": "The available evidence is insufficient to answer this question.",
                "answer_method": "evidence" if mode == "evidence" else ("hosted_model" if settings().generation_backend == "gateway" else "local_model"),
                "claims": [], "citations": [], "conflicts": [], "mode": mode, "usage": None,
                "limitations": ["Retrieval relevance and semantic support are fallible.",
                                "Version labels are declared source metadata; ingestion time does not prove currentness."],
                "timings": {"retrieval_ms": result["retrieval_ms"]}}
    fact = extract_profile_fact(question, passages) if mode == 'generate' else None
    if fact:
        claims, valid = validate_claims(fact, fact['citations'])
        if valid:
            response.update(fact, claims=claims, answer_method='extractive')
            response['timings']['total_ms'] = round((time.perf_counter() - started) * 1000, 2)
            return response
    if relevant:
        # Conservative fixed context budget; do not slice citation text or invent spans.
        selected, budget = [], 0
        for p in relevant:
            if budget + len(p["text"]) <= 11000:
                selected.append(p)
                budget += len(p["text"])
        detected = conflicts(selected)
        if detected:
            ids = {cid for conflict in detected for cid in conflict["citation_ids"]}
            response.update(status="conflicting_evidence", conflicts=detected,
                            answer="The retrieved sources contain potentially conflicting policy values. Compare the quoted passages and their versions before acting.",
                            citations=[p for p in selected if p["id"] in ids])
            response["limitations"].append("Conflict detection covers exact numeric policy templates only; it is not exhaustive.")
        elif mode == "evidence":
            response.update(status="evidence_only", answer="Relevant source passages are shown below. No generated answer was requested.",
                            citations=selected)
        else:
            if settings().generation_backend == "disabled":
                response.update(status="evidence_only", answer_method="evidence", citations=selected,
                                answer="General AI answers are not enabled on this free deployment. These source passages may help; exact supported profile facts can still be answered directly.")
                response["timings"]["total_ms"] = round((time.perf_counter() - started) * 1000, 2)
                return response
            try:
                candidate, usage = generate(question, selected)
                response["usage"] = usage
                claims, valid = validate_claims(candidate, selected)
                state = candidate.get("status") if isinstance(candidate, dict) else None
                if valid and claims and state in {"answered", "conflicting_evidence"}:
                    ids = {i for c in claims for i in c["citation_ids"]}
                    response.update(status=state, claims=claims,
                                    answer="\n\n".join(c["text"] for c in claims),
                                    citations=[p for p in selected if p["id"] in ids])
                elif state == "clarification_required" and valid:
                    response.update(status=state, answer="Please specify the document or version you want to compare.")
                elif not valid:
                    response["limitations"].append("Model output failed reference or unsafe-instruction checks and was rejected.")
            except ProviderError:
                raise
    response["timings"]["total_ms"] = round((time.perf_counter() - started) * 1000, 2)
    return response
