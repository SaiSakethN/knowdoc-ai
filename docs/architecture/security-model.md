# Security model

Browser input, source text and model output are untrusted. Source instructions cannot grant access or invoke tools: no tool execution capability is exposed to the generator. Provider URLs are local-host restricted unless an operator explicitly changes configuration. That flag is not blanket authorization to transmit private user data.

Passwords use Argon2id. Random session tokens are stored only as SHA-256 hashes with expiry and CSRF values. Authenticated mutations require the CSRF header; browser requests also require an allowed origin. Secure cookies are off for loopback HTTP development and enabled on the hosted HTTPS deployment. Cloud originals are private database records behind the same document permissions. Hosted inference is disabled in the card-free edition.

Ownership/grant SQL predicates filter both retrieval branches before text reaches reranking or generation. Original downloads, versions, citations, reindex and deletion authorize independently. Answers recheck access after inference. This is application enforcement, not implemented RLS. A shared runtime role can read application tables; a missed predicate or database compromise remains serious. Runtime role is non-superuser and cannot create roles/databases; migrations use a separate admin account.

Uploads use body/size limits, signature checks, generated paths, DOCX expansion/member limits and PDF page limits. HTML is rendered only as text; originals download as authorized attachments. OCR subprocesses have timeouts. The worker is not a hardened hostile-file sandbox, and native parser resource containment remains incomplete.

Rate limiting is per process/IP and not distributed. MFA, account recovery, SSO, formal penetration testing and certified tenant isolation are not implemented. Operator CLI scripts are trusted local tools, not public endpoints. Logs omit raw document/provider bodies by default.
