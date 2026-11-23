"""Repeat generation after a grounding change without rerunning unchanged retrieval baselines."""
import argparse
import json
from pathlib import Path

from sqlalchemy import select

from knowdoc.db import session
from knowdoc.evaluation import run_evaluation
from knowdoc.models import User

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("email")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    with session() as db:
        user = db.scalar(select(User).where(User.email == args.email))
        owner_id = user.id
    report = run_evaluation(owner_id, generation_limit=args.limit, methods=[])
    Path("artifacts/evaluations/answers-v2.json").write_text(json.dumps(report, indent=2))
    print("Accepted answerable outputs:", sum(r.get("status") == "answered" for r in report["behavior"] if r["category"] in {"answerable", "version_specific"}), flush=True)
