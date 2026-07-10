# Frictions — the dogfood log

Recorded the moment they happen; triaged at week's end. Severity: **blocker**
(stopped the work) · **grind** (works, but fights you) · **paper cut**
(noticed, moved on).

| # | date | bucket | during | friction | severity | disposition |
|---|---|---|---|---|---|---|
| 1 | 2026-07-10 | bluewaves | intake | `.html` is not a supported gate format — three real files (site-page exports) held in inbox on day one; the LibreOffice route could carry them | grind | **fixed** — html/htm joined LIBREOFFICE_EXTS (758f981 + slug fix 21c6b2d); verified live: both held files converted, inbox cleared |
| 2 | 2026-07-10 | bluewaves | intake | the gate detects duplicates only against sources/, not within the inbox — two byte-identical html files landed and only operator eyes caught it | paper cut | **fixed** — gate reports `inbox_dups` per batch (758f981); the twin was deleted and signed (`noted`, 2026-07-10) |
| 3 | 2026-07-10 | bluewaves | intake | sparse-text slides (<100 chars/page) flag needs_vision even with a complete text layer — 26 of 33 deck pages read visually; correct per the coverage invariant, but heavy | paper cut | **accepted** — the human's call (2026-07-10): the price of lossless processing |
| 4 | 2026-07-10 | bluewaves | intake | containers: a 144MB `.athena` delivery (zip: manifest.json + 11 groomed notes + 52 assets) has no route — the gate refuses what is really a vehicle full of Fusion-shaped content | grind | **decided** — unpack-as-delivery (human, 2026-07-10): container route scaffolded; members are the originals; archive-after-intake for past engagements |
| 5 | 2026-07-10 | bluewaves | intake | gate times out on large batches — similarity shingles multi-MB binaries against every source (O(n×m) with full-file decoding); 128-file delivery ran >2min | grind | open — plan: docs/plans/2026-07-10-dogfood-capabilities.md |
| 6 | 2026-07-10 | bluewaves | intake | nested container unpacked to inbox ROOT instead of beside its parent — dest is always inbox/<stem>, losing the folder context | paper cut | open — same plan |
| 7 | 2026-07-10 | bluewaves | intake+librarian | delivery-manifest batch intake (122 admits/links) and broken-link repair (67 rewrites) both ran as hand-written operator scripts — the patterns are proven but not yet Fusion capabilities | grind | open — same plan |
