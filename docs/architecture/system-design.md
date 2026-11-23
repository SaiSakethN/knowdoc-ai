# Implemented system design

`src/knowdoc` contains FastAPI endpoints, PostgreSQL models, security predicates, parsers, provider adapters, jobs, retrieval, grounding and evaluation. `apps/web` is React/TypeScript/Vite with Tailwind and ordinary CSS. Migrations, tests and explicit operator scripts are version controlled.

HTTP ingestion checks access and bounded source bytes, stores a checksummed immutable version and queues a job. A worker claims it with SKIP LOCKED, verifies the hash, parses, chunks and embeds locally, then activates a complete replacement generation in one transaction. Failed rebuilds preserve the previous index. Old chunks remain for citation resolution.

Both lexical and vector retrieval use the same authorized document join. Keyword search is sanitized OR-term English PostgreSQL FTS with ts_rank_cd, not BM25. Dense search is exact pgvector cosine ordering on this bounded corpus, not a claimed scalable ANN service. RRF uses constant 60, optional cross-encoder reranks at most 20 candidates, and duplicate/diversity controls select evidence.

Nomic query/document prefixes and configured digest are part of the embedding identity; digest mismatch fails rather than silently mixing spaces. The Sentence Transformers adapter is available but is not the measured default. Answers use a conservative relevance gate and an 11,000-character evidence cap. Local generation gets temporary short IDs, which map back only to known stored sources. Unknown IDs, missing quotes or mismatched quotes reject output. Valid references do not prove semantic entailment.

Numeric-policy conflict detection compares identical sentence templates with differing values/units and returns both passages/versions. General contradictions remain fallible. Source labels never become current merely through newer ingestion time.

See [storage](data-model.md), [security](security-model.md), [evaluation](evaluation-design.md), [deployment](deployment.md), and [diagrams](diagrams/README.md).
