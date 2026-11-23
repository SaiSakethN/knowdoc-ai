"""30 warmed retrieval repetitions on one fixed query, separately from corpus quality."""
import argparse
import json
from pathlib import Path

import numpy as np
from sqlalchemy import select

from knowdoc.db import session
from knowdoc.models import Collection, User
from knowdoc.retrieval import search


def main(email):
    rows = []
    with session() as db:
        user = db.scalar(select(User).where(User.email == email))
        if not user:
            raise SystemExit("Unknown account")
        corpus = db.scalar(select(Collection).where(Collection.owner_id == user.id, Collection.name == "PostgreSQL · versioned reference"))
        if not corpus:
            raise SystemExit("Import approved corpus first")
        question = "Which index type is preferred for full text search?"
        for method in ["keyword", "dense", "hybrid", "hybrid_rerank"]:
            search(db, user.id, question, collection_id=corpus.id, method=method)
            timings = [search(db, user.id, question, collection_id=corpus.id, method=method)["retrieval_ms"] for _ in range(30)]
            rows.append({"method": method, "repetitions": 30, "p50_ms": float(np.percentile(timings, 50)),
                         "p95_ms": float(np.percentile(timings, 95)), "samples_ms": timings})
            print(method, rows[-1]["p95_ms"], flush=True)
    output = Path("artifacts/evaluations")
    output.mkdir(parents=True, exist_ok=True)
    (output / "performance.json").write_text(json.dumps({"query": question, "results": rows,
        "limitations": "One fixed query, one user, configured model unload policy. Not a throughput or production SLA test."}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("email")
    main(parser.parse_args().email)
