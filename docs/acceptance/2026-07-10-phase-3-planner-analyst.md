# Phase 3 acceptance — fusion-planner + fusion-analyst on a scratch bucket

ROADMAP gate: fusion-planner (Task 8) and fusion-analyst (Task 9) exercised
end-to-end, agent-in-the-loop, on a single live scratch bucket — following
`skills/fusion-planner/SKILL.md` + its `references/`, and
`skills/fusion-analyst/SKILL.md` + its `references/` (including the export
gear's `scripts/export.py`), verbatim. No shortcuts, no reading ahead into
gears not routed to.

Sandbox, before any `fusion new`/`fusion hub` call:

```bash
export FUSION_HUB=/tmp/fusion-accept/hub.md FUSION_ACTOR=claude
mkdir -p /tmp/fusion-accept
cd <fusion repo root>
uv run --project cli fusion new /tmp/fusion-accept/horizon-demo --kind personal \
    --description "Planner/analyst acceptance bucket."
```

`fusion new` scaffolded the bucket, registered it in `/tmp/fusion-accept/hub.md`,
and `git init`'d + committed it, same as the librarian run — unprompted,
harmless, out of scope here.

## Setup — seed two conformant library documents by hand

Neither skill under test has a "create a document" gear (that's the
librarian's job), so per the brief the analyst needs evidence to work with
before Step 3. Authored two documents directly, each already conformant
(`title`, `type`, `aurora: library`, summary-first body), then signed,
indexed, checked — same three-beat discipline the family uses everywhere:

- `library/gear/jazzmaster.md` — Fender Jazzmaster, serial, purchase
  history, pickup measurements, an open bridge-upgrade issue.
- `library/gear/pedalboard.md` — five-pedal touring board, signal chain,
  power supply.

```
fusion log created "library/gear/jazzmaster.md" --bucket .../horizon-demo --as claude
fusion log created "library/gear/pedalboard.md" --bucket .../horizon-demo --as claude
fusion index .../horizon-demo --as claude
→ library/ — 2 documents — regenerated
fusion check .../horizon-demo
→ horizon-demo: 0 errors · 0 warnings — clean, carry on.
```

---

## Step 1 — create-activity (gear: **create-activity**, fusion-planner)

"Prepare the LP listening session, due 2026-07-24, it's a promise" —
textbook create-activity case (references/create-activity.md). Essentials
already stated: name, deadline, and "it's a promise" names the aurora
directly — **`aurora: commitments`** (promised-with-deadline), no other
candidate fits.

Created `activities/lp-listening/plan.md`:

```yaml
title: Prepare the LP listening session
type: plan
aurora: commitments
status: active
created: 2026-07-10
due: 2026-07-24
```

Summary-first body, `## Steps` with three concrete first actions (bounce
mixes, prepare track-order candidates, book the room), `## Log` with a
`created` line.

```
fusion log created "activities/lp-listening/plan.md" --bucket .../horizon-demo --as claude
fusion index .../horizon-demo --as claude
→ activities/ — 1 documents — regenerated
fusion check .../horizon-demo
→ horizon-demo: 0 errors · 0 warnings — clean, carry on.
```

**`fusion today`:**
```
Today across 1 bucket
  commitments:
    · [horizon-demo] Prepare the LP listening session — activities/lp-listening/plan.md (active)
```

**`fusion agenda`:**
```
dated:
    2026-07-24 · [horizon-demo] Prepare the LP listening session — activities/lp-listening/plan.md
```

Confirmed: shows under `commitments` in today, dated correctly in agenda.

Ledger tail:
```
- 11:46 · claude · created · activities/lp-listening/plan.md
- 11:46 · claude · indexed · activities/ (1 document)
```

---

## Step 2 — second activity + horizon (gear: **horizon**, fusion-planner)

**Second activity.** Created `activities/pedalboard-refresh/plan.md`,
`type: plan`, `aurora: focus` (the current deep-work tinkering, not a
promise), `status: active`, no `due:` — no deadline was stated or implied,
and create-activity's "Never set `due:` the human didn't state" applies
directly.

```
fusion log created "activities/pedalboard-refresh/plan.md" --bucket .../horizon-demo --as claude
fusion index .../horizon-demo --as claude
→ activities/ — 2 documents — regenerated
fusion check .../horizon-demo
→ horizon-demo: 0 errors · 0 warnings — clean, carry on.
```

**Horizon review** (references/horizon.md, steps 1–3): ran `fusion agenda`,
`fusion today`, `fusion status --since last-reflection`.

```
fusion agenda
→ dated:
      2026-07-24 · [horizon-demo] Prepare the LP listening session — activities/lp-listening/plan.md
  active, undated:
      · [horizon-demo] Pedalboard refresh — activities/pedalboard-refresh/plan.md (active)

fusion today
→ commitments:
      · [horizon-demo] Prepare the LP listening session — activities/lp-listening/plan.md (active)
  focus:
      · [horizon-demo] Pedalboard refresh — activities/pedalboard-refresh/plan.md (active)
```

**Horizon report, played as the four short lists** (horizon.md step 3):

> - **Moving:** both activities — each has its own `created` ledger entry
>   this minute; nothing has had time to go stale.
> - **Stalled:** none — the bucket is minutes old, no activity has gone
>   untouched.
> - **Expiring:** `lp-listening` — real `due: 2026-07-24`, 14 days out.
>   Not flagged as urgent (14 days is not "within a week"); named because
>   it's the only dated item.
> - **Done-in-fact:** none.
>
> One dated (`lp-listening`, commitments, due 2026-07-24), one
> undated-active (`pedalboard-refresh`, focus). No invented urgency —
> `pedalboard-refresh` has no due date and none is claimed for it; nothing
> is called stalled on a fresh bucket.

**Dormant flip.** Per the brief, played a status change on the `focus`
activity: the human says the band wants studio time freed up for the LP
listening prep first, and pedalboard work should pause until after
2026-07-24. Per horizon.md step 4 ("propose the honest corrections... on
yes: edit the frontmatter, log `noted`"): what would be asked — *"Put
`pedalboard-refresh` on hold (status: dormant) until after the listening
session?"* Played the stated outcome: yes.

Edited `activities/pedalboard-refresh/plan.md`: `status: active` →
`status: dormant`, added a `## Log` line naming the reason.

```
fusion log noted "activities/pedalboard-refresh — status: active → dormant" --bucket .../horizon-demo --as claude
fusion index .../horizon-demo --as claude
→ activities/ — 2 documents — unchanged
fusion check .../horizon-demo
→ horizon-demo: 0 errors · 0 warnings — clean, carry on.
```

**`fusion today` after the flip:**
```
Today across 1 bucket
  commitments:
    · [horizon-demo] Prepare the LP listening session — activities/lp-listening/plan.md (active)
```

`pedalboard-refresh` is gone from today — confirmed. **`fusion agenda`**
also drops it from "active, undated", leaving only the dated commitment.

---

## Step 3 — analyst report (gear: **report**, fusion-analyst)

"Report on what's in the library" — default gear, no audience specified so
full report, not a brief (references/report.md). Gather: triaged
`library/INDEX.md` (2 entries), read both documents in full — that's the
entire evidence set, so `data_sources` is exactly those two paths.

Wrote `output/reports/library-inventory.md`: `## Summary` (2-3 line
triage), `---`, Key findings (numbers verbatim: serial JM62-0451, EUR
1,850, 6.4k/7.1k ohm pickups; 5-pedal chain, Voodoo Lab PSU), Analysis,
Recommendations, `## Sources` table mirroring `data_sources`.

```yaml
data_sources:
  - library/gear/jazzmaster.md
  - library/gear/pedalboard.md
```

```
fusion log shipped "output/reports/library-inventory.md" --bucket .../horizon-demo --as claude
fusion index .../horizon-demo --as claude
→ library/ — 2 documents — unchanged / activities/ — 2 documents — unchanged
fusion check .../horizon-demo --json
→ {"bucket": "horizon-demo", "ok": true, "errors": [], "warnings": []}
```

Clean. `data_sources` lists the two seeded documents, `## Sources` table
present, `shipped` logged.

---

## Step 4 — assess (gear: **assess**, fusion-analyst)

Subject: the two library items. Criteria: **documentation completeness**
and **session readiness** (no scale given by the human, so the default
applies — stated explicitly at the top of the document, per
references/assess.md step 1).

Wrote `output/assessments/gear-readiness.md` — summary stating the default
1–5 scale up front, scores table (item · criterion · criterion · evidence
path), per-criterion rationale citing the specific facts each score is
based on (e.g. Jazzmaster session-readiness scored 3/5 because the
document itself names the string-skip bridge issue as unresolved), `##
Sources`.

```
fusion log shipped "output/assessments/gear-readiness.md" --bucket .../horizon-demo --as claude
fusion index .../horizon-demo --as claude
fusion check .../horizon-demo --json
→ {"bucket": "horizon-demo", "ok": true, "errors": [], "warnings": []}
```

Clean.

---

## Step 5 — export (gear: **export**, fusion-analyst) — the deliberate finding

Scope: `title` + `type` for both library documents, as csv
(references/export.md). Built the JSON payload and piped through the
skill's own script, unmodified:

```
echo '{"headers": ["title", "type"], "rows": [["Fender Jazzmaster (1962 reissue)", "guitar"], ["Main pedalboard", "gear"]]}' \
  | uv run skills/fusion-analyst/scripts/export.py --format csv \
    --output output/exports/library-title-type.csv
→ {"written": ".../output/exports/library-title-type.csv", "rows": 2, "format": "csv"}
```

Wrote the companion document `output/exports/library-title-type.md`:
`resource: output/exports/library-title-type.csv`, `data_sources` listing
both source paths, summary of what the csv contains.

```
fusion log shipped "output/exports/library-title-type.csv" --bucket .../horizon-demo --as claude
fusion index .../horizon-demo --as claude
fusion check .../horizon-demo --json
→ {
    "bucket": "horizon-demo",
    "ok": false,
    "errors": [
      {
        "level": "error",
        "code": "E8",
        "path": "output/exports/library-title-type.csv",
        "message": "filename must be a lowercase-hyphen .md slug"
      }
    ],
    "warnings": []
  }
```

**Not green — a REAL finding, per the brief's explicit warning.** Read
`cli/src/fusion/checker.py` to confirm this isn't operator error:
`_e8_filenames` walks every file in the `DOC_ZONES` (`library`,
`activities`, `output`) via `rglob("*")` — not scoped to `*.md` the way
`_e3_e4_e5_documents` is (that one uses `bucket.iter_documents`, which
filters to `*.md` and correctly ignores the csv). E8's filename regex
(`^[a-z0-9]+(?:-[a-z0-9]+)*\.md$`) requires the `.md` extension
unconditionally, so **any** non-`.md` file dropped in `output/` — exactly
what export.md's own step 2 tells the analyst to do — trips E8. The
companion `.md` document itself is fully conformant and contributes zero
findings on its own; the csv payload is what fails.

Per the brief's instruction, stopped that thread here: did not rename the
csv, did not move it out of `output/`, did not touch `checker.py`. The
`shipped` ledger entry stands as an honest record of what was produced.
This is recorded below as Friction #1 and carried into the final verdict
as a concern for the human to resolve (three options exist —
scope E8 to `*.md` like E3-E5 already are, special-case `resource:`
sidecar binaries, or accept non-md `output/` deliverables as always
warned-not-erred — none of which is this agent's call).

---

## Step 6 — close (gear: **close**, fusion-planner)

Explicit instruction to close the commitments activity. Per close.md step
1: confirm the target and that the human means finished. What would be
asked: *"`lp-listening` isn't due until 2026-07-24 — has the prep work
itself actually finished (mixes bounced, track order set, room booked),
or do you mean something else?"* Played the brief's stated outcome: yes,
finished — prep completed ahead of the session date (mixes bounced, both
candidate orders ready, room booked).

1. Edited `plan.md`: `status: active` → `status: done`,
   `aurora: commitments` → `aurora: archive`, checked off all three
   `## Steps` items, added a final `## Log` line naming the outcome.
2. Moved the folder: `activities/lp-listening/` →
   `activities/archive/lp-listening/`.
3. Signed:

```
fusion log archived "activities/lp-listening/ → activities/archive/lp-listening/" --bucket .../horizon-demo --as claude
fusion index .../horizon-demo --as claude
→ activities/ — 2 documents — regenerated
fusion check .../horizon-demo --json
→ {
    "bucket": "horizon-demo",
    "ok": false,
    "errors": [
      {
        "level": "error",
        "code": "E8",
        "path": "output/exports/library-title-type.csv",
        "message": "filename must be a lowercase-hyphen .md slug"
      }
    ],
    "warnings": []
  }
```

**Same single finding, unchanged** — the close operation itself introduces
zero new errors or warnings; path and aurora agree (`archive/` +
`aurora: archive`), no W3. The one E8 error is the pre-existing Step 5
finding, carried forward untouched, exactly as expected since nothing
about Step 5's export was modified.

**`fusion today`:**
```
Today across 1 bucket
  nothing demands you — the wide-open day.
```

**`fusion agenda`:**
```
the horizon is clear.
```

`lp-listening` no longer appears in either view — confirmed. No
deliverables shipped from this specific activity, so close.md step 5's
reminder (point the human to `output/`) doesn't apply here — the three
`output/` deliverables from Steps 3–5 stand on their own, not tied to this
activity's closure.

---

## Final state

```
fusion status /tmp/fusion-accept/horizon-demo
→ horizon-demo — 7 documents
    auroras: archive 1 · focus 1 · library 5
    types: assessment 1 · export 1 · gear 1 · guitar 1 · plan 2 · report 1
    activities: done 1 · dormant 1
    recent:
      2026-07-10 11:47 · claude · shipped · output/reports/library-inventory.md
      2026-07-10 11:47 · claude · shipped · output/assessments/gear-readiness.md
      2026-07-10 11:48 · claude · shipped · output/exports/library-title-type.csv
      2026-07-10 11:48 · claude · archived · activities/lp-listening/ → activities/archive/lp-listening/
      2026-07-10 11:48 · claude · indexed · activities/ (2 documents)
```

Full ledger:
```
# Ledger

## 2026-07-10
- 11:45 · claude · created · BUCKET.md — "bucket born"
- 11:46 · claude · created · library/gear/jazzmaster.md
- 11:46 · claude · created · library/gear/pedalboard.md
- 11:46 · claude · indexed · library/ (2 documents)
- 11:46 · claude · created · activities/lp-listening/plan.md
- 11:46 · claude · indexed · activities/ (1 document)
- 11:46 · claude · created · activities/pedalboard-refresh/plan.md
- 11:46 · claude · indexed · activities/ (2 documents)
- 11:46 · claude · noted · activities/pedalboard-refresh — status: active → dormant
- 11:47 · claude · shipped · output/reports/library-inventory.md
- 11:47 · claude · shipped · output/assessments/gear-readiness.md
- 11:48 · claude · shipped · output/exports/library-title-type.csv
- 11:48 · claude · archived · activities/lp-listening/ → activities/archive/lp-listening/
- 11:48 · claude · indexed · activities/ (2 documents)
```

`activities/` — `pedalboard-refresh/` (dormant, live) and
`archive/lp-listening/` (done). `output/` — one report, one assessment,
one export (csv + its `.md` passport). `library/` — the two seeded
documents, unchanged since setup.

## Step 7 — Transcript + commit

Cleanup and commit run exactly as the brief specifies (see repo history for
the actual commit — this document is that transcript).

## Verdict

**DONE_WITH_CONCERNS.** Six of seven scenario steps ran clean, `fusion
check` green throughout, ledger verbs correct (`created` ×4 real documents,
`noted` for the dormant flip, `shipped` ×3, `archived`), `fusion today` and
`fusion agenda` reflected every state change correctly (dated vs. undated,
the dormant drop, the post-close clear horizon), and no invented urgency or
dates anywhere. Step 5 surfaced one real, reproducible checker gap
(Friction #1) exactly where the brief warned it might — handled per
instruction: recorded, not patched, not routed around. The bucket was left
carrying that one finding for the remainder of the run (visible again,
unchanged, in Step 6's check) rather than being silently cleaned up, which
is the honest outcome given "the resolution belongs to the human."

## Frictions (feed the Phase-4 backlog)

1. **`fusion check`'s E8 rule fires on non-`.md` files in `output/`,
   which the export gear's own instructions tell the analyst to put
   there.** `_e3_e4_e5_documents` (E3-E5) correctly uses
   `bucket.iter_documents`, which is scoped to `*.md` — a csv/xlsx export
   is invisible to those rules, as intended. But `_e8_filenames`
   independently walks `DOC_ZONES` with `Path.rglob("*")` (all files, not
   `*.md`), and its filename regex hard-requires the `.md` extension. The
   result: every export gear run that ships a non-md binary alongside its
   `.md` passport document — the exact pattern `references/export.md`
   describes — makes `fusion check` report `ok: false` on a perfectly
   correct bucket. Three plausible fixes exist (scope E8 to `*.md` matching
   E3-E5's pattern; special-case files named by another document's
   `resource:` field; or downgrade this specific shape to a warning) — left
   for the human, per the brief. Not patched here.
2. **`fusion index` never touches `output/`.** `indexer.INDEXED_ZONES`
   covers `library/` and `activities/` only (confirmed: three `shipped`
   entries in Steps 3-5 each triggered a `fusion index` call that reported
   `library/ — unchanged` / `activities/ — unchanged` and nothing about
   `output/`). This matches the conventions card's registers table
   (`library/INDEX.md`, `activities/INDEX.md` — no `output/INDEX.md`
   listed) and SPEC's silence on an output index, so it's consistent
   design, not a bug — but neither `SKILL.md` nor `references/report.md` /
   `assess.md` / `export.md` says this explicitly, so an operator might
   reasonably run `fusion index` after a `shipped` expecting an
   `output/INDEX.md` to appear or update. Worth one line in
   `fusion-conventions.md`'s registers table saying output has no index.
3. **close.md's "confirm the human means finished" has no mechanical
   check behind it for a not-yet-due commitment.** Closing
   `lp-listening` five days before... 14 days before its `due:` date is
   entirely a judgment call the operator plays straight from the
   conversation; nothing in `fusion check` or the close gear itself flags
   "you're closing something before its own deadline" as worth a second
   look. Reasonable as designed (an early finish is legitimate and the
   human said so), but the gear's step 1 confirm is the *only* backstop —
   same shape as the librarian run's Friction #2 (promote's frontmatter
   STOP being pure operator discipline).

None of the above except Friction #1 affected the run's outcome — Frictions
#2 and #3 are documentation/observability gaps, not defects, and are
recorded here per the acceptance protocol for the Phase-4 backlog.
