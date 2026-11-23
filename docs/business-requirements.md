# Business requirements

Engineers and technical support teams need to locate version-appropriate guidance and inspect why an answer was produced. The main workflow is collection creation → multi-format upload → asynchronous status → filtered retrieval/answer → exact source passage → comparison across versions. The [charter](planning/PROJECT_CHARTER.md) defines measurable acceptance targets; these are not achieved guarantees.

| Workflow | Implementation | Evidence |
|---|---|---|
| Private workspace | Argon2 passwords, expiring cookies, CSRF/origin checks | API and isolated browser authentication tests |
| Multi-file ingestion | Browser batches of at most 20; bounded individual uploads | Real browser upload; parser/signature/size tests |
| Processing/recovery | Leased jobs, classified errors, retry and atomic generation activation | Expired lease and failed-reindex integration tests |
| Filtered search/QA | Lexical, dense, RRF hybrid, CPU reranking; collection/document/version scope | Real-corpus benchmark and filter tests |
| Source inspection | Authorized normalized passage and original attachment | Browser citation panel and attachment tests |
| Version comparison | Independent passage panels and declared version labels | Desktop comparison test; no invented change claims |
| Privacy | Document grants before model input and recheck after generation | Two-user and mid-inference revocation tests |
| Uncertainty/conflicts | Explicit evidence mode, abstention, quote validation, numeric-policy conflict detector | Citation/injection/conflict tests; model quality measured separately |
| Evaluation/operations | Persisted runs, background tasks, counts and timings | 80 provisional cases; operational status and health endpoints |

The local edition binds to loopback and uses local inference. The hosted edition uses HTTPS, restricted cloud credentials, durable private originals, request-based indexing and bounded storage. Both avoid document bodies in routine logs and enforce document access before returning source text. Distributed request limiting, stronger parser containment and a complete restore drill remain open work. See the cloud guide for the current feature limits.
