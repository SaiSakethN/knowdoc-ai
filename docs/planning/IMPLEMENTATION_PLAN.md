# Implementation plan

This plan records the original local implementation stages. Current capabilities and verification results are in the project status document.

| Phase | Deliverable | Verification gate |
|---|---|---|
| 0 | Actual environment report and resource estimate | Runtime inventory; Docker blocker documented |
| 1 | Charter, workflow criteria, source/license assessment and governance | Explicit primary corpus approval |
| 2 | Architecture, stack/model strategy and evaluation plan | Explicit major architecture approval |
| 3 | Repository, pinned environments, migrations, Compose and CI definitions | Clean local startup, readiness and foundation checks |
| 4 | Safe uploads, durable jobs, four parsers, provenance, versioning, chunking/indexing | Parser regressions, retry/reindex/delete and worker restart tests |
| 5 | Lexical, dense, hybrid and reranked retrieval | Reproducible measured baselines and ACL/filter tests |
| 6 | Local provider adapter, citation validation, conflicts and abstention | Real inference feasibility and answer contract tests |
| 7 | Accessible web workspace and source viewer | Browser upload → ingestion → ask → open source passage |
| 8 | Security and recovery hardening | Unauthorized retrieval/citation tests, injection and recovery tests |
| 9 | Frozen evaluations and bottleneck-driven optimization | Actual comparison tables, plots and failure analysis |
| 10 | Reproducible local operations | Compose rebuild, CI checks, backup/recovery and runbook |
| 11 | Verified portfolio documentation | Screenshots, demonstration, walkthroughs, interview guide and evidence-backed claims |

Build a Markdown upload-to-citation vertical slice first within phases 3–6, then broaden format and retrieval coverage; do not mark full phases complete from the slice. No placeholder dashboards or fabricated telemetry. Update PROJECT_STATUS.md at every phase with commands, actual outcomes, files and open issues.

## Approved local scope

Approve (1) a maximum 24-page PostgreSQL 18.7/19.0 documentation subset on indexing, text search and concurrency, captured under the documented provenance and notice rules; (2) the modular Python 3.12/FastAPI/PostgreSQL-pgvector/React architecture, local CPU embeddings/reranking and Ollama-first adapter; (3) pypdf as the proposed PDF parser with local OCR adapter rather than adopting PyMuPDF without a license decision; (4) local implementation through verification and handoff under these plans.

Alternative corpus: Python standard-library subset. Alternative PDF choice: explicitly select PyMuPDF after resolving its license obligations. Alternative inference: evidence-only mode if the local model fails feasibility, clearly labelled and requiring scope review if it replaces generated QA.

Costs: no paid resources proposed. Disk, download bandwidth, CPU time and local electricity are required; exact usage remains unmeasured. Risks: currently limited free RAM, stopped Docker engine, model quality, PDF layout/OCR errors, source-version ambiguity, annotation effort and semantic support checking. Mitigations and gates appear in the linked plans.

Approval does not include sending private text to hosted providers, paid subscriptions, public deployment, repository publication, deletion of existing work or significant scope changes. Those remain separate explicit checkpoints from the supplied brief.
