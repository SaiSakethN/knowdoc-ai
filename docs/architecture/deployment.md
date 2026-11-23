# Deployment architecture

## Hosted application

The live app at https://knowdoc-ai.vercel.app runs React/Vite and FastAPI as Vercel Services. Neon Free supplies PostgreSQL and pgvector in iad1. The API uses a restricted runtime database role, and migrations run separately with an administrative connection.

Private originals are stored in PostgreSQL rather than the function filesystem. Indexing runs within upload, retry and reindex requests, without an always-on worker. The card-free edition uses keyword search and exact profile extraction; generation, semantic retrieval, OCR and benchmark execution are disabled. Secure cookies are enabled. Public site access does not grant access to other accounts' documents.

See [cloud limits and verification](../cloud-deployment.md).

## Local application

Development runs loopback PostgreSQL in Docker, API/worker on host Python, host Ollama, and Vite or built assets served by FastAPI. A multi-stage Dockerfile also builds React and packages API/worker plus Poppler/Tesseract. Model weights are not included.

Compose exposes PostgreSQL only at 127.0.0.1:54329 and optional app profile at 127.0.0.1:8000. The API startup migrates with an administrative URL, removes that variable from the runtime process environment, then serves with the restricted runtime URL. Worker receives no migration credentials. Containers map host.docker.internal to host-gateway; that explicit mapping was required to reach host Ollama here, without changing the firewall or exposing Ollama publicly.

Initialize the database/role using developer setup before `docker compose --profile app up -d --build`. Host upload storage and Docker's named upload volume are separate: use the matching bind override or matched backup/restore when sharing a database. Never start the same worker twice unintentionally against mismatched storage.

The lightweight image omits optional Python ML dependencies. CPU cross-encoder reranking is available in the host ML environment; container rerank requests fail clearly unless that extra is included in a derived image. Container core embeddings/generation use host Ollama. This distinction limits container feature claims.

The local pipeline retains the worker and Ollama configuration. Its filesystem storage and inference behavior differ from the hosted edition described above.

Verification used API_PORT=8001 with compose.local-storage.yaml while the host development API remained on 8000. The override binds the same data/uploads directory to both app containers. Remove the temporary port override for canonical startup after stopping the host listener. Container OCR extracted the expected text from an image-only fixture with real page 1 metadata and an OCR limitation warning.
