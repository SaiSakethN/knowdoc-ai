# Storage model

Users own collections and logical documents; explicit document grants add read access. Immutable versions store labels, byte checksums, original names, format/size, status, provenance, warnings and active index-generation ID. Duplicate bytes within a document are idempotent; changed bytes with the same label return conflict. Collection-level duplicate detection is owner scoped.

Chunks also serve as citation passages, avoiding a redundant passage table. Each stores version/generation IDs, ordinal, exact normalized substring, quote SHA-256, location JSON, estimated word count, embedding identity/vector and tsvector. Location is a real PDF page or section/block plus normalized section offsets. DOCX pages and original byte offsets are never invented. Word counts are estimates, not exact tokenizer accounting.

Ingestion jobs store status, attempts, lease deadline, fencing token, classified error and timings. Evaluation tasks use a separate leased queue; completed runs persist dataset/configuration hashes, metrics, case outcomes and failures. Foreign-key cascades remove grants, versions, chunks and jobs on deletion.

Raw objects use generated version UUID filenames, not uploaded paths. Database/index deletion commits before raw-file cleanup. Interrupted upload/deletion can leave orphans because there is no distributed filesystem/database transaction; consistency checks are required. Old generations remain for historical citations, so storage grows until a citation-aware retention policy is implemented. Migration credentials are separate from restricted runtime credentials.
