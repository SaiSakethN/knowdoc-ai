# Operations runbook

Start Docker Desktop/database, migrate, then API/worker. Liveness tests the process; readiness checks schema and vector extension, not model quality. Inspect owner-scoped job error classes before Retry. Fix invalid format, missing OCR, checksum mismatch or unavailable model before retrying. Expired ingestion leases can be reclaimed within bounded attempts; exhausted attempts fail visibly.

Reindex after parser/chunk/embedding changes. Failed replacements retain active search and historical chunks. There is no automated citation-aware old-generation garbage collector. Digest mismatch requires reviewing the model change and rebuilding indexes, not silently clearing the guard. Reranking needs the optional ML extra; no hosted fallback exists.

Back up PostgreSQL and raw objects as a matched snapshot while ingestion is quiescent. A database-only backup cannot restore original files. `scripts/check_consistency.py` reports source/index/hash/orphan discrepancies without deleting. Interrupted deletion can leave orphan bytes after access/index removal; review before cleanup. Test restores in distinct database/storage targets, never by overwriting active volumes.

Recovery tests exercise expired leases and failed reindexing; they are not a completed backup-restore drill. Before relying on backups, restore a distinct copy, migrate, run consistency checks and resolve a known citation.

For container host inference, verify host-gateway mapping; do not expose Ollama publicly or change machine firewall settings as a shortcut. Logs contain identifiers/timings/status/error classes, not raw content by default. Stop only owned project processes. `docker compose stop` preserves volumes; avoid `down -v` with valuable data. Public deployment, paid resources and hosted private-document inference remain separate approval checkpoints.
