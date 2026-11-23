# Project status

Updated November 23, 2026.

**Live:** https://knowdoc-ai.vercel.app

**Source:** https://github.com/SaiSakethN/knowdoc-ai

## Current release

The hosted app runs the React frontend and FastAPI backend on Vercel Services, with PostgreSQL and pgvector on Neon Free. Private originals are stored in the database behind document permissions. The API uses a restricted runtime database role.

The card-free deployment supports accounts, collections, uploads, keyword retrieval, exact supported profile answers, citations, sharing, revocation, version comparison, reindexing and deletion. General AI generation, semantic retrieval, OCR and benchmark execution are disabled in this edition. Local installations retain the Ollama pipeline and optional CPU reranker.

Cloud limits: 3 MiB per file, 20 MiB of originals per account, 150 MiB of originals across the deployment, and 200 chunks per source. No paid plan, purchased AI credits or auto top-up was enabled. Local accounts and private uploads were not migrated.

## Verification

| Check | Result |
| --- | --- |
| Ruff and TypeScript/Vite build | Passed |
| Backend suite | 37 passed |
| Full local desktop/mobile suite | 9 passed, 1 intentional skip |
| Production desktop/mobile profile flows | 2 passed |
| Production API smoke | Upload, indexing, answers, citations, originals, permissions, reindex and deletion passed |

Verification used synthetic accounts and documents. The [cloud guide](docs/cloud-deployment.md) records deployment configuration and the [verification report](docs/verification-report.md) retains prior checks.

## Remaining work

- Independently review evaluation annotations and measure generated-answer correctness.
- Broaden profile extraction and conflict handling beyond the current conservative patterns.
- Complete a backup restoration exercise and strengthen distributed rate limiting and parser isolation before a larger public rollout.

Historical measurements remain available in the [evaluation report](docs/evaluation-report.md). Planning documents and the development log are in [docs/planning](docs/planning/README.md).
