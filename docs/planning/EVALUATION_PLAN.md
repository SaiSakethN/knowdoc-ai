# Evaluation plan

This is the original evaluation plan. Actual exploratory runs, measured comparisons and known failures are now recorded in docs/evaluation-report.md. Independent review and semantic quality gates remain open.

Create 80 independently reviewed cases after corpus approval: 35 answerable, 10 version-specific, 10 unanswerable, 10 conflicting-source, 10 permission-isolation and 5 prompt-injection cases. Genuine contradictions must be evidenced; use clearly labelled original fixtures if official versions do not supply enough. Never describe synthetic conflicts as publisher contradictions.

Each case stores ID, question, category, allowed user/scope, requested versions, expected facts, gold version/passage IDs and normalized quote spans, expected abstention/conflict behavior, author, reviewer, review status and rationale. Model-assisted drafts require human review; model-only annotation is labelled unreviewed and excluded from release claims. If no human reviewer is available, report provisional developer annotations and keep the human-reviewed gate open.

Freeze source snapshots before annotation. Reserve 20 cases for tuning and 60 held out, stratified by category; report per-category counts and bootstrap intervals where meaningful. Do not tune thresholds on the held-out set. Explicitly report small-sample limitations.

Run A keyword (PostgreSQL FTS, not falsely called BM25), B dense, C RRF hybrid with fusion constant initially 60, D hybrid plus cross-encoder, E complete grounded answers. Keep corpus, filters, candidate budget and hardware fixed. Log cold/warm distinction, seed, git revision, model revision, parser revision, chunk settings, dataset hash and timings. Measure recall@5/10, MRR@10 and nDCG@10 using documented gold relevance grades. Report both passage and document relevance where useful.

Measure citation existence/exact-quote validity separately from semantic support. Human review rates supported claims, correctness and unsupported claims using a published rubric (supported, partial, unsupported). Compute abstention precision/recall against gold unanswerables; report false abstention on answerable cases. Permission tests check zero unauthorized candidate text, reranker inputs, generator inputs and citation responses. Injection cases attempt role override, false citations and data exfiltration; document text never invokes tools.

Proposed release thresholds: 100% deterministic citation validity; zero tested ACL leaks; recall@10 at least 0.85 overall; at least 0.90 abstention precision and recall; at most 0.05 unsupported-claim rate in reviewed answers. These are goals, not established facts. If unmet, publish failures and keep the release gate open. Reranking is retained only for measured benefit at acceptable latency; report regressions too.

Measure p50/p95 retrieval and end-to-end latency over at least 30 warmed repetitions with one active user, plus cold start and ingest throughput on fixed fixtures. Track peak RAM and provider token counts only when available; local mode has no API charge but consumes hardware and electricity. Export JSON/CSV, comparison tables, plots and concrete failure analysis during evaluation implementation.
