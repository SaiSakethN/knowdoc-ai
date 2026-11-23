# ADR 0003: local models and reference validation

Accepted existing-model alternative: installed Ollama Nomic embeddings and Gemma 2B generation, optional CPU MiniLM cross-encoder, and a configurable Sentence Transformers embedding adapter. No hosted fallback exists. Prefix revision and configured embedding digest identify the vector space; model changes require replacement indexes.

Small models struggled to copy long UUID citations. Short temporary evidence aliases map deterministically to stored IDs and improved a short probe without changing the citation trust boundary. Unknown IDs/nonmatching quotes reject output. This proves reference integrity, not semantic entailment. Evidence-only mode is explicitly user selected, not a silent substitute for generated QA. Real quality gates remain measured and reviewed.
