"""Read-only source/index reconciliation. Does not remove or modify any data."""
import hashlib
import json

from sqlalchemy import func, select

from knowdoc.config import settings
from knowdoc.db import session
from knowdoc.models import Chunk, Version


def main():
    findings = []
    with session() as db:
        versions = db.scalars(select(Version)).all()
        known = {v.id for v in versions}
        for version in versions:
            path = settings().storage_dir / version.id
            if not path.is_file():
                findings.append({"version_id": version.id, "issue": "missing_source"})
            elif hashlib.sha256(path.read_bytes()).hexdigest() != version.checksum:
                findings.append({"version_id": version.id, "issue": "source_checksum_mismatch"})
            if version.status == "ready" and not db.scalar(select(func.count()).select_from(Chunk).where(
                Chunk.version_id == version.id, Chunk.generation == version.active_generation)):
                findings.append({"version_id": version.id, "issue": "ready_without_active_chunks"})
        if settings().storage_dir.is_dir():
            for path in settings().storage_dir.iterdir():
                if path.is_file() and path.name not in known:
                    findings.append({"object": path.name, "issue": "orphan_source"})
    print(json.dumps({"versions_checked": len(versions), "findings": findings}, indent=2))


if __name__ == "__main__":
    main()
