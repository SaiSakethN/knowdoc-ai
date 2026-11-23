# Card-free Vercel deployment

Live application: https://knowdoc-ai.vercel.app

The Vite interface and FastAPI API deploy together using Vercel Services. PostgreSQL and pgvector run on Neon's Free plan in the same region (iad1). The API uses a separate restricted database role. Private originals are stored as database bytes, behind the same permission checks as citations, so uploads survive stateless function restarts. Existing local accounts and private uploads were not migrated.

## Included behavior and limits

- Registration, sign-in, collections, PDF/DOCX/Markdown/HTML uploads, versioning, sharing, revocation and deletion.
- Real PostgreSQL keyword search. Semantic retrieval and CPU reranking are unavailable in this deployment; no placeholder embeddings are used.
- Conservative exact profile extraction for supported name and present employment statements, with validated citations. Other questions show relevant passages and an explicit message that general AI generation is disabled.
- Files up to 3 MiB; 20 MiB of originals per account; 150 MiB of originals across the deployment; up to 200 chunks per indexed source. These application limits leave room for indexes and metadata within the free database quota; they do not guarantee capacity under arbitrary traffic.
- Indexing runs within the upload, retry or reindex request; no always-on paid worker. Scanned PDFs requiring OCR are unsupported in the cloud edition.
- Local benchmark execution remains local. No background polling keeps the cloud database awake while the workspace is idle.

Vercel AI Gateway refused synthetic requests because this team has not completed card verification. The user selected the card-free option. `GENERATION_BACKEND=disabled` and `EMBEDDING_BACKEND=disabled` prevent provider calls. No credits were purchased, no auto top-up was enabled, and no paid plan was selected. Future use of AI Gateway requires separate configuration and verification of its current free allowance; do not silently enable a paid fallback.

## Operations

Cloud secrets live in Vercel environment variables. `KNOWDOC_DATABASE_URL` takes precedence over the integration's administrative `DATABASE_URL`. Local `.env.cloud`, `.env.cloudruntime`, `.env.local` and `.vercel` state are ignored by Git and excluded from uploads. Local `.env` still selects the full Ollama edition.

Migrations are applied explicitly with an administrative connection before release, rather than on every function startup. After schema changes, grant the runtime role only the required new table privileges. Never commit or print connection strings.

Use `vercel deploy --prod` from the linked checkout, or the connected GitHub repository. Preview deployments are not provisioned with production runtime configuration automatically; do not treat a preview URL as a verified production environment.

## Verification on 2026-11-23

- Frontend production build and Ruff pass; 37 backend tests pass, including persistent source storage, keyword-only indexing, extraction, reindexing, download and cascading deletion.
- Unauthenticated live home page, capabilities and readiness endpoints return HTTP 200.
- `python scripts/verify_cloud.py https://knowdoc-ai.vercel.app` passed registration, upload/indexing, name/company answers, stored citations, original download, cross-account denial, sharing/revocation, reindexing, honest no-AI fallback and deletion. It used synthetic text and removed its test document.
- Desktop and mobile Playwright profile checks both passed against the production URL, including inline references and company answers. Screenshots were visually inspected; all sample text was synthetic.

This is a small free-tier demonstration deployment. Citation integrity checks do not prove semantic correctness. The existing human-review evaluation gates remain open.
