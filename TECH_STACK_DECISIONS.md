# Proposed technology decisions

The user approved the local stack by asking to continue. Resolved versions are pinned in lockfiles and tested. The measured embedding default uses the approved existing Ollama Nomic alternative; current decisions and limitations are recorded in docs/adr and docs/model-cards.md.

| Area | Proposal | Alternative and rationale |
|---|---|---|
| Backend | Python 3.12, FastAPI, Pydantic, SQLAlchemy, Alembic | Default 3.14 is present but 3.12 reduces ML wheel compatibility uncertainty |
| Storage | PostgreSQL 18 plus pgvector, tsvector and GIN | Database release is independent of corpus release; verify extension/image support before locking; SQLite would weaken parity |
| Jobs | Separate Python worker polling leased PostgreSQL jobs | Avoid Redis/Celery until concurrency warrants it; leased retries and idempotent writes still mandatory |
| Parsing | python-docx, Beautiful Soup, Markdown parser; propose pypdf for PDFs | Brief recommends PyMuPDF, whose [license documentation](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright) requires review before adoption; parser change is explicitly part of approval |
| OCR | Optional local Tesseract adapter with explicit missing-dependency/low-confidence statuses | Scanned PDFs cannot be marked fully parsed without OCR evidence; quality and sandbox limits need tests |
| Embeddings | CPU Sentence Transformers all-MiniLM-L6-v2, revision pinned | [Model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2); review license and truncation limit before download; existing Ollama embeddings are an alternative requiring separate index dimensions |
| Reranker | CPU cross-encoder/ms-marco-MiniLM-L6-v2, top 20 candidates | [Model card](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2); opt-in runtime load and measured comparison against no reranker |
| Generation | Provider adapter; localhost Ollama first, existing gemma:2b feasibility probe | Model license and revision must be captured; quality unverified. Deterministic evidence-only mode available but labelled non-generative. No hosted fallback |
| Frontend | React, TypeScript, Vite, Tailwind | Verify current dependencies against Node 24 before locking; accessible native controls |
| Tooling | Compose, pytest, Ruff, GitHub Actions, request IDs and structured logs | Add tracing only where pipeline timing needs justify it; CI initially authored locally, no repository publication |

No dependency compatibility claim is made from presence of a runtime alone. Resolve exact package licenses, transitive dependencies and vulnerabilities before release. Code license remains undecided; do not assign third-party source rights to the project.
