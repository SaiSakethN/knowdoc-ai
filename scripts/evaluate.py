import argparse
import csv
import json
from pathlib import Path

from sqlalchemy import select

from knowdoc.db import session
from knowdoc.evaluation import run_evaluation
from knowdoc.models import User


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("email")
    parser.add_argument("--generation-limit", type=int, default=5)
    args = parser.parse_args()
    with session() as db:
        owner = db.scalar(select(User).where(User.email == args.email))
        if not owner:
            raise SystemExit("Unknown local account")
        owner_id = owner.id
    report = run_evaluation(owner_id, generation_limit=args.generation_limit)
    out = Path("artifacts/evaluations")
    out.mkdir(parents=True, exist_ok=True)
    (out / "latest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    with (out / "comparison.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=report["results"][0].keys())
        writer.writeheader()
        writer.writerows(report["results"])
    print(json.dumps(report["results"], indent=2))
    print(report["release_gate"])


if __name__ == "__main__":
    main()
