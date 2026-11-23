# API guide

The hosted API uses https://knowdoc-ai.vercel.app/api/v1. Uploads are limited to 3 MiB and index within the request. Keyword retrieval and supported profile extraction are enabled; general questions return source passages with an explicit no-generation explanation. Benchmark task creation is disabled. GET /api/v1/capabilities reports edition, provider state, retrieval support and upload size. Originals are durable private database bytes. See [cloud limits](cloud-deployment.md).

OpenAPI UI: `http://127.0.0.1:8000/docs`; schema: `/openapi.json`. Prefix `/api/v1`.

Register/login via `POST /sessions/register` or `/sessions/login` with email/password JSON. HttpOnly cookie is set and response returns csrf_token; send it as X-CSRF-Token on authenticated mutations. GET /sessions/me restores the token; DELETE /sessions/current signs out. Unauthenticated private calls return 401; unauthorized object lookups use 404.

| Route | Behavior |
|---|---|
| GET/POST /collections | Owned private collection list/create |
| GET/POST /documents | Authorized library; multipart upload returns 202 job or scoped duplicate result |
| GET /documents/{id}/versions | Authorized version metadata |
| GET /versions/{id}/passages | Paginated active stored passages |
| GET /versions/{id}/original | Authorized original attachment |
| POST /versions/{id}/reindex | Owner queues replacement index |
| DELETE /documents/{id} | Owner deletes all versions, chunks and grants |
| GET/POST /documents/{id}/grants | Owner lists/grants existing users read access |
| DELETE /documents/{id}/grants/{user_id} | Owner revokes access |
| GET /jobs; POST /jobs/{id}/retry | Owner processing status/retry |
| POST /search; /answers | Scoped retrieval or evidence/generated answer |
| GET /citations/{id} | Authorized exact text/location/hash resolution |
| GET/POST /evaluations | Owner reports and background task creation |
| GET /evaluations/{id} | Owner full benchmark report |
| GET /system | User-scoped counts and nonsecret configuration |
| GET /health/live; /health/ready | Process and schema/vector readiness |

Upload fields: collection_id, label, optional document_id/source_url, file. Search JSON: question, method (keyword/dense/hybrid/hybrid_rerank), top_k 1–20, optional collection_id/document_id/version_ids. Answers add mode evidence/generate. Response includes status, answer, claims, citations, conflicts, limitations, timings and optional usage. Provider failure returns 503 and never silently invokes a paid API.

List limit/offset maximum is 100; passages maximum 200. Errors have machine code/request ID where assigned; validation returns field paths without echoing private input. Body limits can reject before normal validation. Rate limits are local-process scope.
