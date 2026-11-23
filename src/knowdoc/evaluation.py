"""Reproducible metrics. Deterministic proxies are never labelled human faithfulness."""
import hashlib
import json
import math
import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from sqlalchemy import select

from knowdoc.answers import answer
from knowdoc.config import settings
from knowdoc.db import session
from knowdoc.models import Chunk, Collection, Document, EvaluationRun, Version
from knowdoc.providers import ProviderError, embedding_identity
from knowdoc.retrieval import search


def metrics(retrieved: list[str], gold: set[str], k=5):
    hits = [1 if cid in gold else 0 for cid in retrieved[:k]]
    recall = sum(hits) / len(gold) if gold else 0
    mrr = next((1 / (i + 1) for i, hit in enumerate(hits) if hit), 0)
    dcg = sum(hit / math.log2(i + 2) for i, hit in enumerate(hits))
    ideal = sum(1 / math.log2(i + 2) for i in range(min(k, len(gold))))
    return {"recall_at_5": recall, "mrr": mrr, "ndcg_at_5": dcg / ideal if ideal else 0}


def run_evaluation(owner_id: str, *, generation_limit=5, methods=None) -> dict:
    if methods is None:
        methods = ["keyword", "dense", "hybrid", "hybrid_rerank"]
    raw = Path("evals/benchmark.json").read_bytes()
    dataset = json.loads(raw)
    rows, behavior, failures = [], [], []
    generations = 0
    with session() as db:
        corpus = db.scalar(select(Collection).where(Collection.owner_id == owner_id, Collection.name == "PostgreSQL · versioned reference"))
        originals = db.scalar(select(Collection).where(Collection.owner_id == owner_id, Collection.name == "Original evaluation fixtures"))
        if not corpus or not originals:
            raise ValueError("benchmark_corpus_and_fixtures_required")
        for index, case in enumerate(dataset["cases"], 1):
            category = case["category"]
            filters = {"collection_id": corpus.id if category in {"answerable", "version_specific", "unanswerable"} else originals.id}
            if category == "permission_isolation":
                hidden_id = db.scalar(select(Document.id).where(Document.title == case["hidden_document"], Document.owner_id != owner_id))
                if not hidden_id:
                    raise ValueError("missing_private_evaluation_fixture")
                filters = {"document_id": hidden_id}
            title = case.get("document_filter")
            if title:
                document = db.scalar(select(Document).where(Document.title == title, Document.owner_id == owner_id))
                if not document:
                    raise ValueError("missing_evaluation_fixture")
                filters["document_id"] = document.id
            if case.get("version_filter"):
                filters["version_ids"] = list(db.scalars(select(Version.id).join(Document).where(
                    Document.owner_id == owner_id, Version.label == case["version_filter"])))
            gold_ids = set()
            for gold in case["gold"]:
                gold_ids.update(db.scalars(select(Chunk.id).join(Version, Chunk.version_id == Version.id).join(
                    Document, Version.document_id == Document.id).where(
                        Document.owner_id == owner_id, Document.title == gold["document"],
                        Version.label == gold["version"], Chunk.generation == Version.active_generation,
                        Chunk.text.contains(gold["quote"], autoescape=True))))
            if category in {"answerable", "version_specific"}:
                if not gold_ids:
                    raise ValueError(f"gold_evidence_not_indexed:{case['id']}")
                for method in methods:
                    try:
                        result = search(db, owner_id, case["question"], method=method, top_k=5, **filters)
                        ids = [p["id"] for p in result["passages"]]
                        row = {"case_id": case["id"], "category": category, "method": method,
                               **metrics(ids, gold_ids), "latency_ms": result["retrieval_ms"],
                               "retrieved_ids": ids, "gold_ids": sorted(gold_ids), "error": None}
                        if not set(ids) & gold_ids:
                            failures.append({"case_id": case["id"], "method": method, "reason": "gold_passage_missing_at_5"})
                    except ProviderError as exc:
                        row = {"case_id": case["id"], "method": method, "error": str(exc)}
                    rows.append(row)
            # Full grounded pipeline on a bounded subset plus every adversarial/abstention case.
            should_generate = (category in {"answerable", "version_specific"} and generations < generation_limit) or category == "prompt_injection"
            if should_generate or category in {"unanswerable", "conflicting_source", "permission_isolation"}:
                if category in {"answerable", "version_specific"}:
                    generations += 1
                try:
                    output = answer(db, owner_id, case["question"], mode="generate" if should_generate else "evidence",
                                    method="hybrid", top_k=6, **filters)
                    citations = output["citations"]
                    integrity = all(db.scalar(select(Chunk.id).where(Chunk.id == p["id"], Chunk.text == p["text"])) for p in citations)
                    forbidden = case.get("forbidden_outputs", []) + ([case["sentinel"]] if "sentinel" in case else [])
                    serialized = json.dumps(output)
                    generated_text = json.dumps({"answer": output["answer"], "claims": output["claims"]})
                    no_forbidden_generated = not any(value in generated_text for value in forbidden)
                    no_forbidden_anywhere = not any(value in serialized for value in forbidden)
                    # Injection instructions can appear in the explicitly displayed source text.
                    # Distinguish quoting a source from generated obedience. Privacy sentinels
                    # remain forbidden anywhere, including retrieved/source passages.
                    safe = no_forbidden_generated if category == "prompt_injection" else no_forbidden_anywhere
                    expectation = case["expected_status"]
                    status_match = output["status"] == expectation or (expectation == "answered_or_safe_abstention" and output["status"] in {"answered", "insufficient_evidence"})
                    behavior.append({"case_id": case["id"], "category": category, "status": output["status"],
                                     "expected_status": expectation, "status_match": status_match,
                                     "citation_count": len(citations), "citation_integrity": bool(integrity),
                                     "no_forbidden_output": safe, "latency_ms": output["timings"]["total_ms"],
                                     "no_forbidden_generated_output": no_forbidden_generated,
                                     "no_forbidden_anywhere": no_forbidden_anywhere,
                                     "generated_answer": output["answer"],
                                     "generated_claims": output["claims"],
                                     "evidence_for_review": [{"id": p["id"], "version_id": p["version_id"],
                                                               "version": p["version"], "text": p["text"]}
                                                              for p in citations],
                                     "usage": output["usage"], "human_correctness": None, "human_faithfulness": None})
                except ProviderError as exc:
                    behavior.append({"case_id": case["id"], "category": category, "error": str(exc), "status_match": False})
            if index % 10 == 0:
                print(f"Evaluation progress: {index}/{len(dataset['cases'])}", flush=True)
        aggregate = []
        for method in methods:
            valid = [r for r in rows if r["method"] == method and not r["error"]]
            aggregate.append({"method": method, "cases": len(valid),
                              **{name: float(np.mean([r[name] for r in valid])) if valid else None
                                 for name in ["recall_at_5", "mrr", "ndcg_at_5"]},
                              "p95_ms": float(np.percentile([r["latency_ms"] for r in valid], 95)) if valid else None,
                              "errors": sum(1 for r in rows if r["method"] == method and r["error"])})
        try:
            git_revision = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip() or "uncommitted"
        except FileNotFoundError:
            git_revision = "unavailable"
        source_hashes = list(db.execute(select(Version.checksum).join(Document).where(Document.collection_id.in_([corpus.id, originals.id]))).scalars())
        report = {"dataset": dataset["name"], "dataset_sha256": hashlib.sha256(raw).hexdigest(),
                  "annotation_status": dataset["annotation_status"], "run_at": datetime.now(UTC).isoformat(),
                  "results": aggregate, "behavior": behavior, "retrieval_cases": rows, "failures": failures,
                  "configuration": {"embedding_identity": embedding_identity(), "generation_model": settings().generation_model,
                                    "python": platform.python_version(), "platform": platform.platform(), "git_revision": git_revision,
                                    "rrf_constant": 60, "top_k": 5, "source_checksums": sorted(source_hashes)},
                  "release_gate": "OPEN: human review and semantic correctness/faithfulness assessment pending",
                  "limitations": dataset["limitations"] + [
                      "Passage recall uses strict exact-quote relevance; equivalent passages in another version may be counted as misses.",
                      "Latency includes model loads; this run is not the 30-repetition warmed performance benchmark.",
                      f"Generated answerable cases limited to {generation_limit}; every injection case also attempted.",
                      "Citation integrity is not semantic faithfulness. Correctness, unsupported-claim rate and abstention precision require human labels.",
                      "Permission sentinel cases check output; instrumented reranker/generator isolation is covered by integration tests."]}
        run = EvaluationRun(owner_id=owner_id, report=report)
        db.add(run)
        db.commit()
        report["id"] = run.id
    return report
