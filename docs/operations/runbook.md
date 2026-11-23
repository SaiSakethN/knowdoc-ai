# Operations runbook

## Hosted service

Production is https://knowdoc-ai.vercel.app. Vercel is connected to GitHub and deploys the production branch. Check its build logs after a push. The readiness endpoint at /api/v1/health/ready checks the database and vector extension; /api/v1/capabilities reports the edition and limits. Neither is an answer-quality check.

The card-free release disables embeddings and general generation. Do not enable a paid fallback silently. Diagnose failed uploads from their job error, file size and chunk count before retrying. Cloud originals are database records, so back up PostgreSQL before schema changes. Monitor overall storage, including indexes and retained generations.

Apply migrations with an administrative connection before release, then grant only required table privileges to the runtime role. Production credentials belong in Vercel, not source. Test schema rollbacks and restores against a separate database. The synthetic live smoke check is scripts/verify_cloud.py.

## Local service

Start Docker Desktop/database, migrate, then API/worker. Liveness tests the process; readiness checks schema and vector extension, not model quality. Inspect owner-scoped job error classes before Retry. Fix invalid format, missing OCR, checksum mismatch or unavailable model before retrying. Expired ingestion leases can be reclaimed within bounded attempts; exhausted attempts fail visibly.

Reindex after parser/chunk/embedding changes. Failed replacements retain active search and historical chunks. There is no automated citation-aware old-generation garbage collector. Digest mismatch requires reviewing the model change and rebuilding indexes, not silently clearing the guard. Reranking needs the optional ML extra; no hosted fallback exists.

Back up PostgreSQL and raw objects as a matched snapshot while ingestion is quiescent. A database-only backup cannot restore original files. `scripts/check_consistency.py` reports source/index/hash/orphan discrepancies without deleting. Interrupted deletion can leave orphan bytes after access/index removal; review before cleanup. Test restores in distinct database/storage targets, never by overwriting active volumes.

Recovery tests exercise expired leases and failed reindexing; they are not a completed backup-restore drill. Before relying on backups, restore a distinct copy, migrate, run consistency checks and resolve a known citation.

For container inference, verify the host-gateway mapping and keep Ollama private. Logs omit raw document content by default. Stop only project-owned processes. `docker compose stop` preserves volumes. Local consistency checks inspect filesystem originals and are not intended for the cloud database-backed original store. A complete backup restoration drill remains outstanding.
