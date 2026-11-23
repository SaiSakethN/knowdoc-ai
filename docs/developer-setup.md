# Developer setup

The project has two editions. The hosted app runs at https://knowdoc-ai.vercel.app with keyword search and exact profile extraction. The local edition below adds Ollama generation, semantic retrieval, optional reranking and OCR. See [cloud configuration](cloud-deployment.md) for the hosted setup. Keep local and production credentials separate.

Follow [README commands](../README.md) from the repository root. Use Python 3.12 and Node.js 24. uv.lock/package-lock.json lock dependencies. Bare uv run can resynchronize away optional extras: specify selected extras consistently or invoke the virtual environment directly.

Start Docker Desktop before the database. init_local.py creates ignored random credentials; after migrations, provision_local.py creates the restricted role and preserves the admin URL in ignored .env. It refuses to unexpectedly rotate an existing role. Never publish .env or data/demo-credentials.json. API and worker need matching database/storage settings.

Ollama must have the configured embedding/generation models. Set the exact embedding digest from local /api/tags. A mismatch fails until reviewed/reindexed. Cross-encoder weights download on first use and stay in the local Hugging Face cache; review/pin the revision for formal release. CPU model quality/latency are measured separately from runtime availability.

Run API and worker in separate terminals; Vite is optional if React was built. start-local.ps1 launches hidden host processes with ignored log files; avoid duplicate listeners. It does not kill unrelated processes. For containers, database and raw-upload volumes must match; use the documented storage override when migrating from host execution.

Corpus capture reads only approved archive members, verifies official source archive SHA-256, records docs archive/page hashes and retains notices. A publisher docs-archive checksum was not established. Capture timestamps do not imply page publication dates. Register your own account before import; demo data is not shared automatically.

Tests use a unique PostgreSQL schema and clean up their synthetic users. Fixture embeddings are not semantic benchmarks. Playwright targets the built app on port 8000 and needs a running API and worker. Set KNOWDOC_TEST_URL to target another endpoint. Against the hosted app, run profile-answer.spec.ts; the full suite includes local-only features. scripts/verify_cloud.py checks hosted upload, storage and permissions with synthetic data and removes its test document. Each browser run writes to its own artifacts directory. Keep the application build fixed during verification.
