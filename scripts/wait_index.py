"""Wait for pending document jobs, failing visibly rather than running partial benchmarks."""
import time

from sqlalchemy import func, select

from knowdoc.db import session
from knowdoc.models import Job

for attempt in range(120):
    with session() as db:
        pending = db.scalar(select(func.count()).select_from(Job).where(Job.status.in_(["queued", "running"])))
        failed = db.scalar(select(func.count()).select_from(Job).where(Job.status == "failed"))
    if not pending:
        if failed:
            raise SystemExit(f"Indexing stopped with {failed} failed jobs")
        print("All document jobs ready.", flush=True)
        break
    if attempt % 6 == 0:
        print(f"Waiting for {pending} document jobs", flush=True)
    time.sleep(5)
else:
    raise SystemExit("Timed out waiting for index")
