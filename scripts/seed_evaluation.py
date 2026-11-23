"""Seed original evaluation fixtures; private cases belong to a separate generated account."""
import hashlib
import secrets
import sys
from pathlib import Path

from sqlalchemy import select

from knowdoc.config import settings
from knowdoc.db import session
from knowdoc.models import Collection, Document, Job, User, Version
from knowdoc.security import hasher


def main(email):
    with session() as db:
        owner = db.scalar(select(User).where(User.email == email))
        if not owner:
            raise SystemExit("Register benchmark owner first")
        hidden = db.scalar(select(User).where(User.email == "evaluation-hidden@knowdoc.local"))
        if not hidden:
            hidden = User(email="evaluation-hidden@knowdoc.local", password_hash=hasher.hash(secrets.token_urlsafe(32)))
            db.add(hidden)
            db.flush()
        settings().storage_dir.mkdir(parents=True, exist_ok=True)
        for file in sorted(Path("evals/fixtures").glob("*.md")):
            principal = hidden if file.stem.startswith("private-") else owner
            name = "Original evaluation fixtures" if principal.id == owner.id else "Restricted evaluation fixtures"
            collection = db.scalar(select(Collection).where(Collection.owner_id == principal.id, Collection.name == name))
            if not collection:
                collection = Collection(owner_id=principal.id, name=name)
                db.add(collection)
                db.flush()
            if file.stem.endswith(("-v1", "-v2")):
                slug, label = "original-" + file.stem[:-3], file.stem[-2:]
            else:
                slug, label = file.stem, "fixture-v1"
            document = db.scalar(select(Document).where(Document.collection_id == collection.id, Document.title == slug))
            if not document:
                document = Document(collection_id=collection.id, owner_id=principal.id, title=slug)
                db.add(document)
                db.flush()
            if db.scalar(select(Version).where(Version.document_id == document.id, Version.label == label)):
                continue
            raw = file.read_bytes()
            version = Version(document_id=document.id, label=label, checksum=hashlib.sha256(raw).hexdigest(),
                              filename=file.name, file_type="markdown", size=len(raw), provenance={
                                  "fixture": True, "license": "CC0-1.0", "publication_date": None,
                                  "private": principal.id != owner.id})
            db.add(version)
            db.flush()
            (settings().storage_dir / version.id).write_bytes(raw)
            db.add(Job(version_id=version.id))
        db.commit()
        print("Original fixtures queued. Hidden documents are owned by a separate test principal.")


if __name__ == "__main__":
    main(sys.argv[1])
