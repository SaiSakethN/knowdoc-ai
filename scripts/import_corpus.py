"""Import captured corpus into a specified existing user's private collection.

uv run python scripts/import_corpus.py user@example.com
"""
import json
import sys
from pathlib import Path

from sqlalchemy import select

from knowdoc.config import settings
from knowdoc.db import session
from knowdoc.models import Collection, Document, Job, User, Version


def main(email):
    records = json.loads(Path("data/corpus/manifest.json").read_text())
    with session() as db:
        user = db.scalar(select(User).where(User.email == email))
        if not user:
            raise SystemExit("Register the target user first")
        collection = db.scalar(select(Collection).where(Collection.owner_id == user.id,
                                                        Collection.name == "PostgreSQL · versioned reference"))
        if not collection:
            collection = Collection(owner_id=user.id, name="PostgreSQL · versioned reference")
            db.add(collection)
            db.flush()
        settings().storage_dir.mkdir(parents=True, exist_ok=True)
        for record in records:
            title = Path(record["file"]).stem
            doc = db.scalar(select(Document).where(Document.collection_id == collection.id, Document.title == title))
            if not doc:
                doc = Document(collection_id=collection.id, owner_id=user.id, title=title)
                db.add(doc)
                db.flush()
            if db.scalar(select(Version).where(Version.document_id == doc.id, Version.label == record["version"])):
                continue
            raw = Path(record["file"]).read_bytes()
            v = Version(document_id=doc.id, label=record["version"], checksum=record["sha256"],
                        filename=Path(record["file"]).name, file_type="html", size=len(raw), provenance=record)
            db.add(v)
            db.flush()
            (settings().storage_dir / v.id).write_bytes(raw)
            db.add(Job(version_id=v.id))
        db.commit()
        print(f"Corpus jobs queued for {email}; collection {collection.id}")


if __name__ == "__main__":
    main(sys.argv[1])
