# Model strategy

| Component | Local model | Verification boundary |
|---|---|---|
| Embedding | Ollama nomic-embed-text:latest, 768 dimensions | Real local embedding tested; configured digest and task prefix form index identity |
| Generation | Ollama gemma:2b, installed 1.7 GB artifact | Short valid structured-citation probe; corpus benchmark includes rejections/abstention |
| Reranking | cross-encoder/ms-marco-MiniLM-L6-v2, CPU | Real scoring probe; optional ML extra, four threads and batch 8 |
| Alternative embedding | Sentence Transformers adapter | Configurable, not the measured default; changing dimensions/model requires reindex |

Publisher references: [Nomic](https://huggingface.co/nomic-ai/nomic-embed-text-v1.5), [cross-encoder](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2), [MiniLM alternative](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2), [Gemma terms](https://ai.google.dev/gemma/terms). Review exact artifact licenses before redistribution; weights are not included in this repository or image.

The provider adapter rejects nonlocal hosts by default and follows no redirects. An operator remote flag is not blanket consent to send private documents. No hosted provider/key was used. Local API charge is zero, while hardware/storage/electricity still cost resources.

Context selection uses a character budget and estimated word counts, not exact tokenizer accounting. Context loss, English-domain bias, OCR/layout errors, unsupported statements with valid quotes, and incomplete contradiction detection remain risks. Semantic faithfulness requires separate reviewed evaluation.
