# Data source assessment

Research date: 2026-11-21. The user subsequently approved this scope. All 24 pages were captured from official release documentation archives; exact hashes/notices are recorded in configs/source-manifest.json. The analysis below preserves the original research basis and remaining date/freshness limits.

## Recommended bounded corpus

Use official PostgreSQL 19.0 and 18.7 documentation on indexing, full-text search and concurrency. Start with these HTML paths under both `/docs/19/` and `/docs/18/`: `indexes.html`, `indexes-types.html`, `indexes-multicolumn.html`, `indexes-expressional.html`, `indexes-partial.html`, `textsearch.html`, `textsearch-intro.html`, `textsearch-tables.html`, `textsearch-indexes.html`, `mvcc.html`, `transaction-iso.html`, `explicit-locking.html`. This is a proposed 24-page allowlist; validate every path and title before ingestion and stop on redirects outside the approved version prefix.

The official pages identify [19.0](https://www.postgresql.org/docs/19/) and [18.7](https://www.postgresql.org/docs/18/). The [documentation index](https://www.postgresql.org/docs/) identifies 19 as current at research time. These mutable URLs are not immutable release snapshots. Prefer the corresponding exact release archives in the [official source directory](https://www.postgresql.org/ftp/source/) for reproducible provenance; verify archive checksums and inspect bundled documentation before choosing the extraction method. If generated HTML is absent, use bounded versioned HTML capture and record the capture as a snapshot, not an exact immutable release artifact.

Publisher: PostgreSQL Global Development Group. Format: HTML for demonstration; original fixtures cover other parsers. Per-page publication/update dates are not established. Retrieval date is a separate field. No assertion that all selected passages differ between releases: discover and annotate actual differences before writing version-change benchmark cases.

The [PostgreSQL License](https://www.postgresql.org/about/licence/) explicitly includes documentation and permits copying and distribution subject to retention of required notices. Proposed storage/indexing and a small attributed repository subset are consistent with that permission; retain the complete applicable notice and track any separately licensed assets. Do not redistribute logos or unrelated assets by assumption.

[Robots policy](https://www.postgresql.org/robots.txt) was inspected: versioned `/docs/18/` and `/docs/19/` are not disallowed for `User-agent: *`; `/docs/devel/` is disallowed. This is access guidance, not a license. Recheck before fetching. No login was required for inspected public pages. Proposed fetch policy: serial requests, at most one/second, bounded retries with backoff, conditional requests, explicit user agent, no search/account/devel crawling. Prefer archives to repeated crawling.

## Alternatives

| Candidate | Evidence and reuse status | Decision |
|---|---|---|
| Python | [Official license](https://docs.python.org/3.12/license.html) covers documentation; examples have specific dual licensing provisions | Strong alternative: a narrow standard-library subset across two pinned releases; preserve full license stack |
| PyTorch | [Official docs](https://docs.pytorch.org/docs/stable/index.html) redirect to a release path; [repository license](https://github.com/pytorch/pytorch/blob/main/LICENSE) inspected | Defer: documentation asset exceptions and release-specific source provenance still need audit |
| Docker | Official legal/contribution URLs could not be fetched successfully during this research | Defer: exact docs license, robots policy, archive and redistribution terms unverified; no ingestion approved |

Only the recommended PostgreSQL candidate has an initial access-policy and explicit documentation-reuse assessment. Other candidates need equivalent checks if selected.

## Manifest contract

Each source record must hold publisher, canonical URL, fetched URL, version label, release archive/tag if applicable, retrieved_at UTC, publication_date nullable, date_evidence, format, SHA-256 of raw bytes, size, license URL, local notice path, access-policy check date, redistribution decision, and extraction tool/version. Store immutable raw snapshots outside Git by default. Link logical document → immutable version → parsed sections → chunks. Hashes establish captured-byte integrity, not publisher authenticity; use HTTPS and published archive verification where available.

Approval requested: the 24-page PostgreSQL 18/19 allowlist, archive-first provenance strategy, and a small attributed subset only after final file-level checks. Alternative: Python standard-library documentation. No external service fees proposed; download/storage and license-notice maintenance are the main costs.
