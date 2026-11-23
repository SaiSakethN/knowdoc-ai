import hashlib
import json
import logging
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException as StarletteHTTPException

from knowdoc.answers import answer
from knowdoc.config import settings
from knowdoc.db import get_db
from knowdoc.limits import UploadBodyLimit
from knowdoc.models import (
    Chunk,
    Collection,
    Document,
    EvaluationRun,
    EvaluationTask,
    Grant,
    Job,
    SourceFile,
    User,
    Version,
    uid,
)
from knowdoc.parsing import ParseError, validate_file
from knowdoc.providers import ProviderError
from knowdoc.retrieval import base_query, passage, search
from knowdoc.schemas import (
    AnswerInput,
    AnswerOutput,
    CollectionInput,
    Credentials,
    GrantInput,
    PassageOutput,
    SearchInput,
    SearchOutput,
)
from knowdoc.security import (
    authorized,
    create_session,
    current_user,
    hasher,
    require_document,
    verify_password,
)

logger = logging.getLogger("knowdoc.api")
logging.basicConfig(level=logging.INFO, format="%(message)s")
rate_windows = defaultdict(deque)


@asynccontextmanager
async def lifespan(app):
    if settings().source_storage == "local":
        settings().storage_dir.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="KnowDoc AI", version="0.1.0", lifespan=lifespan)
app.add_middleware(UploadBodyLimit)
app.add_middleware(CORSMiddleware, allow_origins=[settings().web_origin],
                   allow_credentials=True, allow_methods=["GET", "POST", "DELETE"],
                   allow_headers=["Content-Type", "X-CSRF-Token"])


@app.get("/api/v1/capabilities")
def capabilities():
    cfg = settings()
    return {"cloud": cfg.cloud_mode, "generation": cfg.generation_backend,
            "semantic_search": cfg.embedding_backend != "disabled",
            "max_upload_bytes": cfg.max_upload_bytes}


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = uid()
    request.state.request_id = request_id
    started = time.perf_counter()
    # Per-process limiter is intentionally local-demo scope; not a distributed guarantee.
    key = (request.client.host if request.client else "unknown",
           "auth" if "/sessions" in request.url.path else "api")
    window = rate_windows[key]
    cutoff = time.monotonic() - 60
    while window and window[0] < cutoff:
        window.popleft()
    limit = 20 if key[1] == "auth" else 180
    if request.method not in {"GET", "HEAD"} and len(window) >= limit:
        return JSONResponse({"error": "rate_limit_exceeded", "request_id": request_id}, 429,
                            headers={"Retry-After": "60"})
    if request.method not in {"GET", "HEAD"}:
        window.append(time.monotonic())
    origin = request.headers.get("origin")
    allowed_origins = {settings().web_origin, str(request.base_url).rstrip("/")}
    if request.method not in {"GET", "HEAD", "OPTIONS"} and origin and origin not in allowed_origins:
        return JSONResponse({"error": "origin_not_allowed", "request_id": request_id}, 403)
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.error(json.dumps({"request_id": request_id, "error_class": type(exc).__name__}))
        response = JSONResponse({"error": "internal_error", "request_id": request_id}, 500)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    logger.info(json.dumps({"request_id": request_id, "method": request.method,
                            "path": request.url.path, "status": response.status_code,
                            "duration_ms": round((time.perf_counter() - started) * 1000, 2)}))
    return response


@app.exception_handler(StarletteHTTPException)
async def http_error(request, exc):
    return JSONResponse({"error": exc.detail, "request_id": getattr(request.state, "request_id", None)},
                        exc.status_code, headers=exc.headers)


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    return JSONResponse({"error": "validation_error", "fields": [".".join(map(str, e["loc"])) for e in exc.errors()],
                         "request_id": request.state.request_id}, 422)


@app.exception_handler(ProviderError)
async def provider_error(request, exc):
    return JSONResponse({"error": str(exc), "request_id": request.state.request_id}, 503)


@app.get("/api/v1/health/live")
def live():
    return {"status": "ok", "service": "KnowDoc AI"}


@app.get("/api/v1/health/ready")
def ready(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1 FROM versions LIMIT 1"))
        vector_version = db.scalar(text("SELECT extversion FROM pg_extension WHERE extname='vector'"))
        if not vector_version:
            raise RuntimeError("vector_missing")
        return {"status": "ready", "database": "connected", "vector_extension": vector_version}
    except Exception:
        raise HTTPException(503, "database_not_ready") from None


@app.post("/api/v1/sessions/register", status_code=201)
def register(payload: Credentials, response: Response, db: Session = Depends(get_db)):
    user = User(email=payload.email, password_hash=hasher.hash(payload.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "account_unavailable") from None
    return login_response(db, user, response)


def login_response(db, user, response):
    token, login = create_session(db, user)
    response.set_cookie("knowdoc_session", token, httponly=True, secure=settings().cookie_secure,
                        samesite="lax", max_age=settings().session_hours * 3600, path="/")
    return {"user": {"id": user.id, "email": user.email}, "csrf_token": login.csrf}


@app.post("/api/v1/sessions/login")
def login(payload: Credentials, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(user.password_hash, payload.password):
        raise HTTPException(401, "invalid_credentials")
    return login_response(db, user, response)


@app.get("/api/v1/sessions/me")
def me(request: Request, user: User = Depends(current_user)):
    return {"user": {"id": user.id, "email": user.email}, "csrf_token": request.state.login.csrf}


@app.delete("/api/v1/sessions/current", status_code=204)
def logout(request: Request, response: Response, user=Depends(current_user), db=Depends(get_db)):
    db.delete(request.state.login)
    db.commit()
    response.delete_cookie("knowdoc_session")


@app.get("/api/v1/collections")
def collections(user=Depends(current_user), db=Depends(get_db), limit: int = 50, offset: int = 0):
    rows = db.scalars(select(Collection).where(Collection.owner_id == user.id).order_by(
        Collection.created_at).offset(max(0, offset)).limit(min(100, max(1, limit)))).all()
    return {"items": [{"id": c.id, "name": c.name} for c in rows]}


@app.post("/api/v1/collections", status_code=201)
def create_collection(payload: CollectionInput, user=Depends(current_user), db=Depends(get_db)):
    row = Collection(owner_id=user.id, name=payload.name.strip())
    if not row.name:
        raise HTTPException(422, "name_required")
    db.add(row)
    db.commit()
    return {"id": row.id, "name": row.name}


@app.post("/api/v1/documents", status_code=202)
async def upload(collection_id: str = Form(...), label: str = Form("unversioned"),
                 document_id: str | None = Form(None), source_url: str = Form(""),
                 file: UploadFile = File(...), user=Depends(current_user), db=Depends(get_db)):
    collection = db.scalar(select(Collection).where(Collection.id == collection_id, Collection.owner_id == user.id))
    if not collection:
        raise HTTPException(404, "collection_not_found")
    if not label.strip() or len(label) > 100 or len(source_url) > 2000:
        raise HTTPException(422, "invalid_version_metadata")
    # Read a bounded stream. Reverse proxy/body limits are additionally required for public serving.
    content = await file.read(settings().max_upload_bytes + 1)
    if len(content) > settings().max_upload_bytes:
        raise HTTPException(413, "file_too_large")
    filename = Path((file.filename or "document").replace("\\", "/")).name[:240]
    try:
        kind = validate_file(filename, content)
    except ParseError as exc:
        raise HTTPException(415, str(exc)) from exc
    checksum = hashlib.sha256(content).hexdigest()
    if settings().cloud_mode:
        # Serialize quota checks across function instances. Keep the free database
        # bounded without relying on a per-process counter or fake vectors.
        db.execute(text("SELECT pg_advisory_xact_lock(73658120)"))
        total = db.scalar(select(func.coalesce(func.sum(Version.size), 0)))
        owned = db.scalar(select(func.coalesce(func.sum(Version.size), 0)).join(Document).where(Document.owner_id == user.id))
        if total + len(content) > 150 * 1024 * 1024 or owned + len(content) > 20 * 1024 * 1024:
            raise HTTPException(413, "free_storage_limit_reached")
    if document_id:
        doc = require_document(db, user.id, document_id, owner=True)
        if doc.collection_id != collection.id:
            raise HTTPException(422, "document_collection_mismatch")
    else:
        # Duplicate detection is scoped to owned collection; it reveals no cross-user hashes.
        duplicate = db.scalar(select(Version).join(Document).where(
            Document.owner_id == user.id, Document.collection_id == collection_id,
            Version.checksum == checksum))
        if duplicate:
            return {"version_id": duplicate.id, "document_id": duplicate.document_id,
                    "duplicate": True, "status": duplicate.status}
        doc = Document(collection_id=collection_id, owner_id=user.id, title=filename)
        db.add(doc)
        db.flush()
    duplicate = db.scalar(select(Version).where(Version.document_id == doc.id, Version.checksum == checksum))
    if duplicate:
        return {"version_id": duplicate.id, "document_id": doc.id, "duplicate": True, "status": duplicate.status}
    version = Version(document_id=doc.id, label=label.strip(), checksum=checksum,
                      filename=filename, file_type=kind, size=len(content), provenance={
                          "source_url": source_url or None, "publication_date": None,
                          "version_basis": "uploader_declared", "private": True})
    db.add(version)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "version_label_already_exists") from None
    path = settings().storage_dir / version.id
    if settings().source_storage == "database":
        db.add(SourceFile(version_id=version.id, content=content))
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    job = Job(version_id=version.id)
    db.add(job)
    try:
        db.commit()
    except Exception:
        if settings().source_storage == "local":
            path.unlink(missing_ok=True)
        raise
    if settings().cloud_mode:
        from knowdoc.worker import process_one
        await run_in_threadpool(process_one, job.id)
    return {"document_id": doc.id, "version_id": version.id, "job_id": job.id, "status": "queued", "duplicate": False}


def version_json(v):
    return {"id": v.id, "document_id": v.document_id, "label": v.label,
            "checksum": v.checksum, "filename": v.filename, "file_type": v.file_type,
            "size": v.size, "status": v.status, "provenance": v.provenance,
            "warnings": v.warnings, "created_at": v.created_at.isoformat()}


@app.get("/api/v1/documents")
def documents(collection_id: str | None = None, limit: int = 50, offset: int = 0,
              user=Depends(current_user), db=Depends(get_db)):
    query = select(Document).where(authorized(user.id))
    if collection_id:
        query = query.where(Document.collection_id == collection_id)
    docs = db.scalars(query.order_by(Document.created_at.desc()).offset(max(0, offset)).limit(min(100, max(1, limit)))).all()
    versions = db.scalars(select(Version).where(Version.document_id.in_([d.id for d in docs])).order_by(Version.created_at)).all() if docs else []
    return {"items": [{"id": d.id, "title": d.title, "collection_id": d.collection_id,
                       "owned": d.owner_id == user.id,
                       "versions": [version_json(v) for v in versions if v.document_id == d.id]} for d in docs]}


@app.get("/api/v1/documents/{document_id}/versions")
def versions(document_id: str, user=Depends(current_user), db=Depends(get_db)):
    require_document(db, user.id, document_id)
    return {"items": [version_json(v) for v in db.scalars(select(Version).where(Version.document_id == document_id))]}


@app.get("/api/v1/versions/{version_id}/original")
def original(version_id: str, user=Depends(current_user), db=Depends(get_db)):
    version = db.get(Version, version_id)
    if not version:
        raise HTTPException(404, "version_not_found")
    require_document(db, user.id, version.document_id)
    if settings().source_storage == "database":
        stored = db.get(SourceFile, version.id)
        if not stored:
            raise HTTPException(404, "source_file_unavailable")
        return Response(stored.content, media_type="application/octet-stream", headers={
            "Content-Disposition": "attachment; filename*=UTF-8''" + quote(version.filename, safe="")})
    path = settings().storage_dir / version.id
    if not path.is_file():
        raise HTTPException(404, "source_file_unavailable")
    return FileResponse(path, media_type="application/octet-stream", filename=version.filename,
                        content_disposition_type="attachment")


@app.get("/api/v1/versions/{version_id}/passages")
def version_passages(version_id: str, limit: int = 100, offset: int = 0,
                     user=Depends(current_user), db=Depends(get_db)):
    rows = db.execute(base_query(user.id, version_ids=[version_id]).order_by(Chunk.ordinal).offset(
        max(0, offset)).limit(min(200, max(1, limit)))).all()
    if not rows:
        version = db.get(Version, version_id)
        if not version:
            raise HTTPException(404, "version_not_found")
        require_document(db, user.id, version.document_id)
    return {"items": [passage(r, 0) for r in rows]}


@app.delete("/api/v1/documents/{document_id}", status_code=204)
def delete_document(document_id: str, user=Depends(current_user), db=Depends(get_db)):
    doc = require_document(db, user.id, document_id, owner=True)
    ids = list(db.scalars(select(Version.id).where(Version.document_id == doc.id)))
    db.delete(doc)
    db.commit()  # Revoke and remove indexed text before raw storage cleanup.
    for version_id in ids:
        if settings().source_storage == "local":
            (settings().storage_dir / version_id).unlink(missing_ok=True)


@app.post("/api/v1/documents/{document_id}/grants", status_code=201)
def grant(document_id: str, payload: GrantInput, user=Depends(current_user), db=Depends(get_db)):
    require_document(db, user.id, document_id, owner=True)
    target = db.scalar(select(User).where(User.email == payload.email.strip().lower()))
    if not target:
        raise HTTPException(404, "user_not_found")
    if not db.get(Grant, (document_id, target.id)):
        db.add(Grant(document_id=document_id, user_id=target.id))
        db.commit()
    return {"user_id": target.id, "document_id": document_id}


@app.get("/api/v1/documents/{document_id}/grants")
def list_grants(document_id: str, user=Depends(current_user), db=Depends(get_db)):
    require_document(db, user.id, document_id, owner=True)
    rows = db.execute(select(User.id, User.email).join(Grant, Grant.user_id == User.id).where(Grant.document_id == document_id)).all()
    return {"items": [{"user_id": uid, "email": email} for uid, email in rows]}


@app.delete("/api/v1/documents/{document_id}/grants/{user_id}", status_code=204)
def revoke(document_id: str, user_id: str, user=Depends(current_user), db=Depends(get_db)):
    require_document(db, user.id, document_id, owner=True)
    db.execute(delete(Grant).where(Grant.document_id == document_id, Grant.user_id == user_id))
    db.commit()


@app.get("/api/v1/jobs")
def jobs(user=Depends(current_user), db=Depends(get_db), limit: int = 50, offset: int = 0):
    rows = db.execute(select(Job, Version, Document).join(Version, Job.version_id == Version.id).join(
        Document, Version.document_id == Document.id).where(Document.owner_id == user.id).order_by(
        Job.created_at.desc()).offset(max(0, offset)).limit(min(100, max(1, limit)))).all()
    return {"items": [{"id": j.id, "version_id": v.id, "title": d.title, "version": v.label,
                       "status": j.status, "attempts": j.attempts, "error": j.error,
                       "timings": j.timings} for j, v, d in rows]}


@app.post("/api/v1/jobs/{job_id}/retry")
def retry(job_id: str, user=Depends(current_user), db=Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "job_not_found")
    version = db.get(Version, job.version_id)
    require_document(db, user.id, version.document_id, owner=True)
    if job.status != "failed":
        raise HTTPException(409, "job_not_failed")
    job.status, job.attempts, job.error = "queued", 0, None
    db.commit()
    if settings().cloud_mode:
        from knowdoc.worker import process_one
        process_one(job.id)
    return {"id": job.id, "status": job.status}


@app.post("/api/v1/versions/{version_id}/reindex", status_code=202)
def reindex(version_id: str, user=Depends(current_user), db=Depends(get_db)):
    version = db.get(Version, version_id, with_for_update=True)
    if not version:
        raise HTTPException(404, "version_not_found")
    require_document(db, user.id, version.document_id, owner=True)
    existing = db.scalar(select(Job).where(Job.version_id == version_id, Job.status.in_(["queued", "running"])))
    if existing:
        return {"job_id": existing.id, "status": existing.status}
    job = Job(version_id=version_id)
    db.add(job)
    db.commit()
    if settings().cloud_mode:
        from knowdoc.worker import process_one
        process_one(job.id)
    return {"job_id": job.id, "status": job.status}


@app.post("/api/v1/search", response_model=SearchOutput)
def search_endpoint(payload: SearchInput, user=Depends(current_user), db=Depends(get_db)):
    return search(db, user.id, **payload.model_dump())


@app.post("/api/v1/answers", response_model=AnswerOutput)
def answer_endpoint(payload: AnswerInput, user=Depends(current_user), db=Depends(get_db)):
    result = answer(db, user.id, **payload.model_dump())
    # Recheck grants after external/local model processing, before constructing response.
    db.expire_all()
    allowed = {r[0].id for r in db.execute(base_query(user.id).where(
        Chunk.id.in_([p["id"] for p in result["citations"]]))).all()}
    if any(p["id"] not in allowed for p in result["citations"]):
        raise HTTPException(409, "permissions_changed_retry_question")
    return result


@app.get("/api/v1/citations/{chunk_id}", response_model=PassageOutput)
def citation(chunk_id: str, user=Depends(current_user), db=Depends(get_db)):
    row = db.execute(base_query(user.id).where(Chunk.id == chunk_id)).first()
    if not row:
        # Historical index chunks remain resolvable while their source version exists.
        row = db.execute(select(Chunk, Version, Document).join(Version, Chunk.version_id == Version.id).join(Document, Version.document_id == Document.id).where(
            Chunk.id == chunk_id, authorized(user.id))).first()
    if not row:
        raise HTTPException(404, "citation_not_found")
    p = passage(row, 0)
    if hashlib.sha256(p["text"].encode()).hexdigest() != p["quote_hash"]:
        raise HTTPException(409, "citation_integrity_error")
    return p


@app.get("/api/v1/system")
def system(user=Depends(current_user), db=Depends(get_db)):
    count = db.scalar(select(func.count()).select_from(Document).where(authorized(user.id)))
    chunks = db.scalar(select(func.count()).select_from(base_query(user.id).subquery()))
    return {"documents": count, "active_chunks": chunks, "embedding_model": settings().embedding_model,
            "generation_model": settings().generation_model, "hosted_provider_enabled": settings().allow_remote_provider,
            "ocr_enabled": settings().ocr_enabled, "permission_strategy": "SQL prefilter and response recheck"}


@app.get("/api/v1/evaluations")
def evaluation_runs(user=Depends(current_user), db=Depends(get_db)):
    rows = db.scalars(select(EvaluationRun).where(EvaluationRun.owner_id == user.id).order_by(EvaluationRun.created_at.desc()).limit(20))
    tasks = db.scalars(select(EvaluationTask).where(EvaluationTask.owner_id == user.id).order_by(EvaluationTask.created_at.desc()).limit(10)).all()
    return {"items": [{"id": r.id, "created_at": r.created_at.isoformat(), "report": r.report} for r in rows],
            "tasks": [{"id": t.id, "status": t.status, "run_id": t.run_id, "error": t.error} for t in tasks]}


@app.post("/api/v1/evaluations", status_code=202)
def create_evaluation(user=Depends(current_user), db=Depends(get_db)):
    if settings().cloud_mode:
        raise HTTPException(403, "benchmarks_run_locally_to_preserve_free_quota")
    existing = db.scalar(select(EvaluationTask).where(EvaluationTask.owner_id == user.id, EvaluationTask.status.in_(["queued", "running"])))
    if existing:
        return {"task_id": existing.id, "status": existing.status}
    names = set(db.scalars(select(Collection.name).where(Collection.owner_id == user.id)))
    if not {"PostgreSQL · versioned reference", "Original evaluation fixtures"}.issubset(names):
        raise HTTPException(409, "import_benchmark_corpus_and_fixtures_first")
    task = EvaluationTask(owner_id=user.id)
    db.add(task)
    db.commit()
    return {"task_id": task.id, "status": task.status}


@app.get("/api/v1/evaluations/{run_id}")
def evaluation_result(run_id: str, user=Depends(current_user), db=Depends(get_db)):
    run = db.scalar(select(EvaluationRun).where(EvaluationRun.id == run_id, EvaluationRun.owner_id == user.id))
    if not run:
        raise HTTPException(404, "evaluation_not_found")
    return {"id": run.id, "report": run.report}


web_directory = Path("apps/web/dist")
if web_directory.is_dir():
    app.mount("/", StaticFiles(directory=web_directory, html=True), name="web")
