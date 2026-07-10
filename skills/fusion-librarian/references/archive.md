# archive — out of the way, never out of reach

Path is the truth, aurora is the signal — both, always, in one move.

1. Confirm the target and the authority: explicit ask, or a standing
   delegation in BUCKET.md `### Delegations` that covers this case
   (cite it in the note when you use it).
2. Move the document to `<its-zone>/archive/<same-folder-structure>/`.
3. Repair what pointed at it: run `uv run <skill>/scripts/link-repair.py
   scan --bucket <root>` and apply exact-confidence repairs per the
   sweep protocol in [cross-reference.md](cross-reference.md) (or a
   standing delegation); fuzzy always asks.
4. Edit its frontmatter: `aurora: archive`.
5. `fusion log archived "<zone>/<old> → <zone>/archive/<new>"
   [--note "delegation: <rule>"] --bucket <root> --as <you>` ·
   `fusion index <root>` · `fusion check <root>` — the checker's W3
   watches exactly this agreement.

Activities are the planner's: closing or archiving one is
fusion-planner's close gear (it also writes the final Log line in
plan.md). This gear archives library/ and output/ documents.
