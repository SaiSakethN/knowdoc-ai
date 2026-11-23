# Developer setup

Follow [README commands](../README.md) from the repository root. Use Python 3.12; unqualified python was 3.14 on the audited host. uv.lock/package-lock.json lock dependencies. Bare uv run can resynchronize away optional extras: specify selected extras consistently or invoke the virtual environment directly.

Start Docker Desktop before the database. init_local.py creates ignored random credentials; after migrations, provision_local.py creates the restricted role and preserves the admin URL in ignored .env. It refuses to unexpectedly rotate an existing role. Never publish .env or data/demo-credentials.json. API and worker need matching database/storage settings.

Ollama must have the configured embedding/generation models. Set the exact embedding digest from local /api/tags. A mismatch fails until reviewed/reindexed. Cross-encoder weights download on first use and stay in the local Hugging Face cache; review/pin the revision for formal release. CPU model quality/latency are measured separately from runtime availability.

Run API and worker in separate terminals; Vite is optional if React was built. start-local.ps1 launches hidden host processes with ignored log files; avoid duplicate listeners. It does not kill unrelated processes. For containers, database and raw-upload volumes must match; use the documented storage override when migrating from host execution.

Corpus capture reads only approved archive members, verifies official source archive SHA-256, records docs archive/page hashes and retains notices. A publisher docs-archive checksum was not established. Capture timestamps do not imply page publication dates. Register your own account before import; demo data is not shared automatically.

Tests create/drop a unique PostgreSQL schema using migration privileges; client fixtures clean their own generated users. Model-free unit/integration fixtures are not semantic metrics. Playwright defaults to the built app on port 8000 and requires a running API, worker and isolated Chromium; credentials are synthetic. Set KNOWDOC_TEST_URL to test a different local endpoint. Each run writes to its own timestamped artifacts/browser directory. Avoid editing application source or overlapping model-heavy runs during verification. Real-corpus evaluation requires indexed approved sources and original fixtures.
