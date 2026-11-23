# KnowDoc AI project charter

Prepared 2026-11-21 for the original local implementation. This charter defines objectives and targets, not a claim that every release-quality gate has passed.

KnowDoc AI will help engineers and technical support teams answer questions across evolving technical documents while exposing exact evidence, source versions, and uncertainty. It must not promise error-free answers or enterprise certification.

The signature workflow is upload → track ingestion → search or ask → inspect citations → compare source versions. The system must enforce document permissions before text reaches retrieval outputs, reranking, or generation.

## Scope and acceptance

| Workflow | Acceptance criterion | Nonfunctional target |
|---|---|---|
| Upload multiple documents | PDF, DOCX, Markdown and HTML fixtures ingest; invalid types and oversized files fail clearly | Proposed 20 MiB/file, 20 files/batch; upload returns job ID without parsing inline |
| Track ingestion | Queued, running, ready and failed states visible; retry is idempotent | Job survives worker restart; no private text in logs |
| Search | Collection, document, version and ACL filters work for all four retrieval baselines | Warm CPU p95 under 2 seconds at 5,000 chunks, measured after implementation |
| Ask | Structured answer or explicit abstention with evidence and uncertainty | Proposed local answer p95 under 30 seconds; hardware feasibility gate applies |
| Open citation | Citation resolves to stored version, passage and available location metadata | Every returned citation resolves; revoked access fails on subsequent resolution |
| Compare versions | User can select two versions and see distinct passages and superseded labels | Ingestion time never implies publication order |
| Inspect conflicts | Opposing passages shown with version/date provenance | Contradiction detection limitations shown; no guarantee of exhaustive detection |
| Manage privacy | Private collection and per-document grants tested with two users | Zero unauthorized passages across tested API, citation, worker and retrieval paths |
| Evaluate | Reproducible run exports metrics, configuration and failure examples | No fabricated scores; held-out cases and annotation status recorded |
| Operate locally | New developer can start services using documented commands | No paid provider or GPU required; measured memory budget |

Targets are proposed release criteria, not achieved measurements. Accessibility target: keyboard usable core flows, labelled controls, visible focus, loading/error/empty states. Core demo target: one concurrent query and one ingestion worker.

Out of initial scope: internet-wide crawling, automated cloud deployment, enterprise SSO certification, high availability, and guaranteed contradiction detection. OCR remains required but must expose unavailable/failed status rather than silently dropping scanned pages.

Deliver in gated phases, preserving the supplied requirements. Later portfolio claims must cite actual tests, measurements and screenshots.
