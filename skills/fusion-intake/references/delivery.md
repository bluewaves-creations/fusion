# Delivery intake — batch, for a package of many files

A single dropped file walks the pipeline in SKILL.md one step at a time.
A **delivery** — a container or folder holding dozens to hundreds of
files arriving together — walks the same pipeline, but its mechanical
halves (admit, link) run once each, as a single validated batch, instead
of one subprocess call per file. This is the protocol proven live on a
122-file `.athena` package: 122 sequential `admit` calls plus 122 `link`
calls became one `unpack`, one gate pass, one `batch` call for the admits
and links, with Stage 2 conversion (the operator's judgment) unchanged in
the middle.

## The full protocol

1. **Unpack.** `convert.py unpack --bucket <root> --file <container>` —
   the container is a vehicle, not an original (references/gate.md). It
   lands beside itself in `inbox/`, keeping folder context, and is
   discarded. Sign the act `noted`.
2. **Dedupe (hash sweep).** Before gating hundreds of files one at a
   time, sweep the unpacked tree for byte-identical duplicates
   (`sha256_of` on every member) — a delivery often repeats the same
   attachment across several notes. Keep one copy per distinct hash;
   report the rest as redundant and remove them from `inbox/`, signed
   `noted`, same as `inbox_dups` in `references/gate.md`.
3. **Gate.** `gate.py --bucket <root>` over what remains, then
   `references/gate.md` for Stage 2 classification. A delivery's files
   are usually all `new` — but run the topic match anyway; a delivery can
   still update or conflict with what's already in the library.
4. **Categories on basename collision.** A delivery's folder structure is
   real information: when two admitted files would collide on the same
   `(category, basename)` — the same filename nested under different
   package folders — file each occurrence under its own per-folder
   category (`records/2026-q1/report.pdf`,
   `records/2026-q2/report.pdf`) rather than renaming either file.
   `batch` enforces the collision check; it never picks a category for
   you.
5. **Convert (Stage 2, per file).** Unchanged — this is the operator's
   judgment, never batched. Notes in particular get **lifted summaries**:
   when a delivery's package manifest or index already carries a
   one-line description per note, lift it verbatim into the document's
   `## Summary` instead of re-deriving one from the body — it's the
   author's own framing, and it's usually better than a machine-written
   restatement.
6. **Batch links from the package manifest.** Once every document for
   this delivery is written, build ONE op-list from the package's own
   manifest (see schema below) and run `batch`. If the delivery's admits
   haven't happened yet either, put them in the same op-list — `batch`
   validates and runs both halves together.
7. **Close.** Per document, sign one ledger line: `fusion log converted
   "sources/<cat>/<file> → <doc>" --bucket <root> --as <you>`. A delivery
   of 122 files gets 122 `converted` lines — the ledger is a trail of
   individual acts, batching the mechanics never collapses that trail.
   Then `fusion index <root>` and `fusion check <root>`, green.
8. **Archive pass — only when the delivery's own intent says so.** A
   delivery that is itself an archival drop (its cover note, package
   manifest, or the human's instruction says these are records being
   retired, not active work) gets one archive pass at the end: move the
   closed documents to an `archive/` subfolder inside their zone and set
   `aurora: archive` on each, per `references/fusion-conventions.md`
   §Archive. Do not archive by default — most deliveries add active
   material, not retire it.

## `batch` — schema and semantics

```json
{"admits": [{"file": "<inbox-rel>", "category": "<cat>"}],
 "links":  [{"source": "<sources-rel>", "doc": "<zone-rel-doc>"}]}
```

`admits[].file` is a path relative to `inbox/`; `links[].source` is the
resulting `sources/`-relative path (`<category>/<basename>`);
`links[].doc` is zone-relative (`library/...`, `activities/...`, or
`output/...`) — the document Stage 2 already wrote.

```bash
uv run <skill>/scripts/convert.py batch --bucket <root> --ops <ops.json> --actor <you>
```

Prints `{"admitted": n, "linked": m}`.

**Validation before damage, at batch scale.** Two passes, never partial:

1. Every admit and every link is checked structurally BEFORE anything
   moves: admit files exist in `inbox/` with a supported extension,
   `(category, basename)` is unique both within the batch and against
   every row already in `sources/MANIFEST.md` (and against any file
   already sitting on disk in `sources/` even without a row), the actor
   is a single token, and each link's `doc` is zone-relative while its
   `source` either already has a MANIFEST row or is declared by this same
   batch's admits. One bad op anywhere aborts the whole call — nothing
   moves, nothing is appended, not even the good ops ahead of it in the
   list.
2. All admits then run (reusing `admit()` — still the only writer of
   `sources/MANIFEST.md`). This half does not roll back.
3. Before any link is written, every link's `doc` is checked to exist on
   disk NOW — the operator's Stage 2 conversion must already have
   produced it. If any doc is missing, the batch aborts naming it and NO
   link is written, not even the ones whose doc is fine: partial linking
   would leave some sources correctly cross-referenced and others
   silently `—`, indistinguishable from "not yet converted."
4. All links then run (reusing the same MANIFEST-writing path as the
   `link` subcommand).

Conversion itself (Stage 2 — reading the file, writing the document) is
never part of a batch: it's the one step in this pipeline that stays the
operator's judgment, file by file, exactly as `references/convert.md`
describes.
