"""Capture only approved PostgreSQL pages from official release documentation archives.

Run with `uv run python scripts/fetch_corpus.py`. No recursive crawler or tar extraction.
"""
import hashlib
import io
import json
import tarfile
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

PAGES = ["indexes", "indexes-types", "indexes-multicolumn", "indexes-expressional",
         "indexes-partial", "textsearch", "textsearch-intro", "textsearch-tables",
         "textsearch-indexes", "mvcc", "transaction-iso", "explicit-locking"]
RELEASES = ["18.7", "19.0"]
ROOT = Path("data/corpus")


def fetch(client, url, destination):
    if destination.exists():
        return destination.read_bytes()
    time.sleep(1)
    r = client.get(url)
    r.raise_for_status()
    if len(r.content) > 45_000_000:
        raise RuntimeError("archive_size_limit")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(r.content)
    return r.content


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=90, follow_redirects=False,
                      headers={"User-Agent": "KnowDocAI/0.1 bounded educational corpus capture"}) as client:
        policy = client.get("https://www.postgresql.org/robots.txt")
        policy.raise_for_status()
        (ROOT / "robots.txt").write_bytes(policy.content)
        robots = policy.text
        policy_checked_at = datetime.now(UTC).isoformat()
        if any(f"Disallow: /docs/{major}/" in robots for major in ("18", "19")):
            raise RuntimeError("robots_policy_changed")
        records = []
        for release in RELEASES:
            major = release.split(".")[0]
            base = f"https://ftp.postgresql.org/pub/source/v{release}"
            source_name = f"postgresql-{release}.tar.gz"
            source_url = f"{base}/{source_name}"
            source = fetch(client, source_url, ROOT / source_name)
            expected = fetch(client, source_url + ".sha256", ROOT / (source_name + ".sha256")).decode().split()[0]
            if hashlib.sha256(source).hexdigest() != expected:
                raise RuntimeError("publisher_source_checksum_mismatch")
            with tarfile.open(fileobj=io.BytesIO(source), mode="r:gz") as archive:
                member = archive.getmember(f"postgresql-{release}/COPYRIGHT")
                notice = archive.extractfile(member).read()
                (ROOT / f"NOTICE-{release}.txt").write_bytes(notice)
            archive_url = f"{base}/postgresql-{release}-docs.tar.gz"
            data = fetch(client, archive_url, ROOT / f"postgresql-{release}-docs.tar.gz")
            archive_hash = hashlib.sha256(data).hexdigest()
            with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
                members = {Path(m.name).name: m for m in archive.getmembers() if m.isfile()}
                for page in PAGES:
                    name = page + ".html"
                    member = members.get(name)
                    if not member or member.size > 2_000_000:
                        raise RuntimeError(f"missing_or_oversized_approved_page:{release}/{name}")
                    raw = archive.extractfile(member).read()
                    soup = BeautifulSoup(raw, "html.parser")
                    title = soup.title.get_text() if soup.title else name
                    # Release identity comes from archive name + verified source release, not mutable /current.
                    destination = ROOT / release / name
                    destination.parent.mkdir(exist_ok=True)
                    destination.write_bytes(raw)
                    records.append({"publisher": "PostgreSQL Global Development Group",
                                    "source_url": f"https://www.postgresql.org/docs/{major}/{name}",
                                    "archive_url": archive_url, "archive_sha256": archive_hash,
                                    "publisher_docs_checksum_available": False,
                                    "verified_source_archive_sha256": expected,
                                    "version": release, "title": title, "file": str(destination.as_posix()),
                                    "retrieved_at": datetime.now(UTC).isoformat(),
                                    "publication_date": None, "publication_date_basis": "not established per page",
                                    "format": "html", "sha256": hashlib.sha256(raw).hexdigest(),
                                    "size": len(raw), "license_url": "https://www.postgresql.org/about/licence/",
                                    "notice": f"data/corpus/NOTICE-{release}.txt",
                                    "access_policy": "data/corpus/robots.txt",
                                    "access_policy_checked_at": policy_checked_at,
                                    "redistribution": "retain applicable PostgreSQL notices; exclude unrelated assets"})
            print(f"Captured {release}: {len(PAGES)} approved HTML pages")
        (ROOT / "manifest.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
        public = Path("configs")
        public.mkdir(exist_ok=True)
        (public / "source-manifest.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
        print(f"Manifest: {len(records)} records. Raw content excluded from Git.")


if __name__ == "__main__":
    main()
