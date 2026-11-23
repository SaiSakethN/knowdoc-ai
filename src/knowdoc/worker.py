import hashlib
import logging
import time
from datetime import timedelta

from sqlalchemy import and_, or_, select

from knowdoc.config import settings
from knowdoc.db import session
from knowdoc.models import Chunk, Job, SourceFile, Version, now, uid
from knowdoc.parsing import chunk_sections, parse
from knowdoc.providers import embed, embedding_identity

logger = logging.getLogger("knowdoc.worker")


def claim(job_id=None):
    cfg = settings()
    with session() as db, db.begin():
        exhausted = db.scalars(select(Job).where(Job.status == "running", Job.lease_until < now(),
                                                 Job.attempts >= cfg.max_attempts).with_for_update(skip_locked=True)).all()
        for dead in exhausted:
            dead.status, dead.error = "failed", "retry_limit_exhausted"
            version = db.get(Version, dead.version_id)
            if version and not version.active_generation:
                version.status = "failed"
        job = db.scalar(select(Job).where(
            Job.attempts < cfg.max_attempts,
            or_(Job.status == "queued", and_(Job.status == "running", Job.lease_until < now())),
            Job.id == job_id if job_id else True,
        ).order_by(Job.created_at).with_for_update(skip_locked=True).limit(1))
        if not job:
            return None
        job.status, job.attempts = "running", job.attempts + 1
        job.lease_token, job.lease_until = uid(), now() + timedelta(seconds=cfg.job_lease_seconds)
        version = db.get(Version, job.version_id)
        if not version.active_generation:
            version.status = "processing"
        return job.id, job.version_id, job.lease_token


def heartbeat(job_id: str, token: str):
    with session() as db, db.begin():
        job = db.get(Job, job_id, with_for_update=True)
        if not job or job.lease_token != token:
            raise RuntimeError("job_lease_lost")
        job.lease_until = now() + timedelta(seconds=settings().job_lease_seconds)


def process_one(job_id=None) -> bool:
    claimed = claim(job_id)
    if not claimed:
        return False
    job_id, version_id, lease_token = claimed
    started = time.perf_counter()
    try:
        with session() as db:
            version = db.get(Version, version_id)
            stored = db.get(SourceFile, version.id) if settings().source_storage == "database" else None
            content = stored.content if stored else (settings().storage_dir / version.id).read_bytes()
            if hashlib.sha256(content).hexdigest() != version.checksum:
                raise ValueError("source_checksum_mismatch")
            sections, warnings = parse(content, version.file_type, ocr=settings().ocr_enabled)
        pieces = list(chunk_sections(sections))
        if len(pieces) > settings().max_chunks:
            raise ValueError("chunk_limit_exceeded")
        parsed_at = time.perf_counter()
        generation = uid()
        chunks = []
        for offset in range(0, len(pieces), 8):
            heartbeat(job_id, lease_token)
            batch = pieces[offset:offset + 8]
            vectors = embed([text for text, _, _ in batch]) if settings().embedding_backend != "disabled" else [None] * len(batch)
            for i, ((text, location, tokens), vector) in enumerate(zip(batch, vectors, strict=True)):
                chunks.append(Chunk(version_id=version_id, generation=generation,
                                    ordinal=offset + i, text=text,
                                    quote_hash=hashlib.sha256(text.encode()).hexdigest(),
                                    location=location, token_count=tokens, embedding=vector,
                                    embedding_model=embedding_identity()))
        with session() as db, db.begin():
            job = db.get(Job, job_id, with_for_update=True)
            version = db.get(Version, version_id, with_for_update=True)
            if not job or not version or job.lease_token != lease_token:
                return True
            db.add_all(chunks)
            version.active_generation, version.status = generation, "ready"
            version.warnings = warnings
            version.provenance = {**version.provenance, "parser_revision": "knowdoc-1",
                                  "embedding_model": settings().embedding_model,
                                  "embedding_backend": settings().embedding_backend,
                                  "embedding_identity": embedding_identity(),
                                  "chunk_word_budget": 140, "overlap_words": 25}
            job.status, job.error, job.lease_until = "ready", None, None
            job.timings = {"parse_ms": round((parsed_at - started) * 1000, 2),
                           "total_ms": round((time.perf_counter() - started) * 1000, 2),
                           "chunks": len(chunks)}
        logger.info("ingestion_ready job_id=%s version_id=%s chunks=%s", job_id, version_id, len(chunks))
    except Exception as exc:
        # Classify failures; never log parser text, URLs, credentials or exception bodies.
        known_errors = {"source_checksum_mismatch", "chunk_limit_exceeded", "encrypted_pdf_unsupported",
                        "pdf_page_limit", "scanned_pdf_requires_ocr", "ocr_dependencies_unavailable",
                        "ocr_no_text", "no_extractable_text", "unsupported_parser"}
        safe_error = str(exc) if str(exc) in known_errors else type(exc).__name__
        with session() as db, db.begin():
            job = db.get(Job, job_id, with_for_update=True)
            version = db.get(Version, version_id)
            if job and job.lease_token == lease_token:
                job.status, job.error, job.lease_until = "failed", safe_error[:120], None
                if version and not version.active_generation:
                    version.status = "failed"
        logger.warning("ingestion_failed job_id=%s error=%s", job_id, safe_error)
    return True


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
    while True:
        try:
            if not process_one():
                if not process_evaluation():
                    time.sleep(1)
        except KeyboardInterrupt:
            break
        except Exception as exc:
            logger.error("worker_poll_failed error=%s", type(exc).__name__)
            time.sleep(3)


def process_evaluation():
    from knowdoc.evaluation import run_evaluation
    from knowdoc.models import EvaluationTask
    with session() as db, db.begin():
        task = db.scalar(select(EvaluationTask).where(or_(
            EvaluationTask.status == "queued",
            and_(EvaluationTask.status == "running", EvaluationTask.lease_until < now())
        )).order_by(EvaluationTask.created_at).with_for_update(skip_locked=True).limit(1))
        if not task:
            return False
        task.status, task.lease_token = "running", uid()
        task.lease_until = now() + timedelta(hours=1)
        task_id, token, owner_id = task.id, task.lease_token, task.owner_id
    try:
        report = run_evaluation(owner_id)
        with session() as db, db.begin():
            task = db.get(EvaluationTask, task_id, with_for_update=True)
            if task and task.lease_token == token:
                task.status, task.run_id, task.error = "ready", report["id"], None
    except Exception as exc:
        with session() as db, db.begin():
            task = db.get(EvaluationTask, task_id, with_for_update=True)
            if task and task.lease_token == token:
                task.status, task.error = "failed", type(exc).__name__
        logger.warning("evaluation_failed task_id=%s error=%s", task_id, type(exc).__name__)
    return True


if __name__ == "__main__":
    main()
