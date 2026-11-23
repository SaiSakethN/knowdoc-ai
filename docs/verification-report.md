# Verification report

## Current release: November 23, 2026

Live deployment: https://knowdoc-ai.vercel.app. Ruff and the production frontend build pass. The backend suite has 37 passing tests; local desktop/mobile coverage has 9 passes and 1 intentional skip. Both production profile browser checks pass. The live API smoke covers upload/indexing, exact name/company answers, citations, originals, cross-account denial, sharing/revocation, reindexing, explicit no-AI fallback and deletion. All cloud checks used synthetic documents. See [cloud deployment](cloud-deployment.md).

The records below retain earlier local measurements. Their counts and scope describe those runs.

## Earlier local verification

Updated 2026-11-22. Scope: a local user authenticates, uploads a document, waits for asynchronous indexing, queries authorized sources and opens the exact stored citation/original. Synthetic test accounts and public documentation were used; no private documents were sent to a hosted provider.

| Boundary/check | Actual evidence |
|---|---|
| Backend unit/database/API/security tests | 32 pytest cases passed after quote-span and API schema additions; PostgreSQL test schema isolation |
| Frontend production build | TypeScript and Vite build passed |
| Browser core workflow | 7 isolated Playwright tests passed; 1 intentional skip for a desktop-only benchmark screenshot. Coverage includes registration, upload, indexing, citation, document controls, error states and account switching. |
| Account switch regression | Desktop/mobile both passed in the final suite after fixing the hidden mobile sign-out control and unmounting account-specific state |
| Runtime role | knowdoc_app is non-superuser and cannot create databases |
| Corpus | 24 official pages captured; initial six overview failures fixed and retried; active document jobs ready |
| Real embedding/reranker | Ollama 768-dimensional embedding and CPU cross-encoder probes succeeded |
| Historical references/recovery | Reindex/filter, stable historical citation, expired lease, exhausted attempt and failed-reindex preservation tests passed |
| Authorization | Private passages excluded from reranker/generator callbacks; revocation during inference rejected on answer return |
| Source consistency | 48 stored versions checked with zero findings again after the final disposable smoke fixtures |
| Container deployment | Multi-stage images built; API served built web; real upload/embedding/evidence/citation/original/delete smoke passed on loopback port 8001 |
| OCR | Image-only PDF parsed through container Poppler/Tesseract; extracted expected GIN text with page 1 and explicit OCR warning |
| Retrieval benchmark | Four methods × 45 provisional source-evidence cases completed with zero retrieval provider errors |
| Performance | 30 warmed repetitions per method; actual samples and p50/p95 in evaluation report |
| Generation | Initial answerable sample failed its quality gate; two revised corpus probes returned accepted references; full follow-up completed: 20/45 accepted reference-valid answers; semantic quality remains ungraded |
| CI | Workflow authored; no remote GitHub Actions run or publication claimed |

## Commands

`ruff check src tests scripts migrations`; `pytest -q`; `npm --prefix apps/web run build`; `npx playwright test`; focused account-isolation mobile regression; `scripts/fetch_corpus.py`; `import_corpus.py`; `seed_evaluation.py`; `wait_index.py`; `evaluate.py`; `performance.py`; `check_consistency.py`; `docker compose build api worker`; app profile with matched local storage bind; `scripts/smoke.py --base-url http://127.0.0.1:8001`; container OCR fixture probe. Full machine-readable local artifacts stay under ignored artifacts; measured public-data benchmark and selected screenshots are preserved in docs.

## Failures found and corrected

Windows localhost database connection hang → use explicit 127.0.0.1. Ambiguous SQLAlchemy historical citation join → explicit join conditions. Test-schema fallback to public migration metadata → schema-specific version table and isolated creation. Chapter overview parsing selected a nested TOC span → select the containing chapter and retain overview/TOC. Browser origin mismatch → exact configured loopback origin. Test queued-job contamination → per-client generated-account cleanup. Container host inference DNS failure → explicit host-gateway mapping. Hidden mobile sign-out → visible narrow-layout control. Workspace state surviving account switch → unmount keyed workspace. Quote whitespace copying → deterministic actual-span resolution; semantic support is still not guaranteed.

## Limits

Native in-app/Chrome verification was blocked by the computer-use host/policy, so UI automation used fresh isolated Playwright test browsers instead of the user's profile. No formal accessibility/security certification, independently reviewed answer-quality labels, full backup restore drill, GPU benchmark, public deployment or remote CI execution is claimed. Container image omits optional CPU reranking dependencies; host ML verification is distinct from the lightweight image.

Final canonical runtime: built web/API at http://127.0.0.1:8000 with a separate host worker and loopback database container. The temporary app containers on port 8001 were stopped after verification; their data and the PostgreSQL volume were preserved. Final host upload-to-citation/original/delete smoke passed.

## Final verification isolation, 2026-11-23

A mobile generation check failed while a Vite hot-reload reset the visible workspace and another Playwright run removed its active trace files. The test configuration now defaults to the unchanged built application on port 8000, uses one worker, and assigns a unique output directory per run. Final sequential suite results are recorded below after completion; this setup avoids mistaking development reloads or artifact collisions for application/model failures.

Final sequential result on the built app: **7 passed, 1 intentional mobile screenshot skip in 52.8 seconds**. Both desktop and mobile completed upload, real local generation, source resolution, document management and deletion. Backend: **32 passed in 6.35 seconds**. Vite logs confirmed page reloads and Fast Refresh invalidation during the earlier development-preview failure. Temporary Vite preview was stopped; the canonical built app remains on port 8000. A consistency observation during concurrent deletion was transient; checks after the suite completed are the authoritative snapshot.

## Answer-first acceptance fix, 2026-11-23

The default now returns concise answers with inline clickable references and collapsed passages. Explicit Evidence only mode remains available. Conservative profile extraction and profile-intent retrieval were verified against the user-provided PDF locally, without copying private content into repository fixtures. Synthetic profile regression tests cover name/current role, previous-role exclusion, ambiguity and source resolution. Full validation: 35 backend tests passed; 9 browser tests passed, 1 intentional screenshot skip. Both desktop/mobile verify answer-first defaults and compact citations. The historical 80-case model benchmark predates this targeted change and was not rerun.
