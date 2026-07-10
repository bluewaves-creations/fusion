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
| 5 | 2026-07-10 | bluewaves | intake | gate times out on large batches — similarity shingles multi-MB binaries against every source (O(n×m) with full-file decoding); 128-file delivery ran >2min | grind | **fixed** — SIMILARITY_READ_CAP + binary skip + shingle cache (6af4ce9); live: same bucket 0.35s vs >2min |
| 6 | 2026-07-10 | bluewaves | intake | nested container unpacked to inbox ROOT instead of beside its parent — dest is always inbox/<stem>, losing the folder context | paper cut | **fixed** — dest beside parent (eec8a67) + traversal containment at the root (8851fd3, 3e83d89) |
| 7 | 2026-07-10 | bluewaves | intake+librarian | delivery-manifest batch intake (122 admits/links) and broken-link repair (67 rewrites) both ran as hand-written operator scripts — the patterns are proven but not yet Fusion capabilities | grind | **fixed** — `convert.py batch` + references/delivery.md (b00b292); librarian link-repair scan/apply + sweep protocol (bcabdde, 62dbfae). Known limitation: code-span links scanned like prose — placeholder basenames rely on having no real candidate |
| 8 | 2026-07-10 | all | reflection | the checker and the librarian scanner read links inside code fences/spans as real links — 3 of bluewaves' 7 W4s were template placeholders in fenced examples | paper cut | **fixed** — code-blind link scan in both twins (f27d89c, dd8a785) + N-backtick spans (3a9a447); live: bluewaves 7→4 W4, all four honest. Known limits recorded: 4-space indented blocks still scanned; fence-closer indentation looser than CommonMark |
