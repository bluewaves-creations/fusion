---
name: fusion-intake
description: "The Fusion intake gate — everything that enters a bucket enters through it, losslessly. Classify what landed in inbox/ (new, updated, duplicate, conflicting), preserve the original in sources/ with its sha256 in the MANIFEST, convert to a faithful summary-first document (xlsx, csv, docx, pptx, pdf, html, images, tiff→png, .eml mail, markdown/text exports), propose type and aurora, sign the ledger, clear the inbox. Use when the user says 'process the inbox', 'intake', 'ingest', 'convert this file', or drops files into a Fusion bucket's inbox/. For placement, curation, or restructuring of what is already inside, use fusion-librarian; for deliverables out of the bucket, use fusion-analyst. Applies only inside a Fusion bucket — a directory tree with BUCKET.md and LEDGER.md at its root; if there is no such bucket in play, offer to create one with `fusion new` instead of improvising structure."
license: MIT
compatibility: "Requires the fusion CLI on PATH and uv. LibreOffice (soffice on PATH) required for docx/pptx/legacy office/html formats — fails fast when missing, never silently degrades. Script deps via PEP 723 (openpyxl, PyYAML, pymupdf, pillow)."
---

# fusion-intake — the gate

Nothing enters the library except through the gate. The gate preserves
originals forever, converts losslessly, and asks before it acts on anything
that isn't clean and new.

Read `references/fusion-conventions.md` once per session. Then, before
touching anything: read the bucket's `BUCKET.md` — `## Conventions` may
contain filing rules and standing delegations that bind this whole run.
No `BUCKET.md` up the tree and none named? Then nothing here is a
Fusion bucket and no Fusion skill applies — but offer the door instead
of walking away: `fusion new <path>` scaffolds a conformant bucket and
registers it in the hub (`fusion hub` lists the ones that exist).
Buckets are life-domains — few and bold — never improvised by hand.

## The pipeline

```
inbox/ ─► STAGE 1 gate (scripts/gate.py)      deterministic: hash, similarity
              │        six buckets → gate-<runid>.json
              ▼
          STAGE 2 gate (references/gate.md)   judgment: final class + intake report
              │        new → auto-proceed · exact dup → auto-skip
              │        near-dup / updated / conflicting → ASK FIRST
              ▼
          ADMIT + CONVERT (scripts/convert.py) original → sources/ + MANIFEST row
              │        xlsx/csv finish here; everything else stages pages
              ▼
          STAGE 2 convert (references/convert.md)  vision reconstruction,
              │        fidelity checklist, summary, type + aurora
              ▼
          CLOSE       link MANIFEST → fusion log → fusion index → fusion check
                      admit already moved the original into sources/ —
                      close just needs the register trail green
```

## Running it

`admit`, `prepare`, `link`, `unpack`, and `gate.py` take the bucket root as
`--bucket`; `cleanup` takes only `--run-dir` — resolve it against the
bucket root before calling (the manifest's `run_dir` is bucket-relative).
`<skill>` is this skill's directory.

A delivery — a container or folder holding dozens to hundreds of files
arriving together — walks this same pipeline, but its mechanical halves
(admit, link) run once each as a single validated batch instead of one
call per file: `convert.py batch --bucket <root> --ops <ops.json>`. Read
`references/delivery.md` for the full protocol (dedupe, per-folder
categories on basename collision, batch schema) before working a
delivery.

Containers (`.zip`, `.athena`) are delivery vehicles, not originals:
`uv run <skill>/scripts/convert.py unpack --bucket <root> --file <name>`
extracts one beside the container (`inbox/<stem>/` for top-level drops)
and deletes the container — the members become the originals, signed
`noted` in the ledger — then gate the contents normally (step 1).

1. **Classify:** `uv run <skill>/scripts/gate.py --bucket <root>`
   → read the printed manifest path, then load `references/gate.md` and
   follow it to the intake report. Stop for confirmation where it says stop.
2. **Admit** each approved file:
   `uv run <skill>/scripts/convert.py admit --bucket <root> --file <name> --category <cat> --actor <you>`
   Category follows the bucket's filing rules (BUCKET.md), else a short
   plural noun (`reports`, `mails`, `gear`). The MANIFEST row is the
   script's job — never edit MANIFEST.md yourself.
   `.tif`/`.tiff` is converted to PNG right here, deterministically — the
   PNG is admitted as the original (its own sha256 in the MANIFEST row);
   the tiff bytes are not retained (2026-07-12 ruling: no need for large
   tiff files). A single-frame tiff converts cleanly; a multi-frame tiff
   is refused outright (conservative — never a silent first-frame-wins).
   The JSON result carries a `note` field when this happened — sign it
   immediately, same run: `fusion log noted "<note>" --bucket <root> --as
   <you>`.
3. **Prepare:**
   `uv run <skill>/scripts/convert.py prepare --bucket <root> --source <cat>/<name> [--dest …] [--slug …] [--type …] [--aurora …] [--reconcile]`
   Extractive files (`done: true`) are already conformant documents.
   Everything else returns a work-dir manifest — load
   `references/convert.md` and reconstruct. `--reconcile` (with the
   existing doc's `--dest`/`--slug`) is the confirmed-update path —
   prepare refuses an existing destination without it.
4. **Close** (per file): refine the document summary if it's the
   deterministic placeholder, then — admit already moved the original into
   `sources/`, so closing is just the register trail:
   `uv run <skill>/scripts/convert.py link --bucket <root> --source <cat>/<name> --doc <zone-rel-doc>`
   `fusion log converted "sources/<cat>/<name> → <doc>" --bucket <root> --as <you>`
   `fusion index <root>` · `fusion check <root>` — green, then
   `cleanup --run-dir <dir>`. Nothing remains in inbox for this file.

## The four classes (locked)

| Class | Meaning | Action |
|---|---|---|
| new | nothing matches | auto-proceed |
| duplicate — exact | byte-identical to a source | auto-skip, recorded |
| duplicate — near | re-export / trivial edit | ASK: skip / update / new |
| updated | newer version of an existing source | ASK, then supersede |
| conflicting | claims contradict the library | ASK — the gate never picks a winner |

Four classes — `duplicate` splits into exact (auto-skip) and near (ask).

The four classes cover matches against `sources/`; the same bytes dropped
twice within one inbox batch are reported separately as `inbox_dups` and
cleaned per the bucket's rules (`references/gate.md`).

**Supersede, the Fusion way:** `sources/` is immutable — a confirmed update
ADMITS THE NEW FILE as its own source (rename it first if the name
collides) and RECONCILES the existing library document in place
(`prepare --reconcile`): same path, content updated, `updated:` bumped,
`source:` repointed to the new original. One document, no `-v2` twin.
The old original stays in `sources/` and the MANIFEST, superseded but
never erased.

## The fidelity contract (lossless, non-negotiable)

- The original lands in `sources/` byte-identical, full sha256 in MANIFEST.
  Exception, human-ruled (2026-07-12): `.tif`/`.tiff` is converted to PNG
  at admit — lossless on pixels, not on bytes, and the human explicitly
  waived tiff-byte preservation to avoid needlessly large files. The PNG
  becomes the original; the source tiff's name + sha256 are carried in
  the admit `note` so the transformation stays honest in the ledger.
- Every page is accounted for (`page_count == len(pages)`); a page the
  text layer can't cover is flagged `needs_vision` and YOU read its image.
- Tables: every row, every column. Numbers verbatim — never rounded,
  never paraphrased. Figures get a one-line caption.
- Doubtful fidelity (blurry scan, unreadable region)? If caught BEFORE
  admit, the file simply stays in inbox. If caught AFTER admit, the
  original is already safe in `sources/` — withhold the document instead
  (or flag the gap loudly inside it) and leave the MANIFEST row unlinked
  (`—`) until the human decides. A lossy conversion is a failed conversion.
- Close only after MANIFEST link + ledger + green `fusion check`.

## Never

- Never modify, rename, or delete anything in `sources/`.
- Never hand-edit `MANIFEST.md`, `LEDGER.md`, or any `INDEX.md`.
- Never convert a near-dup, update, or conflict without a yes.
- Never leave a converted file's ledger entry unsigned.
