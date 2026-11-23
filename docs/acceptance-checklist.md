# Expected behavior and how to check it

Open https://knowdoc-ai.vercel.app or the local app at http://127.0.0.1:8000/. Select the intended collection or source version when several documents could answer. The hosted edition supports keyword search and exact profile extraction; general questions return passages with a clear no-generation message. The local edition also supports Ollama generation.

| Check | Expected result | How to verify |
|---|---|---|
| Default experience | Answer with sources is selected | Inspect the answer-mode selector in a new conversation |
| Simple identity fact | One short answer using the name explicitly written in the document | Ask “what is your name”; compare the answer against the introduction |
| Current role | Current title and employer, not an earlier position | Ask “what is your current role”; check the explicit present-tense introduction and current-employer passage |
| Citation | A clickable [1] next to the answer | Click it; verify document, version, actual PDF page/section and supporting text |
| Compact presentation | No paragraph dump beneath a simple answer | Source passages stay collapsed under Sources; expand them only when desired |
| Missing information | An honest insufficient-evidence response | Ask about a fact you have confirmed is absent; it must not invent a value or substitute unrelated guidance |
| Ambiguous identity | Clarification rather than choosing a person arbitrarily | Add two profiles with different names in scope, then ask for the name |
| Explicit passage browsing | Source excerpts without a generated answer | Select Evidence only and repeat a question; this behavior is intentional in that mode |
| Version isolation | Answer/citation stays inside the selected version | Select one source version, ask a question, and inspect the reference version |
| Privacy | Another account cannot retrieve a private document | Sign out, create/use a different test account, and search for an exact phrase from the private source; grant read access explicitly if sharing is intended |
| No external inference | Private text stays with the configured local provider | Hosted providers are disabled by default; do not enable a remote provider without explicit data authorization |

Simple explicit profile facts use deterministic source extraction where the evidence is clear. They still resolve their quotes to actual stored spans, obey document access rules and ask for clarification on conflicting profile values. Other questions use local answer generation. This is not an assurance that all generated statements are semantically correct.

## Automated checks

From the project root, with PostgreSQL running:

```powershell
.venv/Scripts/ruff check src tests scripts migrations
.venv/Scripts/pytest -q
npm --prefix apps/web run build
```

Run API and worker, then in apps/web:

```powershell
npx playwright test
```

The browser suite targets the built app on port 8000, uses synthetic accounts and writes each run to a separate directory under artifacts/browser. The profile-answer test verifies the default answer mode, a concise name/current-role answer, one clickable reference and collapsed passages on desktop/mobile. Do not edit production source during a verification run.

Pass criteria: expected fact correct, reference supports it, source version/page correct, no unauthorized source text, no invented value. Test-suite passes do not replace independent review of real generated answers. Historical quality measurements and remaining release gates are in evaluation-report.md.

Current employer check: select the resume, choose Answer with sources, and ask "What is his current company?" Expect the employer on the explicit date-to-Present employment line and a reference to that page. Repeat with both documents selected. Past employment must not be presented as current.
