# ADR 0004: pre-retrieval access and leased jobs

Use SQL ownership/grant predicates before retrieval output reaches the reranker/model; authorize source access separately and recheck after inference. Separate runtime and migration roles. Application ACLs are implemented; RLS is deferred and documented.

Use SKIP LOCKED claims, expiring leases and fencing tokens rather than in-process tasks. Renew ingestion leases between embedding batches; bounded attempts and atomic activation preserve prior indexes on failure. Evaluations use their own queue/longer lease. A crash can replay an evaluation; exactly-once execution is not guaranteed. Operator reconciliation is necessary for filesystem/database interruptions.
