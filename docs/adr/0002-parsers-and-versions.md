# ADR 0002: conservative parsing and immutable versions

Accepted under the pypdf proposal. Use pypdf, python-docx, Beautiful Soup and direct Markdown section handling. Preserve normalized substrings and real page/section metadata, avoiding invented DOCX pagination. Retain source versions and index generations so historical citations remain stable.

PyMuPDF was considered but not adopted because its licensing required a separate decision. pypdf trades some layout quality for the selected stack. Optional local OCR reports missing dependencies/failed scans and timeouts explicitly. Complex tables, scans and code-block splitting remain known fidelity limits.
