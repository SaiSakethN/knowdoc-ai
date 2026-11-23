import re
import time
from collections import defaultdict

from sqlalchemy import func, select

from knowdoc.facts import extract_profile_fact, profile_intent, profile_queries
from knowdoc.models import Chunk, Document, Version
from knowdoc.providers import embed, embedding_identity, rerank
from knowdoc.security import authorized


def base_query(user_id: str, collection_id=None, document_id=None, version_ids=None):
    query = select(Chunk, Version, Document).join(Version, Chunk.version_id == Version.id).join(
        Document, Version.document_id == Document.id).where(
            authorized(user_id), Chunk.generation == Version.active_generation)
    if collection_id:
        query = query.where(Document.collection_id == collection_id)
    if document_id:
        query = query.where(Document.id == document_id)
    if version_ids:
        query = query.where(Version.id.in_(version_ids))
    return query


def passage(row, score: float):
    chunk, version, document = row[:3]
    return {"id": chunk.id, "document_id": document.id, "title": document.title,
            "version_id": version.id, "version": version.label,
            "text": chunk.text, "quote_hash": chunk.quote_hash,
            "location": chunk.location, "score": float(score),
            "source_url": version.provenance.get("source_url"),
            "retrieved_at": version.provenance.get("retrieved_at"),
            "publication_date": version.provenance.get("publication_date"),
            "freshness": "version_declared; currentness_not_asserted"}


def search(db, user_id: str, question: str, *, method="hybrid", top_k=6,
           collection_id=None, document_id=None, version_ids=None):
    started = time.perf_counter()
    query = base_query(user_id, collection_id, document_id, version_ids)
    candidates: dict[str, dict] = {}
    lists = []
    intent = profile_intent(question)
    lexical_question, semantic_question = profile_queries(intent) if intent else (None, question)
    if method in {"keyword", "hybrid", "hybrid_rerank"}:
        terms = re.findall(r"[\w-]+", question.lower())[:80]
        terms = [t for t in terms if t not in {"what", "which", "how", "does", "the", "is", "are", "a", "an", "in", "of", "for", "to", "can", "and"}]
        tsquery = func.websearch_to_tsquery("english", lexical_question or " OR ".join(terms))
        rank = func.ts_rank_cd(Chunk.search_vector, tsquery)
        rows = db.execute(query.add_columns(rank).where(
            Chunk.search_vector.op("@@")(tsquery)).order_by(rank.desc()).limit(30)).all()
        lexical = [passage(r, r[3]) for r in rows]
        lists.append(lexical)
        candidates.update({p["id"]: p for p in lexical})
    if method in {"dense", "hybrid", "hybrid_rerank"}:
        vector = embed([semantic_question], purpose="query")[0]
        distance = Chunk.embedding.cosine_distance(vector)
        rows = db.execute(query.add_columns(distance).where(
            Chunk.embedding_model == embedding_identity(),
            func.vector_dims(Chunk.embedding) == len(vector)
        ).order_by(distance).limit(30)).all()
        dense = [passage(r, 1 - r[3]) for r in rows]
        lists.append(dense)
        candidates.update({p["id"]: p for p in dense})
    scores = defaultdict(float)
    if len(lists) > 1:
        for ranked in lists:
            for index, p in enumerate(ranked, 1):
                scores[p["id"]] += 1 / (60 + index)
        ranked = [{**p, "score": scores[p["id"]]} for p in candidates.values()]
        ranked.sort(key=lambda p: p["score"], reverse=True)
    else:
        ranked = lists[0] if lists else []
    if method == "hybrid_rerank" and ranked:
        ranked = rerank(question, ranked[:20])
    if intent:
        # Explicit, extractable profile statements outrank incidental uses of "role"
        # or "current". This applies only to already-authorized candidates.
        ranked.sort(key=lambda p: extract_profile_fact(question, [p]) is not None, reverse=True)
    # Exact duplicate passages from the same version do not consume evidence slots.
    result, seen = [], set()
    per_document = defaultdict(int)
    for p in ranked:
        key = (p["version_id"], p["quote_hash"])
        if key in seen or per_document[p["document_id"]] >= max(2, top_k // 2):
            continue
        seen.add(key)
        per_document[p["document_id"]] += 1
        result.append(p)
        if len(result) >= top_k:
            break
    return {"passages": result, "method": method,
            "retrieval_ms": round((time.perf_counter() - started) * 1000, 2)}
