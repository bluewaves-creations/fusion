---
name: fusion-analyst
description: "The Fusion analyst — deliverables out of the bucket. Four gears: report (multi-section analysis from library + activities — the default), assess (scored assessment with explicit criteria and scale), compare (side-by-side matrix with deltas and red flags), export (CSV/JSON/XLSX data extracts). Everything lands in output/ as a summary-first document, cites every source path in data_sources, and ships signed in the ledger. Use for 'report on', 'analyze and write up', 'brief', 'assess', 'evaluate', 'score', 'compare X and Y', 'export as csv/excel'. For searching without producing a deliverable use fusion-librarian's query; for new documents of record use fusion-librarian's create."
license: MIT
compatibility: "Requires the fusion CLI on PATH; uv for the export script (PEP 723: openpyxl)."
---

# fusion-analyst — the output

Deliverables leave the bucket; their evidence never does. Every analyst
document cites the exact paths it was built from, and ships with a
`shipped` ledger entry.

Read `references/fusion-conventions.md` once per session; read
`BUCKET.md ## Conventions` before acting.

## Pick the gear

| Signal | Gear | Load |
|---|---|---|
| report / analyze / write up / brief (default) | report | references/report.md |
| assess / evaluate / score / rate | assess | references/assess.md |
| compare / versus / side by side | compare | references/compare.md |
| export / as csv / as excel / as json | export | references/export.md |

## The output contract (all four gears)

- Deliverables are documents in `output/` — frontmatter `title`, `type`,
  `aurora` (usually `library` for reference-grade output, `commitments`
  when it answers a promise), `created`, and **`data_sources`: the YAML
  list of every bucket path the deliverable was built from.** No
  uncited claims: if it isn't in a listed source, it is labelled as the
  analyst's own inference.
- Drafts live in `workbench/` while the human iterates; the finished
  piece moves to `output/` (that move is the librarian's promote gear if
  the human asks for the full ceremony, or written directly to `output/`
  when the ask was a deliverable from the start).
- Sign every deliverable:
  `fusion log shipped "output/<path>" --bucket <root> --as <you>` ·
  `fusion index <root>` · `fusion check <root>` green.

## Never

- Never invent data — the bucket is the evidence, `data_sources` is the
  warrant.
- Never overwrite an existing deliverable silently; new version, new
  name, or an explicit yes.
- Never hand-edit the registers.
