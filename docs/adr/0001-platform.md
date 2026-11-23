# ADR 0001: local modular platform

Accepted after user approval of the planning proposal. Use Python 3.12/FastAPI, PostgreSQL pgvector/FTS, leased database jobs and React/Vite. A shared durability boundary reduces infrastructure on a 16 GB laptop. SQLite would reduce setup but lose backend parity; a separate vector database or Redis queue adds consistency/permission boundaries without measured need. Initial vector ordering is exact; no ANN-scale claim is made.

Tradeoff: explicit SQL permission enforcement needs careful coverage and the shared database is a single point of failure. RLS is a future defense, not an implemented guarantee. Revisit infrastructure against measured workload rather than portfolio complexity.
