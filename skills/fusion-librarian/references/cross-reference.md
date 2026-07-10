# cross-reference — map what relates to what

Read-only. For a target document or topic:

1. Extract its entities (names, projects, products, periods).
2. Sweep the bucket: direct mentions (grep), shared frontmatter values
   (type, tags, aurora), thematic kinship (summaries that talk about the
   same thing).
3. Report three buckets, every line carrying a path:
   **Direct references** · **Shared attributes** · **Thematic connections**.
4. Offer (don't apply) link edits: "these two documents should point at
   each other" — applying them is a content change the user approves.
   On a yes: edit, then sign the write —
   `fusion log noted "<path> — cross-linked to <other>" --bucket <root>
   --as <you>` — then `fusion index <root>`, `fusion check <root>`.

## Repair sweep — broken links, scan proposes, you approve, apply signs off

`scripts/link-repair.py` productizes the pattern above for the mechanical
case: a link that used to resolve and no longer does (a document moved, a
source got re-filed). It never guesses between candidates — the human
gate stays in the middle.

1. `uv run <skill>/scripts/link-repair.py scan --bucket <root> >
   proposals.json` — walks `library/` and `activities/`, tests every
   relative link from the doc's own directory, and for each broken one
   searches `sources/` and the doc zones by basename. JSON goes to
   stdout, a human-readable table to stderr: **EXACT** (unique basename
   match — safe to apply as-is), **FUZZY** (unique only after
   lowercase/hyphen-insensitive normalization — confirm per group, never
   silently folded in with the exact ones), **UNREPAIRABLE** (zero or
   two-or-more candidates — never guessed, hand-fix or leave it).
2. Show the human the table. Exact and fuzzy are always separated; a
   fuzzy group is applied only on an explicit yes.
3. Edit `proposals.json` down to the approved subset (delete the
   proposals nobody confirmed; `unrepairable` entries are informational,
   never fed to apply).
4. `uv run <skill>/scripts/link-repair.py apply --bucket <root>
   --proposals proposals.json` — rewrites only the approved pairs,
   bumps (or adds) `updated:` on the documents it touched, prints the
   count. It writes no ledger entry.
5. Sign the pass yourself: `fusion log noted "link-repair sweep — <N>
   links repaired (<E> exact, <F> fuzzy)" --bucket <root> --as <you>` —
   then `fusion index <root>`, `fusion check <root>` green before you
   report done.
