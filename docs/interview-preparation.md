# Interview preparation

Use [the demo narrative](project-demonstration.md) for two-, five- and ten-minute presentations. Quote only actual measurements from the report. These questions distinguish architecture decisions from claims that have not been verified.

1. **What problem does KnowDoc AI solve?** Version-appropriate technical answers with inspectable source evidence and document permissions.
2. **Why PostgreSQL plus pgvector?** One durability boundary for metadata, ACLs, FTS, vectors and jobs reduces local infrastructure and consistency boundaries.
3. **Is keyword search BM25?** No. It uses English FTS, sanitized OR terms and ts_rank_cd; label the baseline accurately.
4. **Why hybrid retrieval?** Lexical exact identifiers and semantic similarity fail differently; whether fusion helps is an experimental question.
5. **Why RRF?** It fuses ranks without assuming lexical and cosine scores share a comparable scale; constant 60 is recorded.
6. **Why rerank?** A cross-encoder scores question/passage pairs jointly, at additional CPU/load cost; compare measured results before retaining it.
7. **Is the vector index approximate?** Initial ordering is exact cosine on a bounded corpus; no ANN scalability claim exists.
8. **What defines a source version?** A logical document identity plus immutable source bytes/checksum, declared version metadata and provenance.
9. **Does a new upload mean current?** No. Retrieval/ingestion time does not establish publication or release order.
10. **How do citations stay stable?** Stored chunk/version identities and historical generations retain exact normalized text and quote hashes.
11. **Can citations prove correctness?** They prove stored reference/quote integrity, not that every generated claim is entailed.
12. **How are fabricated citations rejected?** Model aliases map only to known IDs, and quotes must exist in every cited passage.
13. **What does abstention mean?** Evidence/model output did not meet the current checks; it can include false abstentions and needs reviewed evaluation.
14. **How are contradictions detected?** A narrow numeric-policy template detector plus fallible model classification; not exhaustive contradiction reasoning.
15. **Where are ACLs applied?** In the shared SQL base query before text reaches reranking/generation, then separately at source resolution and answer return.
16. **Why recheck after inference?** A long model call can overlap access revocation; the test suite covers that race.
17. **Does the database enforce tenants with RLS?** No. The runtime role is restricted, but ACL enforcement is currently application SQL; RLS is a documented follow-up.
18. **How is prompt injection handled?** Source data has no tool execution capability; permissions are deterministic and citations are validated. Real model obedience still needs adversarial evaluation.
19. **Why a separate worker?** Parsing/embedding do not block the upload request; database leases persist work across process restarts.
20. **How are duplicate workers fenced?** Each claim gets a lease token and final activation checks it; expired attempts are bounded.
21. **What if reindexing fails?** The prior active generation remains searchable and historical citations survive.
22. **Are database and file writes atomic?** No distributed transaction exists; orphan/missing source reconciliation and matched backups are required.
23. **How are parser locations represented?** Real PDF page numbers, DOCX sections/blocks, HTML headings/anchors and normalized text offsets; no invented DOCX pagination.
24. **What happens with scans?** Explicit OCR requirement/dependency errors; optional local OCR has timeouts and quality warnings.
25. **What counts as gold evidence?** Exact annotated quote containment in nominated source/version chunks; equivalent evidence elsewhere can be a strict miss.
26. **How do recall, MRR and nDCG differ?** Recall measures recovered relevant passages; reciprocal rank emphasizes the first relevant result; nDCG rewards relevant results near the top relative to ideal ordering.
27. **What is the benchmark limitation?** Developer-authored, unreviewed and correlated variants; no independent human quality claim yet.
28. **How are performance claims bounded?** Report hardware, warm/cold policy, sample count, model loads and query distribution; one-query latency is not a production SLA.
29. **Why no paid provider?** Core local deployment meets CPU/no-fee constraints and avoids silently sending private text externally.
30. **What would you improve first?** Use measured failure analysis: reviewed annotations/support checks, model choice, parser containment, RLS, token accounting and reproducible backup restore before optional infrastructure.
