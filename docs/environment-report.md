# Environment and resource budget

Observed 2026-11-21 using read-only inventory commands, apart from an incidental Python launcher self-update described below.

| Item | Observation |
|---|---|
| Workspace | Empty at initial inspection; no Git repository; no workspace AGENTS.md found |
| OS | Windows 11 Home, 10.0.26200 |
| CPU | Intel Core Ultra 7 256V; 8 logical processors |
| Physical RAM | 16,690,790,400 bytes, approximately 15.5 GiB |
| Free RAM snapshot | 2,292,544 KiB, approximately 2.2 GiB; varies with other applications |
| Graphics | Intel Arc 140V reported; WMI adapter memory is not a reliable usable model budget; GPU inference untested |
| Python | Default python 3.14.6; `py -3.12 --version` confirms 3.12.10 |
| Node/npm | 24.18.0 / 11.16.0 |
| Docker | CLI 29.5.2; desktop-linux context; engine pipe missing, so daemon unreachable |
| Git | Executable present; workspace not initialized |
| Ollama | CLI present; `ollama list` succeeds; nomic-embed-text (274 MB), mxbai-embed-large (669 MB), gemma:2b (1.7 GB) listed |

Model availability is not evidence of inference quality, RAM usage or throughput. No model inference was run. No Python dependencies, database extension, container build or frontend compatibility tests were run. Python launcher discovery reported a self-update to 26.4; no explicit package installation or project runtime changes were requested.

## Proposed CPU budget, to measure

Database 0.5–1 GiB; API/worker/parsers 0.5–1 GiB; embeddings/reranker 1–2 GiB; frontend/tooling 0.5–1 GiB; optional local LLM 2–4 GiB. Estimated combined 4–9 GiB plus OS and other applications. This does not currently fit the free-memory snapshot. Close memory-heavy applications, limit batch sizes to 8, worker concurrency to 1 and model threads to 4, and avoid loading reranker and generator simultaneously. Start with 24 pages and a 5,000-chunk cap. Plan 10 GiB disk reserve for images, dependencies, models and snapshots; free disk space not yet measured.

After approval: start Docker Desktop, create a Python 3.12 virtual environment, lock compatible dependencies, test CPU model inference and migrations, then measure peak resident memory and warm/cold latency. A failure to fit requires a reported scope decision, not a silent hosted fallback.

## Implementation observations, 2026-11-22

Docker/pgvector now runs successfully; runtime database principal is a restricted non-superuser. Real local embeddings, CPU reranking and Gemma generation were exercised. Ollama reported zero GPU allocation for a loaded Gemma 2B request with context length 4096. Idle container snapshots were roughly 80 MiB worker, 86 MiB API and 84 MiB PostgreSQL; these are not peak model/parse memory figures. Free host memory was about 1 GiB during heavy verification with unrelated desktop/container workloads still running. They were preserved. The measured reports distinguish cold loading from bounded warmed retrieval repetitions.
