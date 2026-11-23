# User guide

Create a local account and collection. Upload PDF, DOCX, Markdown or HTML with a meaningful source version. Processing is asynchronous; watch ingestion activity for ready/failed status. A batch contains at most 20 independent uploads, so earlier successes are not rolled back by a later failure. Scanned PDFs need enabled local OCR dependencies.

Ask your knowledge defaults to Answer with sources: a concise answer with clickable references. Explicit simple profile facts can be extracted directly from the document; other questions use local generation. Supporting passages stay collapsed unless expanded. Evidence only remains available for browsing raw passages and intentionally does not synthesize an answer. The local model can abstain or fail validation even if relevant passages exist. Always inspect evidence for important decisions.

Click a source card for its exact stored text, version and real PDF page or normalized section offsets. Original source download is authorized and private. Publisher links can lead to mutable pages that differ from the stored snapshot. Citation resolution is not proof of semantic support.

In the library, add a version to an existing document with its version action. Duplicate bytes are detected; different bytes with the same label are rejected. Comparison shows the latest two uploaded versions independently, not an asserted release chronology or exhaustive semantic diff. Numeric-policy conflict fixtures are explicitly fictional, not PostgreSQL guidance.

Document settings grant/revoke existing local accounts read access, queue reindexing and delete all versions. Deletion needs a second explicit confirmation in the UI and cannot be undone through the app. Sharing a document does not transfer collection ownership. Revoked users cannot resolve its citations again.

Evaluations show actual saved runs and provisional annotation warnings. Run benchmark requires the approved corpus/fixtures in your account. System health reports configuration and user-scoped counts; database readiness does not prove every model has passed a quality test.

Use the acceptance-checklist.md for step-by-step expectations and verification.
