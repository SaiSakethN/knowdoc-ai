import hashlib
import secrets
from datetime import timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, HTTPException, Request
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from knowdoc.config import settings
from knowdoc.db import get_db
from knowdoc.models import Document, Grant, LoginSession, User, now

hasher = PasswordHasher(memory_cost=19456, time_cost=2, parallelism=1)


def digest(value: str):
    return hashlib.sha256(value.encode()).hexdigest()


def verify_password(encoded: str, password: str) -> bool:
    try:
        return hasher.verify(encoded, password)
    except (VerificationError, InvalidHashError):
        return False


def create_session(db: Session, user: User):
    token = secrets.token_urlsafe(32)
    login = LoginSession(token_hash=digest(token), user_id=user.id,
                         csrf=secrets.token_hex(32),
                         expires_at=now() + timedelta(hours=settings().session_hours))
    db.add(login)
    db.commit()
    return token, login


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("knowdoc_session")
    login = db.get(LoginSession, digest(token)) if token else None
    if not login or login.expires_at <= now():
        raise HTTPException(401, "authentication_required")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        if not secrets.compare_digest(request.headers.get("x-csrf-token", ""), login.csrf):
            raise HTTPException(403, "csrf_validation_failed")
    request.state.login = login
    return db.get(User, login.user_id)


def authorized(user_id: str):
    return or_(Document.owner_id == user_id, Document.id.in_(
        select(Grant.document_id).where(Grant.user_id == user_id)))


def require_document(db: Session, user_id: str, document_id: str, *, owner=False):
    query = select(Document).where(Document.id == document_id)
    query = query.where(Document.owner_id == user_id if owner else authorized(user_id))
    doc = db.scalar(query)
    if not doc:
        raise HTTPException(404, "document_not_found")
    return doc
