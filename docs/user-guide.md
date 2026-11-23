# Using KnowDoc AI

Open [the hosted app](https://knowdoc-ai.vercel.app), create an account, and create a collection. Cloud accounts are separate from local accounts.

## Add documents

Upload PDF, DOCX, Markdown or HTML. Use a meaningful version label when a source has multiple releases. The hosted app accepts files up to 3 MiB and indexes them during upload. The local edition accepts 20 MiB by default and processes jobs in the background. Check the library's ingestion activity for failures.

Scanned PDFs need OCR, which is available only in a configured local installation. Duplicate file contents are detected within your documents; a version label cannot be reused for different contents in the same document.

## Ask and inspect

Choose the collection or source version you want to use, then ask a question. **Answer with sources** is the default. Supported explicit profile facts, such as a name or a current company stated in a date-to-Present employment line, can return a short answer with a reference.

Click **[1]** to inspect the supporting passage, source version and PDF page or section. Expand **Sources** for more detail. The original file is available through the source panel. A resolved citation confirms the stored passage; it does not independently establish that every statement is correct or current.

The hosted edition uses keyword search and exact profile extraction. For general questions it displays relevant passages and explains that AI generation is disabled. The local edition can use Ollama to generate referenced answers, but may abstain or reject output that fails its checks. **Evidence only** explicitly requests source passages without generation.

If sources describe different people or conflicting facts, select the intended document/version rather than relying on upload order to establish currentness. Starting a new conversation does not change your uploaded sources.

## Versions and sharing

In the library, add a version to an existing document or compare its latest two uploaded versions. Comparison displays their stored passages independently; it is not an exhaustive semantic diff.

Document settings let an owner grant read access to another registered account, revoke access, reindex or delete a document. Sharing does not transfer collection ownership. Revoked readers cannot open its citations or original again. Deletion removes all source versions and requires confirmation; the app has no undo action.

## Limits and troubleshooting

The free deployment allows 20 MiB of originals per account and 200 chunks per source. See [cloud limits](cloud-deployment.md) for the deployment-wide cap. Reduce a large document or split it into smaller sources if indexing exceeds the chunk limit.

For failed jobs, check ingestion activity, correct the underlying issue and retry. System health shows account-scoped counts and configuration. Benchmarks run in the local edition to preserve the free hosting quota.

See [acceptance checks](acceptance-checklist.md) for expected answers and permission checks.
