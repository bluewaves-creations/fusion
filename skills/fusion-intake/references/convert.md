# Conversion — Stage 2 (reconstruction)

`prepare` returned `done: false` and a work-dir manifest. You are the
vision half of the engine: reconstruct the document faithfully, then close
the loop. All paths below are bucket-relative.

## Reconstruct

Read `manifest.json` (`run_dir`, `pages`, `images`, `front_matter_seed`,
`output_file`, `attachments`).

Walk `pages` in order:
- `needs_vision: false` → use the page's `text` verbatim. Do not
  paraphrase; do not "clean up" numbers.
- `needs_vision: true` → Read the corresponding `page-NNN.png` (or the
  staged image) and transcribe what you see: headings, paragraphs, FULL
  tables — every column, every row, no cap — and figures as a one-line
  caption (`*Figure: monthly deliveries trending up since March.*`).

Format-specific notes:
- **mail** (`path: mail`): the page text carries headers + body. Body
  becomes the document; headers land in the summary and frontmatter
  (`created:` from the Date header). Attachments were extracted into the
  work dir — tell the user, and offer to move them to `inbox/` so each
  goes through the gate itself.
- **text** (`path: text`): the content is already prose. Normalize it
  into the document body; if it carried frontmatter, preserve unknown
  keys (liberal reader) and merge the required three.
- **image**: transcribe or describe honestly — a photo gets a faithful
  description, a screenshot of text gets the text.

## Write the document

To `output_file`, exactly this shape:

```markdown
---
title: <refined from content — the seed title is just the filename>
type: <seed, or better from content>
aurora: <see the guidance below>
source: <seed verbatim>
created: <seed verbatim, or the mail Date>
---

## Summary

<2–3 lines a human reads in two seconds to decide whether to open the rest.
Write it from the content — never "converted from X.">

---

<the reconstructed body>
```

Aurora guidance — seven of the eight; `archive` is deliberately absent
(nothing enters a bucket already archived — archiving is the librarian's
act, moving path and aurora together per SPEC §9):
| Content | Aurora |
|---|---|
| Settled reference: manuals, records, data, mail worth keeping | `library` |
| Something to act on with a deadline or promise | `commitments` |
| Material for current deep work | `focus` |
| Recurring process, ops docs | `ops` |
| Shared work, other people's input | `collab` |
| Personal, non-work | `life` |
| Unvetted research, curiosity | `explore` |

When unsure between two: propose one, note the alternative in the intake
report. The bucket's own Rules (BUCKET.md) override this table.

## The fidelity checklist (run it before closing)

1. Document is non-empty and summary-first.
2. Every manifest page is represented in the body (count them).
3. Every table's row and column counts match the source page (spot-check
   against the image).
4. All three required frontmatter fields present; aurora is one of the
   eight; `source:` points at the admitted original.
5. Anything you could not read faithfully is flagged in your report to
   the human — and the inbox file stays put.

## Close the loop (per file, in this order)

```bash
uv run <skill>/scripts/convert.py link --bucket <root> --source <cat>/<file> --doc <output_file>
fusion log converted "sources/<cat>/<file> → <output_file>" --as <you>
fusion index
fusion check <root>
```

Green check → delete the inbox file, then
`uv run <skill>/scripts/convert.py cleanup --run-dir <run_dir>`.
Extractive files (`done: true`) skip reconstruction but get the same
close: refine their placeholder summary and title from the tables first
(Edit the document — that is a content change, so bump nothing else),
then link → log → index → check.
