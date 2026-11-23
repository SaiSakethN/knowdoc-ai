# Security assessment

This assessment covers the local implementation and the limited hosted edition. It is not a penetration test or certification. [Trust boundaries](architecture/security-model.md) describe the design. The hosted app enables secure cookies, stores originals behind authenticated database reads and disables AI provider calls.

Implemented: hashed credentials/tokens, expiry, CSRF/origin checks, ownership/grants, SQL prefilters, post-inference access recheck, authorized source/citation routes, UUID filenames, body/format/expansion/page limits, unprivileged image, local-provider restriction and minimized logs.

Tests cover two-user isolation, original-download denial, grant/revoke, mid-generation revocation, spoofed uploads, DOCX expansion, fabricated citation rejection, injection text, remote-provider rejection and recovery. Mocked invalid-output tests are not evidence that a real model resists all attacks; actual model behavior is reported by the provisional benchmark.

Residual risks: no RLS or per-tenant DB role, incomplete parser sandboxing/resource containment, no distributed request rate limiter, no SSO/MFA/recovery, no complete transitive vulnerability/license audit, no formal accessibility audit, incomplete retention/backup enforcement and fallible semantic support/conflict detection. Local administrators can bypass application ACLs. The hosted release remains a limited free-tier demonstration without a production security certification.

Do not export raw prompts/documents through tracing or publish credentials, uploads, cookies or private browser traces. Generated responses and reports may include source text and must remain owner scoped.

Actual adversarial follow-up: 3/5 cases omitted forbidden generated strings; two copied attack instructions into generated claims, without observed private data exposure. After a narrow claim-content rejection was added, both focused failing cases abstained in real local-provider retests. Historical failures are retained in the evaluation report; this does not establish exhaustive injection resistance.
