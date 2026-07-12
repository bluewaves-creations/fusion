# restructure — ownership means showing your reasons

The librarian's distinctive power: reorganizing the bucket when the
taxonomy stopped serving. Also the most destructive gear — so it runs as
propose → confirm → execute → sign.

1. **Propose.** Read the zone's INDEX + folder shape. Write the plan:
   every move (`old → new`), every folder created or retired, and the
   REASON in one paragraph. Check `BUCKET.md ### Rules` — a restructure
   that contradicts a Rule needs the Rule changed first (that is a
   reflect-gear conversation).
2. **Confirm.** The human says yes (or a Delegation explicitly covers
   it — rare for restructures; cite it).
3. **Execute.** Move files; update relative links in affected documents
   (grep for the old paths); keep filenames conformant. If a moved
   document is named by a MANIFEST `library` cell (it was converted from
   a source), repoint the cell with the intake writer — `MANIFEST.md` is
   single-writer, never hand-edited:
   `uv run <fusion-intake>/scripts/convert.py relink --bucket <root>
   --source <cat>/<file> --from <old-path> --to <new-path>`
   (one call per moved document per source row that names it).
4. **Sign.** One ledger entry for the operation:
   `fusion log restructured "<zone>/<scope>" --note "<the reason>"
   --bucket <root> --as <you>` — the note is not optional here. Then
   `fusion index <root>` and `fusion check <root>` (W4 watches the links
   you just moved).
