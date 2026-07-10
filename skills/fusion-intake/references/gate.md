# The intake gate — Stage 2 (judgment)

Stage 1 (`scripts/gate.py`) wrote `workbench/.intake/gate-<runid>.json`
with five buckets: `exact_dups`, `near_dups`, `update_candidates`,
`clean_new`, `containers`. This stage assigns each file's final class and
writes the intake report. It writes NOTHING to `sources/` or `library/` —
admission and conversion happen only after this stage's confirmations.

## Topic matching (do this before classifying)

For every `clean_new` and `update_candidates` entry:

1. Read `library/INDEX.md` (and `activities/INDEX.md` if the content looks
   like live work) — titles + summary lines are your map.
2. Grep `library/` for the incoming file's key entities (names, products,
   periods, metrics).
3. Read the 1–3 most-related documents' summaries; open bodies only when
   claims must be compared.

## Per-bucket protocol

**`exact_dups` → duplicate (exact).** Record in the report with the
matched source. Do not convert, do not prompt — an exact re-drop carries
no new information.

**`inbox_dups` → the same bytes dropped twice in one batch.** The first
copy proceeds under its own class; the rest are redundant — report them,
and clean them out of `inbox/` (delete, signed with a `noted` ledger
line) per the standing rule of 2026-07-10; a bucket's BUCKET.md
Conventions may override.

**`clean_new` → new.** Run the topic match. No overlap → class `new`,
auto-proceed; the gate adds zero friction to genuinely new content.
Topic overlap without contradiction → still `new`, but note
"extends <doc>" in the report. Contradiction → reclassify `conflicting`.

**`update_candidates` → updated (confirm) — the identity guard.**
Read the incoming content and the matched source. Same logical identity
(a newer version of the SAME document), one candidate, unambiguous →
class `updated`. Similar-but-not-clearly-same, or multiple candidates →
ASK the user to confirm identity. Never guess a supersede. On `updated`,
the report states exactly what a confirmed update will do:
- admit the new file to `sources/` (renamed if the name collides — the
  old original is immutable and stays);
- reconcile the existing library document IN PLACE: same path, content
  re-converted, `updated:` bumped, `source:` repointed;
- MANIFEST: new row for the new original, its `library` column pointing
  at the reconciled document.

**Contradiction detection → conflicting (confirm + resolve).** For
update candidates and topic-overlapping new files, compare claims:
figures (same metric, different value), dates (same event, different
date), conclusions (approved vs rejected). Do NOT flag: facts the
library is silent on, cosmetic rewording, or a clearly new reporting
period. On a real conflict, record the claim, both values, both sources —
and stop. Nothing converts until the human resolves it: accept as
correction (reconcile), reject (skip), or keep both with a note.

**`near_dups` → duplicate (near) (confirm).** Probably a re-export or
trivial edit. Never auto-skip, never auto-convert: offer skip / treat as
update / convert as new.

**`containers` → vehicles, not originals.** Report each one (name, size).
Containers (`.zip`, `.athena`) never enter `sources/` intact — `unpack`
them beside the container (`inbox/<stem>/` for top-level drops, or a
nested container's own sub-folder if it lives deeper, keeping that
context) on the standing rule (or ask first if the container is
unexpected or its size is surprising), delete the container, sign the
act `noted`, then gate the extracted contents like any other inbox drop.

## The intake report (the prompt surface)

Present one report for the whole run — a table, then a detail block per
non-`new` row:

```markdown
## Intake report — <date>

| Incoming | Class | Matches | Action |
|---|---|---|---|
| acme-audit.pdf | new | — | converting |
| q1-report.xlsx | updated | sources/reports/q1-report.xlsx | supersede + reconcile (confirm) |
| brochure.pdf | duplicate | sources/marketing/brochure.pdf | auto-skipped (exact) |
| q1-financials.xlsx | conflicting | library/finance/q1.md | hold — revenue 5.0M vs 4.2M |
```

Detail blocks name the evidence: similarity score, normalized-name match,
git history lines, the exact conflicting claims. The report is the
question — ask it, then act only on the answers.

## After confirmation

Proceed per SKILL.md steps 2–4 for approved files only. For an `updated`
file, `prepare` targets the existing document (`--dest`/`--slug` set to
its current path pieces) and the reconciliation edits that document in
place. Delete gate run files (`workbench/.intake/gate-*.json`) at the end
of the run.
