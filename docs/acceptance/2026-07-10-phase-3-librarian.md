# Phase 3 acceptance — fusion-librarian, eight gears on a scratch bucket

ROADMAP gate: fusion-librarian (Task 6) exercised end-to-end, agent-in-the-loop,
on a live scratch bucket — following `skills/fusion-librarian/SKILL.md` and its
`references/` exactly, no shortcuts, no reading the gear scripts (there are
none; the librarian has no scripts, only judgment and the `fusion` CLI as
notary).

Sandbox, before any `fusion new`/`fusion hub` call:

```bash
export FUSION_HUB=/tmp/fusion-accept/hub.md FUSION_ACTOR=claude
mkdir -p /tmp/fusion-accept
cd <fusion repo root>
uv run --project cli fusion new /tmp/fusion-accept/librarian-demo --kind personal \
    --description "Librarian acceptance bucket."
```

`fusion new` scaffolded the bucket, registered it in `/tmp/fusion-accept/hub.md`,
and — unprompted — `git init`'d and committed the bucket itself ("fusion new:
bucket born"). Not documented in SKILL.md but harmless and out of scope for
this run. Read `references/fusion-conventions.md` and the fresh `BUCKET.md`
(empty `### Rules` / `### Delegations`) before touching anything, per
SKILL.md's opening instruction — nothing bound the run at the start.

`fusion log`, `fusion index`, `fusion check` all take a positional `path` (or
`log` takes `--bucket`); confirmed with `--help` up front, no failed calls
this run (unlike the intake acceptance run's friction #4).

---

## Step 1 — Seed (gear: **create**)

Gear chosen because the brief calls for four new documents born conformant —
the textbook `create` case (references/create.md). Four documents authored,
each closed with the gear's own three-beat discipline: `fusion log created` ·
`fusion index` · `fusion check`.

1. `library/gear/jazzmaster.md` — `title`, `type: guitar`, `aurora: library`,
   `created`, summary-first body with real facts (serial number, purchase
   price/date, pickup output, the pending Mastery-bridge upgrade).
2. `library/gear/pedalboard.md` — `type: gear`, `aurora: library`, signal
   chain and power supply facts.
3. `activities/lp-first-light/plan.md` — `type: activity-plan`,
   `aurora: focus`, `status: active`, a five-song recording plan that links
   to the Jazzmaster document.
4. `workbench/q3-ideas.md` — **no frontmatter**, a rough bullet list, one
   relative link back to the Jazzmaster doc. Workbench has no rules; create
   still writes it and still signs it, but skips the conformance write-up
   entirely (nothing to establish).

```
fusion log created "library/gear/jazzmaster.md" --bucket .../librarian-demo --as claude
fusion index .../librarian-demo --as claude
fusion check .../librarian-demo
→ librarian-demo: 0 errors · 0 warnings — clean, carry on.

fusion log created "library/gear/pedalboard.md" ... / index / check → clean
fusion log created "activities/lp-first-light/plan.md" ... / index / check → clean
fusion log created "workbench/q3-ideas.md" ... / index / check --json
→ {"bucket": "librarian-demo", "ok": true, "errors": [], "warnings": []}
```

Confirmed precisely what the brief asked: the workbench draft has zero
frontmatter and `fusion check` stayed green with **zero** findings — because
`workbench/` is not one of the checker's document zones (`library`,
`activities`, `output`), so nothing there is ever inspected. Frictions #1
below covers a real gap this step surfaced in `fusion index`'s scoping.

Ledger tail after Step 1:
```
- 11:19 · claude · created · BUCKET.md — "bucket born"
- 11:20 · claude · created · library/gear/jazzmaster.md
- 11:20 · claude · indexed · library/ (2 documents)
- 11:20 · claude · indexed · activities/ (1 document)
- 11:20 · claude · created · library/gear/pedalboard.md
- 11:20 · claude · created · activities/lp-first-light/plan.md
- 11:20 · claude · created · workbench/q3-ideas.md
```

---

## Step 2 — Query (gear: **query**)

"What do we know about the Jazzmaster?" — bare natural-language ask, default
gear, read-only, logs nothing (references/query.md).

Triage: `library/INDEX.md` titles/summaries, then grep for "jazzmaster"
across `library/` and `activities/` → two hits, `library/gear/jazzmaster.md`
and `activities/lp-first-light/plan.md`. Both read in full (well under the
~10-read ceiling).

**Answer played:**

> The bucket holds one instrument document on the Jazzmaster:
> `library/gear/jazzmaster.md` — a 1962 reissue, serial `JM62-0451`, bought
> 2026-05-14 for €1,850 at the Q2 gear swap, sunburst nitro finish, rosewood
> board. Stock single-coils measured at 6.4k Ω (neck) / 7.1k Ω (bridge).
> The original vintage-style bridge is flagged as string-skip-prone; a
> Mastery bridge upgrade is queued for Q3. Strung 011-050 flatwound.
>
> It's also the primary guitar for the "First Light" LP sessions —
> `activities/lp-first-light/plan.md` names it as the DI + mic'd-amp source
> for all guitar tracking on that five-song EP.
>
> ## Sources
> | Path | Contributed |
> |---|---|
> | `library/gear/jazzmaster.md` | specs, purchase history, condition, upgrade plan |
> | `activities/lp-first-light/plan.md` | its role in the current recording plan |
>
> Nothing outside these two documents mentions it — no pricing history beyond
> the one purchase, no maintenance log yet.

Cites both paths, invents nothing beyond what's in the two documents (no
outside knowledge about Fender Jazzmasters injected). No ledger entry, no
index/check needed — read-only gear, as specified.

---

## Step 3 — Tag (gear: **tag**)

"Add `tags: [guitars]` across `library/gear/`" — explicit bulk-metadata
instruction (references/tag.md). Scope at this point: `library/gear/` held
both `jazzmaster.md` and `pedalboard.md`.

Edited each document's frontmatter only — inserted `tags: [guitars]`,
preserved every existing key and the body byte-for-byte.

| File | Field | Old → New |
|---|---|---|
| `library/gear/jazzmaster.md` | `tags` | (absent) → `[guitars]` |
| `library/gear/pedalboard.md` | `tags` | (absent) → `[guitars]` |

One ledger entry for the batch, then index (no summaries changed, so no
`indexed` fired), then check:

```
fusion log classified "library/gear/ — tags: [guitars] (2 documents)" --as claude
fusion index .../librarian-demo --as claude
→ library/ — 2 documents — unchanged
fusion check .../librarian-demo
→ librarian-demo: 0 errors · 0 warnings — clean, carry on.
```

`updated:` was correctly left untouched on both documents (metadata, not
content, per tag.md's own instruction).

---

## Step 4 — Promote (gear: **promote**) — the must-STOP path

Explicit invocation ("promote the workbench draft"), source in `workbench/`,
destination named: `library/notes/q3-ideas.md`. Pre-flight per
references/promote.md, all three checked before anything moves.

**First attempt.** Read `workbench/q3-ideas.md`: a bare bullet list, no
`---` frontmatter block at all. Promote's validation is explicit: *"frontmatter
parses; title, type, aurora present... a failed check stops the promotion,
nothing moves."* This fails at the first clause — **STOP**.

What would be asked of the human at this point: *"`workbench/q3-ideas.md` has
no frontmatter — I can't promote it as-is. Want me to add `title`, `type`,
`aurora`, and a `## Summary`, or leave it in the workbench for now?"* Played
the brief's stated outcome: **fix it**.

Fixed the draft in place (still in `workbench/`, no move yet):
- `title: Q3 gear ideas`, `type: notes`, `aurora: explore`, `created: 2026-07-10`
- `## Summary` (two lines) + `---` separator ahead of the existing body
- also corrected the one relative link so it resolves from the *destination*
  (`library/notes/`) rather than the draft's current location — a judgment
  call folded into "fix what needs fixing," see Frictions #3.

**Re-promote.** Validation now passes (frontmatter parses, three required
fields present, summary-first body, slug ≤60 chars). State the plan: "Promoting
`workbench/q3-ideas.md` to `library/notes/q3-ideas.md`." Moved (write new +
delete old), signed, indexed, checked:

```
fusion log promoted "workbench/q3-ideas.md → library/notes/q3-ideas.md" --as claude
fusion index .../librarian-demo --as claude
→ library/ — 3 documents — regenerated
fusion check .../librarian-demo --json
→ {"bucket": "librarian-demo", "ok": true, "errors": [], "warnings": []}
```

Fully green — no W4 (broken link) despite the document having just moved
zones, because the link was corrected for its new home before the move.

---

## Step 5 — Archive (gear: **archive**)

"Archive one gear document" — direct instruction, so the authority
pre-condition (references/archive.md #1) is the explicit ask itself, no
delegation needed. Target: `library/gear/pedalboard.md`.

1. Moved to `library/archive/gear/pedalboard.md`.
2. Frontmatter edited: `aurora: archive` (no `status` field on a `gear`
   document — nothing to bump there).
3. Signed, indexed, checked:

```
fusion log archived "library/gear/pedalboard.md → library/archive/gear/pedalboard.md" --as claude
fusion index .../librarian-demo --as claude
→ library/ — 3 documents — regenerated
fusion check .../librarian-demo --json
→ {"bucket": "librarian-demo", "ok": true, "errors": [], "warnings": []}
```

**W3 silent, confirmed by design**: the checker's `_w3_w4_documents` flags a
mismatch between an `archive/` path and a non-`archive` aurora (or vice
versa) — here path and aurora agree in the same move, so the warning that
watches exactly this never fires. Verified by reading `checker.py` after the
fact, not by taking it on faith.

---

## Step 6 — Restructure (gear: **restructure**)

"Rename `library/gear/` to `library/instruments/`" — the most destructive
gear, run as propose → confirm → execute → sign (references/restructure.md).
At this point `library/gear/` held exactly one document, `jazzmaster.md`
(pedalboard had already moved to `archive/gear/` in Step 5).

**Propose.** Plan: move `library/gear/jazzmaster.md` →
`library/instruments/jazzmaster.md`; retire the now-empty `library/gear/`
folder; leave `library/archive/gear/` untouched (archived items are already
"out of the way" — the archive-path/aurora agreement W3 watches doesn't
depend on the live zone's current folder name, and nothing in
`references/archive.md` or `restructure.md` requires archive subfolders to
track a live rename — a judgment call, see Frictions #4). Grepped every `.md`
for `gear/jazzmaster` first to find every link that would break: two hits —
`activities/lp-first-light/plan.md` and `library/notes/q3-ideas.md` (both
written earlier in this run, deliberately, to give restructure something
real to fix). Checked `BUCKET.md ### Rules` — empty, nothing to contradict.

Reason (the note): *"gear was a miscellaneous label; the collection is
specifically musical instruments (guitars, pedalboard) — renamed to match
the make-model filing the bucket actually uses."*

**Confirm.** Played as a direct instruction from the human (the brief names
the rename outright) — treated as the yes.

**Execute.** Moved the file; updated both relative links
(`../../library/gear/jazzmaster.md` → `../../library/instruments/jazzmaster.md`
in the activity plan; `../gear/jazzmaster.md` → `../instruments/jazzmaster.md`
in the promoted note); re-grepped afterward to confirm zero remaining
`gear/jazzmaster` references outside `LEDGER.md` (immutable history, correctly
untouched).

**Sign.**
```
fusion log restructured "library/gear/ → library/instruments/" \
    --note "gear was a miscellaneous label; the collection is specifically \
musical instruments (guitars, pedalboard) — renamed to match the make-model \
filing the bucket actually uses; 1 document moved (jazzmaster.md), 2 \
relative links updated (activities/lp-first-light/plan.md, \
library/notes/q3-ideas.md); archive/gear/ left as-is, archived items are \
out of the active taxonomy" --as claude
fusion index .../librarian-demo --as claude
→ library/ — 3 documents — regenerated
fusion check .../librarian-demo --json
→ {"bucket": "librarian-demo", "ok": true, "errors": [], "warnings": []}
```

Green, including **W4 silent** — the link-integrity warning that watches
exactly the move just made, confirmed clean because both links were actually
fixed before signing.

---

## Step 7 — Reflect (gear: **reflect**)

references/reflect.md's four beats, on the bucket's very first cycle (no
prior `reflected` entry).

**1. Introspect.**
```
fusion log --since last-reflection --bucket .../librarian-demo
```
No prior reflection exists, so `--since last-reflection` returned the whole
ledger from bucket birth — 16 entries (bucket-born through the restructure's
`indexed`). `fusion status --since last-reflection` and `fusion check` also
run — the latter still green.

**2. Curate & prune.** Two proposals, per the brief:

- **Dormant-activity**: `activities/lp-first-light/plan.md` is
  `status: active` with exactly one ledger touch this window — its own
  `created` entry. No tracking session, no progress note. Proposed
  reclassifying it `dormant` until real recording work starts, to keep
  "active" meaningful. (See Frictions #5 — this is pure editorial judgment,
  not the checker's W5 heuristic, which cannot fire on a bucket's first-ever
  reflection.)
- **New Rule**: *"Instruments are filed by make-model"* — codifying what
  Step 6's restructure just did in practice, so future creates/promotes
  don't reinvent the `gear/` label.

**3. Judge.** Presented both, separately (never bundled, per reflect.md).
What would be asked: *"(a) Mark `lp-first-light` dormant — no session
activity beyond its own creation this window. (b) Add a Rule: instruments
are filed by make-model, e.g. `library/instruments/<slug>.md`. Approve
either, both, or neither?"* Played the brief's stated outcome: **yes to
both**.

**4. Learn & sign.** Executed each approved act through its own gear-verb,
per reflect.md's instruction not to let reflect itself carry acts that
belong to other gears:

```
fusion log classified "activities/lp-first-light/plan.md — status: dormant (1 document)" --as claude
fusion log noted "BUCKET.md — added Rule: instruments are filed by make-model" --as claude
fusion log reflected "librarian-demo — 2 proposals, 2 adopted" --as claude
fusion index .../librarian-demo --as claude
fusion check .../librarian-demo --json
→ {"bucket": "librarian-demo", "ok": true, "errors": [], "warnings": []}
```

`BUCKET.md ### Rules` now reads:
```
- Instruments are filed by make-model (e.g. `library/instruments/jazzmaster.md`), not under a generic `gear/` label.
```

**Verification (brief's explicit ask):**
```
fusion log --since last-reflection --bucket .../librarian-demo --json
→ []
```
Empty window, confirmed — `reflected` is now the ledger's last entry, so
everything "since last reflection" is nothing, exactly as designed.

---

## Final state

```
fusion check /tmp/fusion-accept/librarian-demo
→ librarian-demo: 0 errors · 0 warnings — clean, carry on.

fusion status /tmp/fusion-accept/librarian-demo
→ librarian-demo — 4 documents
    auroras: archive 1 · explore 1 · focus 1 · library 1
    types: activity-plan 1 · gear 1 · guitar 1 · notes 1
    activities: dormant 1
    recent:
      2026-07-10 11:22 · claude · restructured · library/gear/ → library/instruments/
      2026-07-10 11:22 · claude · indexed · library/ (3 documents)
      2026-07-10 11:23 · claude · classified · activities/lp-first-light/plan.md — status: dormant (1 document)
      2026-07-10 11:23 · claude · noted · BUCKET.md — added Rule: instruments are filed by make-model
      2026-07-10 11:23 · claude · reflected · librarian-demo — 2 proposals, 2 adopted
```

Full ledger (17 entries, one date heading):
```
# Ledger

## 2026-07-10
- 11:19 · claude · created · BUCKET.md — "bucket born"
- 11:20 · claude · created · library/gear/jazzmaster.md
- 11:20 · claude · indexed · library/ (2 documents)
- 11:20 · claude · indexed · activities/ (1 document)
- 11:20 · claude · created · library/gear/pedalboard.md
- 11:20 · claude · created · activities/lp-first-light/plan.md
- 11:20 · claude · created · workbench/q3-ideas.md
- 11:21 · claude · classified · library/gear/ — tags: [guitars] (2 documents)
- 11:21 · claude · promoted · workbench/q3-ideas.md → library/notes/q3-ideas.md
- 11:21 · claude · indexed · library/ (3 documents)
- 11:21 · claude · archived · library/gear/pedalboard.md → library/archive/gear/pedalboard.md
- 11:21 · claude · indexed · library/ (3 documents)
- 11:22 · claude · restructured · library/gear/ → library/instruments/ — "gear was a miscellaneous label; the collection is specifically musical instruments (guitars, pedalboard) — renamed to match the make-model filing the bucket actually uses; 1 document moved (jazzmaster.md), 2 relative links updated (activities/lp-first-light/plan.md, library/notes/q3-ideas.md); archive/gear/ left as-is, archived items are out of the active taxonomy"
- 11:22 · claude · indexed · library/ (3 documents)
- 11:23 · claude · classified · activities/lp-first-light/plan.md — status: dormant (1 document)
- 11:23 · claude · noted · BUCKET.md — added Rule: instruments are filed by make-model
- 11:23 · claude · reflected · librarian-demo — 2 proposals, 2 adopted
```

`library/` — 4 documents (`instruments/jazzmaster.md`, `notes/q3-ideas.md`,
`archive/gear/pedalboard.md`, plus the regenerated `INDEX.md`).
`activities/` — 1 document (`lp-first-light/plan.md`, now `status: dormant`).
`workbench/` — empty (its one draft was promoted out in Step 4).

## Verdict

**DONE.** All eight gears played on a single scratch bucket, in the sequence
the brief specified, with `fusion check` green after every single close
point — including the one deliberate STOP (promote on missing frontmatter)
and the two deliberately engineered link-breaking moves (restructure), both
handled per the reference docs with no shortcuts. The reflection ritual
closed its own window correctly (`--since last-reflection` empty right after
signing). No skill document or CLI command needed patching to get here —
the frictions below are real but none blocked the run.

## Frictions (feed the Phase-4 list)

1. **`fusion index` is disk-state-scoped, not act-scoped.** After logging
   only `library/gear/jazzmaster.md`'s `created` entry, `fusion index`
   picked up **both** `jazzmaster.md` and `pedalboard.md` into
   `library/INDEX.md` — because `pedalboard.md` already existed on disk
   (all four Step-1 documents were authored before their individual
   `created` acts were logged). `INDEX.md` can silently run ahead of the
   ledger's narrative: nothing enforces "index only reflects documents
   whose creation is already signed." Not a bug — `fusion index`'s job is
   to regenerate from the real tree — but an agent that writes several
   documents before logging any of them will find the index already
   includes the unlogged ones. Worth a line in `references/create.md`
   telling operators to log-then-index per document if act/index parity
   matters.
2. **`promote`'s frontmatter STOP is entirely the operator's own
   discipline — `fusion check` cannot backstop it.** The checker's document
   zones (`library`, `activities`, `output`) exclude `workbench/` by
   design (confirmed in `bucket.py`'s `DOC_ZONES`), so a frontmatter-less
   draft sitting in `workbench/` never trips any error or warning. The
   "strict writer" gate promote.md describes is real, but it lives
   entirely in the gear's own pre-flight reading — there is no CLI
   tripwire behind it. Fine as designed (workbench is explicitly
   ruleless), but worth being explicit about in the skill so a future
   operator doesn't assume `fusion check` would have caught a skipped
   promote validation.
3. **Fixing a workbench draft's internal links for its future destination
   is not covered by promote.md's validation checklist.** The checklist
   names frontmatter, required fields, summary-first body, and filename
   length — not relative links. This run's draft carried a link written
   relative to `workbench/`; promoting it verbatim to `library/notes/`
   would have silently broken it (no W4 until the next `fusion check`,
   which — being run right after promote — would have caught it, but only
   as a warning, not a blocking error). Chose to fix the link as part of
   "fix what the user wants fixed" while already editing the draft's
   frontmatter. Consider adding "check and fix relative links for the
   destination" to promote.md's pre-flight explicitly.
4. **No documented policy for archive subfolder names after a live-zone
   restructure.** Step 6 renamed `library/gear/` to `library/instruments/`
   while `library/archive/gear/` (created one step earlier) was left
   untouched — `restructure.md` says nothing about whether archived
   subfolders should track a rename of their live counterpart, and W3 only
   checks path/aurora agreement, not naming consistency between a zone and
   its `archive/` mirror. Judgment call made here (leave it); a bucket with
   a longer history could end up with an `archive/` tree full of
   folder names that no longer match anything live. Worth a line in
   `restructure.md` either way.
5. **`reflect.md`'s W5 dormant-activity signal cannot fire on a bucket's
   first-ever reflection.** `checker._w5_untouched_activities` requires at
   least two `reflected` entries to define a comparison window; on the
   very first reflection there is no such window, so "W5 already names
   them" (reflect.md's own parenthetical) over-promises — the dormant
   proposal made in this run was pure editorial judgment (one `created`
   touch, nothing since), not a mechanically-assisted one. True on every
   bucket's first cycle, not just this scratch one. Worth a caveat in
   reflect.md for first-reflection runs.

None of the above blocked the run or required patching a skill file or the
CLI — recorded here per the acceptance protocol for the Phase-4 backlog.
