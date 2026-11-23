# Source governance

All corpus changes require an allowlisted source, publisher and version evidence, license record and access-policy review. Public accessibility alone does not authorize redistribution. Keep source notices with redistributed material and exclude third-party assets unless individually cleared.

Record byte hashes before normalization. Preserve original snapshots, parser revision and normalization rules. Never replace a previous version in place. A changed hash creates a candidate version; a newer retrieval timestamp does not establish newer guidance. Mark latest only within a verified release family and expose verification date.

The proposed refresh is manual and manifest driven. Diff bytes and parsed passages, review changed version claims, rerun parser and retrieval regressions, then atomically activate the new index generation. Failed indexing leaves the previous generation active. Deletion revokes access immediately, then removes raw objects, passages, embeddings and cached answers; document backup retention in the implementation runbook.

Private uploads remain local and owner-scoped. Default logs contain identifiers, status, timings and classified errors, not content. Hosted generation is disabled unless explicitly approved for the relevant data. Uploaded text is untrusted and cannot grant permissions or trigger tool execution. Public demo corpus rights do not change private upload rules.

Before initial ingestion, validate the full allowlist, archive contents and checksums, applicable notices, robots rules and actual capture dates. Unresolved provenance is displayed as unknown and blocks public redistribution.
