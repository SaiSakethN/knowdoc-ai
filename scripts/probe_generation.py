"""Small real-provider diagnostics on public approved source passages only."""
import argparse
import json
from pathlib import Path

from sqlalchemy import select

from knowdoc.answers import answer
from knowdoc.db import session
from knowdoc.models import Collection, User


def main(email):
    with session() as db:
        user = db.scalar(select(User).where(User.email == email))
        collection = db.scalar(select(Collection).where(Collection.owner_id == user.id, Collection.name.like("PostgreSQL%")))
        results = []
        for question in ["Which index type does CREATE INDEX use by default?", "Which index type is preferred for text search?"]:
            output = answer(db, user.id, question, mode="generate", method="hybrid_rerank", top_k=4, collection_id=collection.id)
            results.append(output)
            print(question, output["status"], len(output["claims"]), output["timings"], flush=True)
        Path("artifacts/generation-probes-v2.json").write_text(json.dumps(results, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("email")
    main(parser.parse_args().email)
