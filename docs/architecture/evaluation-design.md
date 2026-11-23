# Evaluation design

[benchmark.json](../../evals/benchmark.json) has 80 developer-authored cases: 35 answerable, 10 version-specific, 10 unanswerable, 10 original conflict variants, 10 permission cases and 5 injection cases. Every case has expected behavior, gold source/version/quote where applicable, split and review status. Questions are not produced by the evaluated local model. Human review is pending; variants are correlated, not independent experimental units.

Ten answerable cases are development split; the remainder are provisional holdout. Until independent review and tuning freeze, aggregate scores are exploratory rather than a held-out quality claim. Retrieval compares lexical, dense, RRF hybrid and hybrid/reranking on the same 45 answerable/version-specific cases. Gold relevance is exact quote containment in the nominated version's active chunks. Equivalent evidence in another version can count as a strict miss.

Metrics: recall@5, reciprocal rank at 5, binary nDCG@5, latency, citation reference/text integrity, expected-status match and forbidden-sentinel absence. Generation is bounded to selected answerable cases plus all injection cases. Semantic correctness, faithfulness, unsupported-claim rate and semantic abstention precision remain ungraded until human labels exist; deterministic proxies are not relabelled as these metrics.

Runs preserve dataset hash, source checksums, embedding identity, generation model, RRF/top-k, Python/platform, timestamp and Git revision when available. Exploratory timing includes model loads; a separate warmed repetition script handles performance. Proposed release thresholds remain open when human labels are missing or measured targets fail.
