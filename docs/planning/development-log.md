# Development history

Historical notes from the local implementation and initial cloud release. Statements below describe the stage at which they were recorded; see [current status](../../PROJECT_STATUS.md) for the deployed application.

# KnowDoc AI project status

Updated 2026-11-23. The initial scope used the PostgreSQL reference corpus and a local architecture. A working local implementation is available. The release remains provisional because independent annotation review and generated-answer semantic quality are not established.

## Phase outcomes

| Phase | Actual state |
|---|---|
| 0 Environment | Windows/Python/Node/Docker/RAM audited; original Docker/localhost blockers resolved |
| 1-2 Discovery/design | Approved PostgreSQL 18.7/19.0 subset and local modular architecture; design/ADRs recorded |
| 3 Foundation | Locked Python/JS environments, PostgreSQL/pgvector, migrations, restricted runtime role, Compose and local CI commands verified |
| 4 Ingestion | PDF/DOCX/HTML/Markdown, checksums, versions, queued jobs, exact offsets and index replacement tested; real container OCR probe succeeded |
| 5 Retrieval | Four real baselines evaluated on 45 provisional source-evidence cases; results/plots/failures saved |
| 6 Generation | Local schema-constrained generation, deterministic citation/span resolution, explicit abstention and narrow numeric conflicts implemented; initial quality failures retained; full follow-up recorded: 20 of 45 accepted referenced answers; 24 abstentions and 1 clarification; no provider errors |
| 7 Application | Private auth/workspace/library/upload/citations/version comparison/document controls/evaluations/health implemented; 7 browser tests passed, 1 intentional desktop-only screenshot skip |
| 8 Robustness | 32 backend tests passed, including privacy input boundaries, mid-generation revocation, chunked body limits and worker recovery; residual hardening documented |
| 9 Evaluation | 80-case dataset, real four-method comparison and 30 warmed repetitions/method completed; human correctness/faithfulness labels remain open |
| 10 Operations | Multi-stage container build, real container upload-to-citation/original/delete smoke and OCR verified; CI authored but not run remotely; no full backup restore claim |
| 11 Portfolio | Substantive guides, 11 Mermaid sources, measured plots, screenshots, demo narrative and 30 interview answers delivered locally |

## Actual verification

- `ruff check src tests scripts migrations`: passed after fixes.
- `pytest -q`: 32 passed in the latest full backend run.
- `npm --prefix apps/web run build`: TypeScript/Vite production build passed.
- `npx playwright test`: 7 passed, 1 intentional mobile skip for a desktop-only benchmark screenshot. Later focused evaluation-display test also passed.
- `fetch_corpus.py`: 24 approved HTML pages captured with hashes, notices, verified source archive checksums and a source manifest.
- `import_corpus.py`, `seed_evaluation.py`, `wait_index.py`: real local embeddings indexed approved sources and original fixtures; overview parse failures were corrected/retried.
- `evaluate.py`: 45 cases per retrieval method, zero retrieval provider errors. Recall@5: keyword .444, dense .711, hybrid .644, hybrid/rerank .911. These are exploratory unreviewed results.
- `performance.py`: 30 warmed repetitions per method. p95 ms: keyword 18.9, dense 1001.5, hybrid 1070.1, hybrid/rerank 1303.4. One query/user, not a production SLA.
- Initial generated answerable sample: 6 attempts for nominal budget 5 due to an attempt-count bug, zero accepted answers; fixed budget accounting and grounding diagnostics are documented. The full follow-up recorded 20 accepted referenced answers, 24 abstentions and 1 clarification across 45 attempts, with zero provider errors. These are not correctness scores.
- `check_consistency.py`: 48 stored versions checked with zero findings before subsequent disposable smoke fixtures.
- `docker compose build api worker`: successful images with compiled web assets, runtime API/worker and OCR tools.
- Container smoke on 127.0.0.1:8001: database/vector ready, web served, real embedding ingestion, evidence/citation/original resolution and delete revocation passed.
- Container startup race found by smoke was fixed using API healthcheck and worker healthy dependency. API process migration URL removal was verified via /proc/1/environ; runtime DB principal is knowdoc_app.
- Image-only PDF OCR returned expected GIN text on actual page 1 with an OCR limitation warning.
- Local credential scan of unignored text files found no actual local database credential values.

## Files and decisions

Implementation lives in src/knowdoc, apps/web, migrations, tests and scripts. Runtime/container config is in compose.yaml, compose.local-storage.yaml, Dockerfile, .env.example and lockfiles. Evaluation data, original fixtures, source/model manifests, measured artifacts and documentation are version controlled; raw uploads, archives, local credentials, caches and transient test traces are ignored. Original code uses MIT; PostgreSQL excerpts retain their notice. No model weights are redistributed.

Important fixes: explicit historical citation joins; schema-isolated migration/test setup; chapter overview parsing; loopback origin/database resolution; queued test cleanup; host inference DNS mapping; expired final-attempt state; exact whitespace-only quote span resolution; keyed workspace unmount on account switch; visible mobile sign-out; truthful unavailable metric rendering; classified safe errors and bounded streamed bodies.

## Open release gates and limitations

Independent human review, semantic support/correctness scoring, unsupported-claim rate and calibrated abstention remain ungraded. Narrow policy conflicts and synthetic privacy/injection tests are not exhaustive guarantees. Field-separated real tests confirmed two copied attack instructions in generated claims, beyond the initial whole-response flags. A narrow unsafe-instruction rejection was added; both focused real-provider retests abstained without the attack text. This is not exhaustive protection. No RLS, hardened hostile-parser sandbox, formal accessibility/security certification, complete transitive audit or full backup restore drill is claimed. Lightweight containers omit optional CPU reranking dependencies; host ML verification is separate. Local generation was observed with zero GPU allocation; other desktop/container workloads constrained free memory.

No hosted private-document inference, paid resource, GitHub publication or public deployment occurred. Local source changes are uncommitted. See docs/verification-report.md and docs/evaluation-report.md for evidence and scope. Local handoff is prepared. Independent review and the semantic generation release gate remain open. Focused regressions now reject generic-word-only unrelated evidence and copied unsafe instructions; both observed attack-contamination cases abstained in real-provider retests. Full historical results are preserved.

## Final handoff verification, 2026-11-23

Sequential testing against the frozen built application passed 7 browser tests with 1 intentional desktop-only screenshot skip on mobile (52.8 s). Both form factors now cover real local generated answers and citations. Backend suite: 32 passed (6.35 s). Test artifact paths are unique per run; production code was held unchanged during verification. Vite reloads/artifact collisions explained the prior development-preview test failure. The temporary Vite preview is stopped; built API/web and host worker remain running with the loopback PostgreSQL container. Generation semantic quality and human review remain explicitly provisional.

## Answer-first correction, 2026-11-23

Changed the default from passage browsing to Answer with sources at both API and UI layers. Answers now show compact clickable reference buttons and collapsed supporting passages. Added conservative exact-source profile extraction, pronoun-aware profile retrieval and clarification for conflicting identities. The user-provided PDF name/current-role questions resolved to the correct page-1 statements in local checks (about 1.04 s and 0.71 s); private document content is not copied into repository fixtures. Backend suite: 35 passed. Final frozen-build verification passed 9 browser tests with 1 intentional screenshot skip, including concise profile answers and reference opening on desktop/mobile. See docs/acceptance-checklist.md for user-facing expectations and checks. Historical model benchmark scores predate this change and were not remeasured here.

### Current-company correction (2026-11-23)
Recognizes current-company/employer and where-does-he-work questions; retrieves Present employment evidence and extracts explicit resume company/title/date lines with stored-span citations. Past-only employment still abstains. Verified locally against both uploaded documents and resume-only scope; private source text was not added to fixtures. Backend: 36 passed; focused profile tests: 4 passed.

### Professional interface and public source release (2026-11-23)
Replaced the dark navigation and green palette with a white workspace, indigo accents, a consistent book mark, quieter cards, revised account screens and responsive spacing. Starter prompts now fit general uploaded documents. Frontend build, Ruff and 36 backend tests pass; full desktop/mobile browser suite: 9 passed, 1 intentional skip. Sign-in and workspace screenshots were visually inspected using synthetic accounts. Public source excludes local credentials, private uploads, model weights and runtime data. Hosted launch is pending the deployment target.

### Card-free Vercel release (2026-11-23)
Live at https://knowdoc-ai.vercel.app. Vite and FastAPI deploy as Vercel Services; Neon Free stores indexed passages and permission-protected originals using a restricted runtime role. Existing local private uploads were not moved. Per user choice, generation and semantic embeddings are disabled because Gateway requires card verification. The cloud UI declares keyword retrieval and conservative exact profile answers; general questions receive passages with an explicit no-generation explanation. Limits: 3 MiB per file, 20 MiB of originals per account, 150 MiB globally, 200 chunks per source. No paid resources or AI credits were purchased. Frontend build/Ruff and 37 backend tests pass; production API smoke and two desktop/mobile browser flows pass. See docs/cloud-deployment.md.

The complete local browser regression suite also passed after the cloud changes: 9 passed, 1 intentional skip. GitHub is connected to Vercel for future deployments.
