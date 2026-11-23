# Technical walkthrough

Trace api.py upload: validate owned collection and optional document, bound/check/hash source bytes, generate version-ID storage path, commit version/job, return 202. Interrupted filesystem/database work can leave orphans, making reconciliation part of the design.

Trace worker.py: claim with lease/fencing token, verify checksum, parse real page/section locations, chunk exact normalized substrings, embed in bounded batches and atomically switch active generation. A failed rebuild leaves previous results usable. Historical citation resolution intentionally does not require the old chunk to be active.

Trace retrieval.py: common authorized join feeds FTS and vector queries; model identity/dimensions filter vector compatibility. RRF avoids adding incomparable lexical/cosine scales. CPU reranking and diversity see authorized text only. Initial cosine search is exact and bounded.

Trace answers/providers: select evidence, use local inference with short aliases, map only known IDs and verify quotes against stored text. Invalid output abstains; a valid quote still may not entail every generated statement. Numeric-policy conflicts are a narrow detector, not general contradiction proof.

Follow a React source card through citation resolution and hash/access checks. Mid-generation revocation rejects the answer after inference. Read actual evaluation failures and strict relevance definitions before making portfolio quality claims.
