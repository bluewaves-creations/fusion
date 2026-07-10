---
name: fusion-intake
description: "The Fusion intake gate — everything that enters a bucket enters through it, losslessly. Classify what landed in inbox/ (new, updated, duplicate, conflicting), preserve the original in sources/ with its sha256 in the MANIFEST, convert to a faithful summary-first document (xlsx, csv, docx, pptx, pdf, images, .eml mail, markdown/text exports), propose type and aurora, sign the ledger, clear the inbox. Use when the user says 'process the inbox', 'intake', 'ingest', 'convert this file', or drops files into a Fusion bucket's inbox/. For placement, curation, or restructuring of what is already inside, use fusion-librarian; for deliverables out of the bucket, use fusion-analyst."
license: MIT
compatibility: "Requires the fusion CLI on PATH and uv. LibreOffice (soffice on PATH) required for docx/pptx/legacy office formats — fails fast when missing, never silently degrades. Script deps via PEP 723 (openpyxl, PyYAML, pymupdf)."
---

# fusion-intake — the gate

Nothing enters the library except through the gate. The gate preserves
originals forever, converts losslessly, and asks before it acts on anything
that isn't clean and new.

Read `references/fusion-conventions.md` once per session. Then, before
touching anything: read the bucket's `BUCKET.md` — `## Conventions` may
contain filing rules and standing delegations that bind this whole run.

## The pipeline

```
inbox/ ─► STAGE 1 gate (scripts/gate.py)      deterministic: hash, similarity
              │        four buckets → gate-<runid>.json
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
                      inbox file deleted ONLY when check is green
```

## Running it

Every command runs with the bucket root as `--bucket`; `<skill>` is this
skill's directory.

1. **Classify:** `uv run <skill>/scripts/gate.py --bucket <root>`
   → read the printed manifest path, then load `references/gate.md` and
   follow it to the intake report. Stop for confirmation where it says stop.
2. **Admit** each approved file:
   `uv run <skill>/scripts/convert.py admit --bucket <root> --file <name> --category <cat> --actor <you>`
   Category follows the bucket's filing rules (BUCKET.md), else a short
   plural noun (`reports`, `mails`, `gear`). The MANIFEST row is the
   script's job — never edit MANIFEST.md yourself.
3. **Prepare:**
   `uv run <skill>/scripts/convert.py prepare --bucket <root> --source <cat>/<name> [--dest …] [--type …] [--aurora …]`
   Extractive files (`done: true`) are already conformant documents.
   Everything else returns a work-dir manifest — load
   `references/convert.md` and reconstruct.
4. **Close** (per file): refine the document summary if it's the
   deterministic placeholder, then
   `uv run <skill>/scripts/convert.py link --bucket <root> --source <cat>/<name> --doc <zone-rel-doc>`
   `fusion log converted "sources/<cat>/<name> → <doc>" --as <you>`
   `fusion index` · `fusion check <root>` — green, then and only then
   delete the inbox file and `cleanup --run-dir <dir>`.

## The four classes (locked)

| Class | Meaning | Action |
|---|---|---|
| new | nothing matches | auto-proceed |
| duplicate (exact) | byte-identical to a source | auto-skip, recorded |
| duplicate (near) | re-export / trivial edit | ASK: skip / update / new |
| updated | newer version of an existing source | ASK, then supersede |
| conflicting | claims contradict the library | ASK — the gate never picks a winner |

**Supersede, the Fusion way:** `sources/` is immutable — a confirmed update
ADMITS THE NEW FILE as its own source (rename it first if the name
collides) and RECONCILES the existing library document in place: same
path, content updated, `updated:` bumped, `source:` repointed to the new
original. One document, no `-v2` twin. The old original stays in
`sources/` and the MANIFEST, superseded but never erased.

## The fidelity contract (lossless, non-negotiable)

- The original lands in `sources/` byte-identical, full sha256 in MANIFEST.
- Every page is accounted for (`page_count == len(pages)`); a page the
  text layer can't cover is flagged `needs_vision` and YOU read its image.
- Tables: every row, every column. Numbers verbatim — never rounded,
  never paraphrased. Figures get a one-line caption.
- Doubtful fidelity (blurry scan, unreadable region)? Flag it to the human
  and leave the file in inbox. A lossy conversion is a failed conversion.
- The inbox file is deleted only after MANIFEST link + ledger + green
  `fusion check`.

## Never

- Never modify, rename, or delete anything in `sources/`.
- Never hand-edit `MANIFEST.md`, `LEDGER.md`, or any `INDEX.md`.
- Never convert a near-dup, update, or conflict without a yes.
- Never leave a converted file's ledger entry unsigned.
