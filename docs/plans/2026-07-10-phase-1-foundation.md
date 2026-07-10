# Fusion Phase 1 — Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce the Fusion Convention (`SPEC.md`) as a normative, publishable document, plus a complete conformant example bucket that doubles as the test fixture for Phase 2, plus the README manifesto and the phased roadmap with QA gates.

**Architecture:** Phase 1 is documentation-as-product: the spec IS the product (OKF lesson); the example bucket is its executable proof; the README is its voice. No code ships in this phase — Phase 2 (CLI) builds against the fixture created here. Every task ends with a mechanical verification gate (grep/find sweeps with expected output) because there is no `fusion check` yet.

**Tech Stack:** Markdown, YAML frontmatter, git. (Python/uv arrive in Phase 2.)

**Design spec:** `docs/specs/2026-07-10-fusion-design.md` — read it before starting. This plan implements its §§1–4 (convention), parts of §5 (ledger/hub formats), §7 (metabolism contract), §8 (repo layout, license), and seeds §10 (testing fixture).

## Global Constraints

- **Tone:** rebel misfit (Think Different) in prose (README, spec preambles); **clarity always wins** in structure — zone names, field names, grammar rules stay plain and unambiguous. Not boring AI, not consultant, not wellbeing coach, not tech nerd.
- **The eight auroras, verbatim, closed:** `commitments`, `focus`, `ops`, `collab`, `life`, `explore`, `archive`, `library`. Never add, rename, or make configurable.
- **The eleven ledger verbs, verbatim, closed:** `created`, `converted`, `classified`, `indexed`, `moved`, `promoted`, `archived`, `restructured`, `shipped`, `reflected`, `noted`.
- **Three required document fields:** `title`, `type`, `aurora`. All other frontmatter optional.
- **Filenames:** lowercase, hyphen-separated, `.md` for documents, ≤60 chars before extension.
- **Error posture:** liberal reader, strict writer — spec language must encode this (consumers MUST NOT reject; producers MUST validate).
- **No personal paths** anywhere in committed files (this repo will be open-sourced). Example bucket uses fictional content only.
- **License:** MIT, copyright Bluewaves Boutique.
- **Git:** work directly on `main`, linear history, commit per task, **never push** (user pushes manually).
- **Format version:** `fusion_version: "1.0"` everywhere it appears.

---

### Task 1: Repo foundation — license and hygiene

**Files:**
- Create: `LICENSE.md`
- Create: `.gitignore`

**Interfaces:**
- Consumes: nothing (first task).
- Produces: MIT license and ignore rules all later phases rely on; `.gitignore` patterns Phase 2 (Python) extends.

- [ ] **Step 1: Write `LICENSE.md`**

```markdown
MIT License

Copyright (c) 2026 Bluewaves Boutique

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 2: Write `.gitignore`**

```gitignore
.DS_Store
__pycache__/
*.pyc
.venv/
dist/
*.egg-info/
```

- [ ] **Step 3: Verify**

Run: `test -f LICENSE.md && grep -c "MIT License" LICENSE.md && test -f .gitignore && echo OK`
Expected: `1` then `OK`

- [ ] **Step 4: Commit**

```bash
git add LICENSE.md .gitignore
git commit -m "chore: MIT license and git hygiene"
```

---

### Task 2: SPEC.md Part 1 — preamble, conformance, hub, bucket anatomy, BUCKET.md

**Files:**
- Create: `SPEC.md` (sections 0–3)

**Interfaces:**
- Consumes: design spec §§1–3.
- Produces: normative §0 (conformance language), §1 (hub entry grammar `- **<name>** · <kind> · <path> — <description>`), §2 (zone list: `inbox sources library activities workbench output` + `BUCKET.md` + `LEDGER.md`), §3 (BUCKET.md frontmatter: `name`, `kind`, `description`, `fusion_version`, `created` required; `inbox_max_age_days`, `reflection_cadence` optional; body sections `## Conventions` → `### Rules` + `### Delegations`). Task 3 appends to this same file; Phase 2's `fusion check`/`fusion new`/`fusion hub` implement these rules; Tasks 4–6 must conform to them.

- [ ] **Step 1: Write `SPEC.md` with sections 0–3**

````markdown
# The Fusion Convention

**Version 1.0**

Fusion is a file-based working environment for Human + AI collaboration —
knowledge, activities, and their shared record — living entirely in markdown
on a filesystem. It is operable by any capable agent and by any human with a
text editor. It is not a document-management system, not a PKM, not a note
app. It refuses the category.

The contract the whole convention serves:

> **The human judges, the AI operates, the files remember.**

This document is the product. Everything else — the `fusion` CLI, the skill
family — is a reference implementation. Rewrite the tools in any language;
buckets that follow this convention are Fusion.

## 0. Conformance

The key words MUST, MUST NOT, SHOULD, and MAY are to be interpreted as in
RFC 2119.

**Liberal reader, strict writer:**

- A **consumer** (anything reading a bucket) MUST NOT reject a bucket or a
  document because of missing optional fields, unknown `type` values, unknown
  frontmatter keys, broken links, or missing INDEX files. A half-migrated
  bucket is still a bucket.
- A **producer** (anything writing to `library/`, `activities/`, `output/`,
  or any register) MUST satisfy every applicable MUST in this convention
  before writing. Validation happens before damage, not after.

## 1. The hub

The hub registers a machine's buckets so any agent can discover the user's
world. It lives at `~/.fusion/hub.md` and is maintained by `fusion hub`;
hand edits MUST be tolerated by consumers.

```markdown
# Fusion Hub

- **personal** · personal · ~/Fusion/personal — life, training, the wide-open days
- **studio** · studio · ~/Fusion/studio — music, photography, instruments
- **acme** · company · ~/Work/acme-fusion — the Acme engagement
```

Entry grammar, one line per bucket:

    - **<name>** · <kind> · <path> — <description>

- `name` MUST be unique in the hub and MUST equal the bucket's
  `BUCKET.md` `name`.
- `kind` SHOULD be one of `personal`, `company`, `studio`, `club` — but the
  vocabulary is open (liberal reader).
- `path` is absolute or `~`-relative.
- The hub is per-machine and never synced; buckets are the durable objects.

## 2. Bucket anatomy

A bucket is a directory — its own git repository — with this exact shape.
All zones MUST exist from creation; an empty zone carries a `.gitkeep`.

```
<bucket>/
├── BUCKET.md        # identity card + learned conventions (§3)
├── LEDGER.md        # append-only collaboration record (§6)
├── inbox/           # drop zone — things arrive here, nothing lives here
├── sources/         # immutable originals + MANIFEST.md (§7)
├── library/         # settled knowledge — documents per §4
├── activities/      # live work — documents per §4, plus status
├── workbench/       # ephemeral human+AI space — NO format rules
└── output/          # finished deliverables — documents per §4
```

Zone rules:

- `inbox/` — ephemeral by contract. Files older than `inbox_max_age_days`
  (§3) are a conformance warning.
- `sources/` — immutable. Files here MUST NOT be modified, renamed, or
  deleted after registration in `MANIFEST.md`. Organized in subdirectories
  by category.
- `library/`, `activities/`, `output/` — every `.md` file MUST conform to
  the document format (§4). `INDEX.md` files (§8) are generated and exempt.
- `workbench/` — no rules. Half-baked work belongs here. Leaving workbench
  (promotion) is a deliberate, ledger-logged act.
- Fusion holds knowledge and work, never media or code. Big binaries and
  repositories stay in their native homes; documents point to them
  (`resource:`, §4).

## 3. BUCKET.md

The bucket's identity card and its long-term memory of how it works.

```markdown
---
name: studio
kind: studio
description: Music, photography, instruments — the creative domain.
fusion_version: "1.0"
created: 2026-07-10
inbox_max_age_days: 7
reflection_cadence: weekly
---

Free-form introduction: what this bucket is for, what lives here,
anything a new collaborator (human or AI) should know first.

## Conventions

### Rules

- Instruments are filed one document per instrument, by slug of make-model-year.
- Session notes are weekly, never daily.

### Delegations

- The librarian may archive dormant explore-aurora documents without asking.
```

- Frontmatter `name`, `kind`, `description`, `fusion_version`, `created`
  are REQUIRED. `inbox_max_age_days` (default 7) and `reflection_cadence`
  (free text) are optional.
- `## Conventions` holds what the bucket has learned (§10): `### Rules` are
  operating rules discovered through use; `### Delegations` are standing
  grants of autonomy to the AI colleague. Both are maintained by the
  librarian; every change MUST be ledger-logged.
- Skills MUST read `## Conventions` before acting on the bucket.
````

- [ ] **Step 2: Verify**

Run: `grep -cE '^## [0-3]\. ' SPEC.md && grep -c 'MUST' SPEC.md | awk '{print ($1>=10) ? "OK" : "FAIL"}'`
Expected: `4` (numbered sections 0–3) then `OK`

- [ ] **Step 3: Commit**

```bash
git add SPEC.md
git commit -m "spec: conformance language, hub, bucket anatomy, BUCKET.md (SPEC 0-3)"
```

---

### Task 3: SPEC.md Part 2 — documents, aurora, ledger, sources, INDEX, archive, metabolism, conformance checklist

**Files:**
- Modify: `SPEC.md` (append sections 4–11)

**Interfaces:**
- Consumes: Task 2's SPEC.md sections 0–3; design spec §§4–5, 7, 9.
- Produces: §4 document grammar (frontmatter fields + summary-first), §5 aurora table, §6 ledger grammar + 11 verbs, §7 MANIFEST table grammar (`| file | added | by | sha256 | library |`), §8 INDEX format + generated marker `<!-- generated by fusion index — do not edit -->`, §9 archive rule, §10 metabolism contract, §11 conformance checklist (errors vs warnings). Phase 2 implements §11 literally as `fusion check`; Tasks 4–6 conform to all of it.

- [ ] **Step 1: Append sections 4–11 to `SPEC.md`**

````markdown
## 4. The document format

Every `.md` file in `library/`, `activities/`, and `output/` (except
`INDEX.md`) is a document: YAML frontmatter, then a summary, then the body.

```markdown
---
title: Jazzmaster 1962
type: instrument
aurora: library
tags: [guitars, offsets, vintage]
created: 2026-07-10
updated: 2026-07-10
source: sources/manuals/jazzmaster-1962-manual.pdf
resource: https://reverb.com/item/example
status: active
data_sources: [library/instruments/jazzmaster-1962.md]
---

## Summary

Two or three lines a human or agent reads in two seconds to know
whether to open the rest.

---

Full body below the separator. Standard markdown. Cross-links are plain
relative paths: [the LP plan](../activities/lp-first-light/plan.md).
```

**Required fields (exactly three):**

| Field | Meaning |
|---|---|
| `title` | Human-readable display name |
| `type` | What the document *is* — open vocabulary, curated per bucket by the librarian |
| `aurora` | What it *means for the human's attention* — one of the eight (§5) |

**Optional fields:**

| Field | Meaning | Where |
|---|---|---|
| `tags` | YAML list of short strings | anywhere |
| `created` / `updated` | ISO 8601 dates | anywhere |
| `source` | Path into `sources/` — the original this was converted from | library |
| `resource` | URI of an external thing this document describes | anywhere |
| `status` | `active` \| `done` \| `dormant` | activities only |
| `data_sources` | YAML list of bucket paths this was built from | output only |

Producers MAY add other keys; consumers MUST tolerate and SHOULD preserve
unknown keys.

**Summary-first, always:** the body MUST begin with `## Summary`, then a
`---` separator line, then the full content. An agent triages a bucket by
reading INDEX files and summaries alone.

**Links** are standard relative markdown links. Consumers MUST tolerate
broken links — they may point at knowledge not yet written.

**Filenames:** lowercase, hyphen-separated, `.md`, ≤60 characters before
the extension, meaningful slugs.

## 5. Aurora

Aurora is an attention model, not a category taxonomy: it says what a
document means for the human's energy. It is a lens over structure, never
a replacement for it. The vocabulary is CLOSED — the eight are the eight:

| Aurora | Meaning |
|---|---|
| `commitments` | Obligations, promises, deadlines |
| `focus` | Deep work, what deserves full attention |
| `ops` | Operations, process, the recurring |
| `collab` | Shared work, other people involved |
| `life` | Personal, wellbeing, the non-work |
| `explore` | Curiosity, research, the not-yet-settled |
| `archive` | Done, kept, out of the way |
| `library` | Reference, the settled knowledge |

A producer MUST set `aurora` to one of these eight. Anything else is a
conformance error.

## 6. The ledger

`LEDGER.md` at bucket root is the collaboration record: what was done, by
whom, and why. Git remembers bytes; the ledger remembers meaning. It is
append-only, chronological, and has exactly one writer: `fusion log`.
Neither humans nor agents edit it by hand.

```markdown
# Ledger

## 2026-07-10
- 07:42 · claude · converted · sources/manuals/jazzmaster-1962-manual.pdf → library/instruments/jazzmaster-1962.md
- 09:10 · bertrand · promoted · workbench/q3-draft.md → output/reports/q3-review.md
- 18:30 · pi · restructured · library/clients/ — "taxonomy stopped serving"
```

Entry grammar, under `## YYYY-MM-DD` date headings, oldest date first,
entries appended in order:

    - HH:MM · <actor> · <verb> · <object>[ — "<note>"]

- `actor` is whoever holds the pen: an agent name (`claude`, `pi`,
  `goose`, …) or the human's name. Resolved from `FUSION_ACTOR` or `--as`.
- `verb` is one of the CLOSED set of eleven: `created`, `converted`,
  `classified`, `indexed`, `moved`, `promoted`, `archived`,
  `restructured`, `shipped`, `reflected`, `noted`. `noted` is the escape
  hatch; `reflected` signs off a reflection cycle (§10).
- `restructured` entries SHOULD carry a note with the justification —
  ownership means showing your reasons.

## 7. Sources and MANIFEST.md

`sources/` preserves originals forever, out of the knowledge but never out
of reach. Files are registered in `sources/MANIFEST.md`:

```markdown
# Manifest

| file | added | by | sha256 | library |
|---|---|---|---|---|
| gear/pedalboard-inventory.csv | 2026-07-10 | claude | 3b8f… | library/instruments/pedalboard.md |
```

- Every file in `sources/` MUST have a manifest row; `sha256` (first 8+
  hex chars minimum, full hash preferred) pins immutability.
- `library` column points at the converted document(s), comma-separated —
  or `—` when not (yet) converted.

## 8. INDEX.md

`library/INDEX.md` and `activities/INDEX.md` are GENERATED files
(`fusion index`) giving one-page triage before opening anything. They MUST
carry the marker and MUST NOT be hand-edited:

```markdown
<!-- generated by fusion index — do not edit -->
# Library Index

## instruments/

- [Jazzmaster 1962](instruments/jazzmaster-1962.md) — 1962 Fender Jazzmaster: provenance, setup, service history (library)
- [Pedalboard](instruments/pedalboard.md) — current pedalboard chain and settings (library)
```

Entry grammar: `- [<title>](<relative-path>) — <summary first line> (<aurora>)`.
Consumers MUST tolerate a missing or stale INDEX (liberal reader).

## 9. Archive

There is no archive zone. Archived items move to an `archive/` subfolder
*within their zone* (`library/archive/…`, `activities/archive/…`) and take
`aurora: archive`. **Path is the truth, aurora is the signal.** Both MUST
agree; disagreement is a conformance warning.

## 10. The metabolism

A bucket that only operates is a filing cabinet with better manners. The
loop: **the files remember → the AI reflects → the human judges → the
system learns.**

- **The Reflection** — per bucket, on the `reflection_cadence` suggested in
  BUCKET.md, invoked by the human or their agent's scheduler (Fusion has no
  watchers). The librarian: (1) introspects the ledger since the last
  `reflected` entry plus check/status output; (2) proposes curation and
  pruning — stale workbench items, dormant activities, superseded documents
  to archive, duplicates to merge, summaries drifted from bodies, taxonomy
  that stopped serving; (3) submits proposals to the human — destructive
  and archival acts need a yes, except under standing delegation; (4) lands
  what was learned in `BUCKET.md ## Conventions` and signs off with a
  `reflected` ledger entry.
- **Learning** lives in `BUCKET.md ## Conventions` (§3): the long-term
  memory of *how this bucket works*. The ledger is the episodic memory of
  *what happened*. Every convention change is ledger-logged.
- **Trust** widens through `### Delegations`: explicit, recorded, revocable
  grants of autonomy. Earned the way trust between humans is earned — by a
  ledger that proves reliability.
- Reflection sees *actions*, not *reads*: Fusion learns from what the
  centaur did, not what it glanced at. That is the portable trade.

## 11. Conformance

A checker (reference implementation: `fusion check`) validates a bucket.

**Errors** (strict writer violations):

1. Zone missing from the bucket root (§2).
2. BUCKET.md missing or lacking a required frontmatter field (§3).
3. A document in `library/`, `activities/`, or `output/` with unparseable
   frontmatter, or missing `title`, `type`, or `aurora` (§4).
4. `aurora` not one of the eight (§5).
5. A document body not summary-first (§4).
6. A ledger entry with a verb outside the eleven (§6).
7. A `sources/` file absent from MANIFEST.md, or a manifest row whose file
   is gone (§7).
8. A filename violating §4 rules, in the three document zones.

**Warnings** (drift, not damage):

1. Inbox files older than `inbox_max_age_days` (§2).
2. INDEX.md stale or missing (§8).
3. Archived path without `aurora: archive`, or vice versa (§9).
4. Broken relative links between documents (§4).
5. Activities with `status: active` and no ledger mention since the last
   `reflected` entry (§10).

A consumer MUST NOT refuse to read a bucket with errors; a producer MUST
NOT add to one without flagging them. Recovery is always possible: the
ledger is append-only and the bucket is a git repository.
````

- [ ] **Step 2: Verify structure and closed vocabularies**

Run: `grep -cE '^## ([0-9]|1[01])\. ' SPEC.md`
Expected: `12` (numbered sections 0–11)

Run: `grep -A11 '^| Aurora |' SPEC.md | grep -c '^| \`'`
Expected: `8`

Run: `grep -o 'created., .converted., .classified., .indexed., .moved., .promoted., .archived., .restructured., .shipped., .reflected., .noted' SPEC.md | wc -l | awk '{print ($1>=1) ? "OK" : "FAIL"}'`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add SPEC.md
git commit -m "spec: documents, aurora, ledger, sources, index, archive, metabolism, conformance (SPEC 4-11)"
```

---

### Task 4: Example bucket — skeleton, BUCKET.md, LEDGER.md

**Files:**
- Create: `examples/crazy-ones/BUCKET.md`
- Create: `examples/crazy-ones/LEDGER.md`
- Create: `examples/crazy-ones/inbox/.gitkeep`
- Create: `examples/crazy-ones/sources/.gitkeep` (removed in Task 5 when content lands)
- Create: `examples/crazy-ones/library/.gitkeep` (removed in Task 5)
- Create: `examples/crazy-ones/activities/.gitkeep` (removed in Task 6)
- Create: `examples/crazy-ones/workbench/.gitkeep` (removed in Task 6)
- Create: `examples/crazy-ones/output/.gitkeep` (removed in Task 6)

**Interfaces:**
- Consumes: SPEC §§2, 3, 6 (Tasks 2–3).
- Produces: the fixture bucket `examples/crazy-ones/` — Phase 2's pytest golden files run `fusion check` (expect exactly 0 errors, 0 warnings), `fusion index`, `fusion status` against this path. The ledger seeds every one of the 11 verbs at least once across Tasks 4–6 so Phase 2 can parse-test the full vocabulary.

- [ ] **Step 1: Create the zone skeleton**

```bash
mkdir -p examples/crazy-ones/{inbox,sources,library,activities,workbench,output}
touch examples/crazy-ones/{inbox,sources,library,activities,workbench,output}/.gitkeep
```

- [ ] **Step 2: Write `examples/crazy-ones/BUCKET.md`**

```markdown
---
name: crazy-ones
kind: studio
description: A fictional one-person studio — music, gear, and one album that refuses to be reasonable.
fusion_version: "1.0"
created: 2026-07-10
inbox_max_age_days: 7
reflection_cadence: weekly
---

This is the example bucket for the Fusion Convention — a small fictional
studio run by someone recording an album at night. Everything in it is
invented; everything in it is conformant. Use it to see the convention in
motion, or to test an implementation against.

## Conventions

### Rules

- Instruments are filed one document per instrument: `make-model-year` slug.
- Recording sessions are logged weekly, never per-take.

### Delegations

- The librarian may archive dormant explore-aurora documents without asking.
```

- [ ] **Step 3: Write `examples/crazy-ones/LEDGER.md`**

```markdown
# Ledger

## 2026-07-08
- 09:00 · bertrand · created · BUCKET.md — "bucket born"
- 09:05 · claude · created · library/recipes/tape-echo-settings.md
- 10:12 · claude · converted · sources/gear/pedalboard-inventory.csv → library/instruments/pedalboard.md
- 10:13 · claude · classified · library/instruments/pedalboard.md — "type: instrument, aurora: library"
- 10:15 · claude · indexed · library/ (3 documents)
- 11:00 · bertrand · created · activities/lp-first-light/plan.md

## 2026-07-09
- 08:30 · claude · created · library/instruments/jazzmaster-1962.md
- 08:31 · claude · indexed · library/ (3 documents)
- 09:00 · bertrand · noted · workbench/liner-notes-draft.md — "half-baked on purpose"
- 18:00 · claude · moved · activities/demo-ep/plan.md → activities/archive/demo-ep/plan.md
- 18:00 · claude · archived · activities/archive/demo-ep/plan.md — "shipped in June, resting now"
- 18:05 · claude · indexed · activities/ (2 documents)

## 2026-07-10
- 09:40 · bertrand · promoted · workbench/press-kit-draft.md → output/press-kit.md
- 09:41 · claude · shipped · output/press-kit.md — "data_sources cited"
- 10:00 · claude · restructured · library/ (flat files → instruments/ + recipes/) — "taxonomy stopped serving"
- 10:30 · claude · reflected · bucket — "first reflection: 0 stale, 1 archived activity, conventions updated"
```

- [ ] **Step 4: Verify against SPEC**

Run: `ls examples/crazy-ones/ | sort | tr '\n' ' '`
Expected: `BUCKET.md LEDGER.md activities inbox library output sources workbench `

Run: `for v in created converted classified indexed moved promoted archived restructured shipped reflected noted; do grep -q "· $v ·" examples/crazy-ones/LEDGER.md || echo "MISSING $v"; done; echo DONE`
Expected: `DONE` (no MISSING lines — all 11 verbs present)

- [ ] **Step 5: Commit**

```bash
git add examples/crazy-ones/
git commit -m "example: crazy-ones bucket skeleton, identity card, ledger with all 11 verbs"
```

---

### Task 5: Example bucket — sources, manifest, library knowledge

**Files:**
- Create: `examples/crazy-ones/sources/MANIFEST.md`
- Create: `examples/crazy-ones/sources/gear/pedalboard-inventory.csv`
- Create: `examples/crazy-ones/library/INDEX.md`
- Create: `examples/crazy-ones/library/instruments/jazzmaster-1962.md`
- Create: `examples/crazy-ones/library/instruments/pedalboard.md`
- Create: `examples/crazy-ones/library/recipes/tape-echo-settings.md`
- Delete: `examples/crazy-ones/sources/.gitkeep`, `examples/crazy-ones/library/.gitkeep`

**Interfaces:**
- Consumes: SPEC §§4, 5, 7, 8; ledger entries from Task 4 (paths must match exactly).
- Produces: three conformant library documents (one with `source:`, one with `resource:`), a manifest with a real sha256, a hand-written INDEX exactly matching the format `fusion index` must reproduce in Phase 2 (golden-file test).

- [ ] **Step 1: Write `examples/crazy-ones/sources/gear/pedalboard-inventory.csv`**

```csv
position,pedal,role,notes
1,tuner,utility,always first
2,compressor,dynamics,slow attack for jangle
3,overdrive,gain,low gain stacking
4,tape echo,time,the sound of the record
5,reverb,space,plate setting only
```

- [ ] **Step 2: Compute the hash and write `examples/crazy-ones/sources/MANIFEST.md`**

Run: `shasum -a 256 examples/crazy-ones/sources/gear/pedalboard-inventory.csv | cut -c1-16`
Then write the manifest using the real first-16 hash from that output in place of `<HASH16>`:

```markdown
# Manifest

| file | added | by | sha256 | library |
|---|---|---|---|---|
| gear/pedalboard-inventory.csv | 2026-07-10 | claude | <HASH16> | library/instruments/pedalboard.md |
```

- [ ] **Step 3: Write `examples/crazy-ones/library/instruments/jazzmaster-1962.md`**

```markdown
---
title: Jazzmaster 1962
type: instrument
aurora: library
tags: [guitars, offsets, vintage]
created: 2026-07-09
updated: 2026-07-09
resource: https://en.wikipedia.org/wiki/Fender_Jazzmaster
---

## Summary

A 1962 Fender Jazzmaster in sunburst — provenance, setup, and service
history. The album's rhythm voice; strung with flatwound 11s.

---

## Provenance

Bought in 2019 from a jazz player who never bent a string in forty years.
All original except the bridge.

## Setup

- Strings: flatwound 11–48
- Action: 1.8mm at the 12th
- Bridge: replacement Mastery, original in the case

## Service history

| Date | Work |
|---|---|
| 2024-03 | Fret polish, full setup |
| 2026-01 | New bone nut |

Used with the [pedalboard](pedalboard.md) and the
[tape echo recipe](../recipes/tape-echo-settings.md).
```

- [ ] **Step 4: Write `examples/crazy-ones/library/instruments/pedalboard.md`**

```markdown
---
title: Pedalboard
type: instrument
aurora: library
tags: [gear, signal-chain]
created: 2026-07-08
updated: 2026-07-10
source: sources/gear/pedalboard-inventory.csv
---

## Summary

The current pedalboard: five pedals, one job — the sound of the record.
Converted from the gear inventory spreadsheet.

---

## Signal chain

| # | Pedal | Role | Notes |
|---|---|---|---|
| 1 | Tuner | utility | always first |
| 2 | Compressor | dynamics | slow attack for jangle |
| 3 | Overdrive | gain | low gain stacking |
| 4 | Tape echo | time | the sound of the record |
| 5 | Reverb | space | plate setting only |

Settings detail for the echo lives in
[tape-echo-settings](../recipes/tape-echo-settings.md).
```

- [ ] **Step 5: Write `examples/crazy-ones/library/recipes/tape-echo-settings.md`**

```markdown
---
title: Tape Echo Settings
type: recipe
aurora: library
tags: [effects, recording]
created: 2026-07-08
updated: 2026-07-08
---

## Summary

The three echo settings used across the album — slapback, dotted-eighth,
and the long self-oscillating tail on the title track.

---

## Slapback

Repeat rate 11 o'clock, intensity 9 o'clock, echo volume noon.

## Dotted eighth

Set against the click at 120 BPM; repeat rate marked with tape on the dial.

## The tail

Intensity past 3 o'clock until it sings, ride the repeat rate by hand.
Used once, on purpose, at the end of
[the LP plan](../../activities/lp-first-light/plan.md) tracklist.
```

- [ ] **Step 6: Write `examples/crazy-ones/library/INDEX.md`**

```markdown
<!-- generated by fusion index — do not edit -->
# Library Index

## instruments/

- [Jazzmaster 1962](instruments/jazzmaster-1962.md) — A 1962 Fender Jazzmaster in sunburst — provenance, setup, and service (library)
- [Pedalboard](instruments/pedalboard.md) — The current pedalboard: five pedals, one job — the sound of the record. (library)

## recipes/

- [Tape Echo Settings](recipes/tape-echo-settings.md) — The three echo settings used across the album — slapback, dotted-eighth, (library)
```

- [ ] **Step 7: Remove placeholder keeps and verify**

```bash
rm examples/crazy-ones/sources/.gitkeep examples/crazy-ones/library/.gitkeep
```

Run: `grep -L '^## Summary' examples/crazy-ones/library/*/*.md; echo CHECKED`
Expected: `CHECKED` (no files listed — every document is summary-first)

Run: `grep -h '^aurora:' examples/crazy-ones/library/*/*.md | sort -u`
Expected: `aurora: library`

Run: `grep -c '<HASH16>' examples/crazy-ones/sources/MANIFEST.md || true`
Expected: `0` (real hash substituted)

- [ ] **Step 8: Commit**

```bash
git add -A examples/crazy-ones/
git commit -m "example: sources with manifest, three library documents, generated-format index"
```

---

### Task 6: Example bucket — activities, workbench, output

**Files:**
- Create: `examples/crazy-ones/activities/INDEX.md`
- Create: `examples/crazy-ones/activities/lp-first-light/plan.md`
- Create: `examples/crazy-ones/activities/archive/demo-ep/plan.md`
- Create: `examples/crazy-ones/workbench/liner-notes-draft.md`
- Create: `examples/crazy-ones/output/press-kit.md`
- Delete: `examples/crazy-ones/activities/.gitkeep`, `examples/crazy-ones/workbench/.gitkeep`, `examples/crazy-ones/output/.gitkeep`

**Interfaces:**
- Consumes: SPEC §§4, 5, 8, 9; ledger paths from Task 4 (must match exactly).
- Produces: an active activity (`status: active`, `aurora: focus`), an archived one proving §9 (path `activities/archive/…` + `aurora: archive` + `status: done`), a rule-free workbench file, an output document with `data_sources`. Completes the fixture: after this task the bucket exercises every SPEC §4 field at least once.

- [ ] **Step 1: Write `examples/crazy-ones/activities/lp-first-light/plan.md`**

```markdown
---
title: LP — First Light
type: plan
aurora: focus
tags: [album, recording]
created: 2026-07-08
updated: 2026-07-10
status: active
---

## Summary

The first album: ten tracks, recorded at night, mixed on weekends.
Tracking through September, mix in October, out when it's right.

---

## Tracklist (working)

1. First Light
2. Round Pegs
3. No Respect for the Status Quo
4. Ericeira
5. The Tail *(the self-oscillating one)*

## Sessions

Weekly, logged here per the bucket rules:

| Week | Done |
|---|---|
| 2026-W28 | Drums for 1–3 |

Gear references: [Jazzmaster](../../library/instruments/jazzmaster-1962.md),
[tape echo settings](../../library/recipes/tape-echo-settings.md).
```

- [ ] **Step 2: Write `examples/crazy-ones/activities/archive/demo-ep/plan.md`**

```markdown
---
title: Demo EP
type: plan
aurora: archive
tags: [demo]
created: 2026-05-02
updated: 2026-07-09
status: done
---

## Summary

Four-track demo EP, shipped in June to exactly eleven listeners. Archived —
it did its job: it taught us what the album is not.

---

## What it taught

- Slapback on everything is a phase, not a sound.
- The Jazzmaster is the record.
```

- [ ] **Step 3: Write `examples/crazy-ones/activities/INDEX.md`**

```markdown
<!-- generated by fusion index — do not edit -->
# Activities Index

## lp-first-light/

- [LP — First Light](lp-first-light/plan.md) — The first album: ten tracks, recorded at night, mixed on weekends. (focus)

## archive/demo-ep/

- [Demo EP](archive/demo-ep/plan.md) — Four-track demo EP, shipped in June to exactly eleven listeners. Archived — (archive)
```

- [ ] **Step 4: Write `examples/crazy-ones/workbench/liner-notes-draft.md`**

```markdown
liner notes — draft zero, no rules in the workbench

here's to the takes we kept by accident
the hum we mixed in because it was honest
(figure out how to thank the ocean without sounding like a greeting card)
```

- [ ] **Step 5: Write `examples/crazy-ones/output/press-kit.md`**

```markdown
---
title: Press Kit — First Light
type: press-kit
aurora: collab
tags: [album, press]
created: 2026-07-10
updated: 2026-07-10
data_sources: [activities/lp-first-light/plan.md, library/instruments/jazzmaster-1962.md]
---

## Summary

One-page press kit for the First Light album: the story, the sound, the
gear that made it. Built from the LP plan and the instrument documents.

---

## The story

Recorded at night in a studio by the ocean, on a 1962 Jazzmaster and a
tape echo with opinions.

## The sound

Flatwounds, slow compression, plate reverb only. One self-oscillating
tail, used once, on purpose.

## Contact

studio@crazy-ones.example
```

- [ ] **Step 6: Remove keeps and verify**

```bash
rm examples/crazy-ones/activities/.gitkeep examples/crazy-ones/workbench/.gitkeep examples/crazy-ones/output/.gitkeep
```

Run: `grep '^status:' examples/crazy-ones/activities/lp-first-light/plan.md examples/crazy-ones/activities/archive/demo-ep/plan.md`
Expected: `…lp-first-light/plan.md:status: active` and `…demo-ep/plan.md:status: done`

Run: `grep '^aurora:' examples/crazy-ones/activities/archive/demo-ep/plan.md`
Expected: `aurora: archive` (path is truth, aurora is signal — §9 agreement)

Run: `grep -c 'data_sources:' examples/crazy-ones/output/press-kit.md`
Expected: `1`

- [ ] **Step 7: Commit**

```bash
git add -A examples/crazy-ones/
git commit -m "example: active + archived activities, workbench draft, output with data_sources"
```

---

### Task 7: Phase-1 QA gate — full conformance sweep

**Files:**
- None created — this task is the gate. Fix-in-place anything it catches, amend the relevant file, and note the fix in the commit.

**Interfaces:**
- Consumes: everything from Tasks 2–6.
- Produces: a verified-conformant fixture and spec — the precondition Phase 2's golden tests assume (`fusion check examples/crazy-ones` must report 0 errors / 0 warnings on first run).

- [ ] **Step 1: Sweep — every SPEC §11 error rule against the fixture**

```bash
cd examples/crazy-ones
# E1: all zones present
ls -d inbox sources library activities workbench output >/dev/null && echo E1-OK
# E2: BUCKET.md required fields
for f in name kind description fusion_version created; do grep -q "^$f:" BUCKET.md || echo "E2-FAIL $f"; done; echo E2-DONE
# E3+E4: every document has title/type/aurora, aurora in the eight
find library activities output -name '*.md' ! -name 'INDEX.md' | while read -r d; do
  for f in title type aurora; do grep -q "^$f:" "$d" || echo "E3-FAIL $f $d"; done
  grep '^aurora:' "$d" | grep -Eq 'commitments|focus|ops|collab|life|explore|archive|library' || echo "E4-FAIL $d"
done; echo E34-DONE
# E5: summary-first
find library activities output -name '*.md' ! -name 'INDEX.md' -exec grep -L '^## Summary' {} + ; echo E5-DONE
# E6: ledger verbs all valid
grep '·' LEDGER.md | grep -Ev '· (created|converted|classified|indexed|moved|promoted|archived|restructured|shipped|reflected|noted) ·' ; echo E6-DONE
# E7: sources all manifested
find sources -type f ! -name 'MANIFEST.md' ! -name '.gitkeep' | while read -r s; do grep -q "${s#sources/}" sources/MANIFEST.md || echo "E7-FAIL $s"; done; echo E7-DONE
# E8: filenames lowercase-hyphen
find library activities output -name '*.md' | grep -E '[A-Z_ ]' | grep -v INDEX ; echo E8-DONE
cd ../..
```

Expected: every marker line ends `-OK` or `-DONE` with **no** `FAIL` lines and **no** filenames printed by E5/E6/E8.

- [ ] **Step 2: Sweep — the warning rules (W3, W4)**

```bash
cd examples/crazy-ones
# W3: archive path <-> aurora agreement
find library activities -path '*archive*' -name '*.md' ! -name 'INDEX.md' -exec grep -L '^aurora: archive' {} + ; echo W3-DONE
# W4: relative links resolve
grep -rhoE '\]\((\.\./)*[a-z0-9/-]+\.md\)' library activities output --include='*.md' | tr -d '()]' | sort -u
cd ../..
```

Expected: `W3-DONE` with no files listed; for W4, manually confirm each printed path resolves from its containing document's directory (5 links expected: pedalboard.md, tape-echo-settings ×2, jazzmaster + plan cross-links).

- [ ] **Step 3: Spec ↔ fixture cross-read**

Read `SPEC.md` top to bottom with the fixture open beside it. For each of §§2–9, confirm the fixture demonstrates the rule (zone shape, BUCKET.md fields + Conventions, all document fields exercised, all 11 verbs, manifest with hash, INDEX marker + grammar, archive agreement). Fix any drift in the fixture — the spec wins.

- [ ] **Step 4: Commit the gate**

```bash
git add -A
git commit -m "qa: phase-1 conformance gate — spec/fixture sweep clean" --allow-empty
```

(`--allow-empty` so the gate leaves a mark even when nothing needed fixing.)

---

### Task 8: README manifesto + roadmap with phase gates

**Files:**
- Create: `README.md`
- Create: `docs/ROADMAP.md`

**Interfaces:**
- Consumes: SPEC.md, the fixture, the design spec.
- Produces: the public face (README links: `SPEC.md`, `examples/crazy-ones/`, `docs/specs/…`, `docs/ROADMAP.md`) and the phase-gate definitions Phases 2–4 must pass.

- [ ] **Step 1: Write `README.md`**

```markdown
# Fusion

**A file-based working environment for humans and their AI colleagues.**

Here's to the ones who drown in legacy documents — the spreadsheets, the
PDFs, the decks, the mail threads — and decided the filing cabinet was the
problem, not them. Fusion is not a document-management system, not a PKM,
not another note app. It refuses the category.

> **The human judges, the AI operates, the files remember.**

## What it is

- **Buckets** — your life-domains (personal, studio, each company) as
  separate git repos. Private by construction. A tiny hub registers them.
- **Markdown + frontmatter, everywhere** — three required fields (`title`,
  `type`, `aurora`), summary-first, plain relative links. Readable by any
  human, any agent, forever.
- **Aurora** — eight words for what a thing means for your attention:
  commitments, focus, ops, collab, life, explore, archive, library. An
  attention system, not a taxonomy. It's what makes this calm instead of a
  hoard.
- **The librarian owns the library.** You never file. The AI colleague
  places, names, curates, restructures — and signs every act in an
  append-only ledger. Ownership with a paper trail.
- **The metabolism** — buckets reflect, prune, and learn. What a bucket
  learns lands in its conventions; trust widens through explicit, recorded
  delegations.

## How it's built

Three layers: a **convention** ([SPEC.md](SPEC.md) — the actual product),
a small **CLI** (`fusion` — the notary: ledger, registers, hub, checks,
your cross-bucket day), and a **skill family** (the judgment: intake,
librarian, planner, analyst) for any agent that reads
[Agent Skills](https://agentskills.io) — Claude Code, Pi, Goose, and
whatever comes next.

See it in motion: [`examples/crazy-ones/`](examples/crazy-ones/) — a
fictional studio bucket, fully conformant, ledger and all.

## Status

| Phase | What | State |
|---|---|---|
| 1 | The Convention + example bucket | ✅ this repo |
| 2 | The `fusion` CLI | in design |
| 3 | The skill family | in design |
| 4 | Dogfood + release | in design |

Design spec: [docs/specs/2026-07-10-fusion-design.md](docs/specs/2026-07-10-fusion-design.md)
· Roadmap & QA gates: [docs/ROADMAP.md](docs/ROADMAP.md)

## Lineage

Fusion is the deliberate synthesis of four systems — Google's
[OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog), and
Bluewaves' Athena, Gizmo, and Shaping Room — keeping from each the one
thing it got right. The full argument lives in the design spec.

## License

[MIT](LICENSE.md). The spec is the contribution; the tools are reference
implementations. Rewrite them in anything — buckets that follow the
convention are Fusion.
```

- [ ] **Step 2: Write `docs/ROADMAP.md`**

```markdown
# Fusion Roadmap & QA Gates

Four phases. Each ends at a gate; no phase starts before the previous
gate is green. Each gate closes with an improvement loop: what the phase
taught goes into the next phase's plan (and, where it changes the
convention, into a versioned SPEC amendment).

## Phase 1 — Foundation (the Convention)

**Ships:** SPEC.md 1.0 · examples/crazy-ones fixture · README · this roadmap.

**Gate:**
- [ ] Full conformance sweep of the fixture against SPEC §11 — zero
      errors, zero warnings (mechanical, scripted in the phase plan).
- [ ] Spec ↔ fixture cross-read — every SPEC §2–9 rule demonstrated.
- [ ] Fresh-eyes read of SPEC.md for contradiction and ambiguity.

## Phase 2 — The CLI (the notary)

**Ships:** `fusion` as a uv tool — new, hub, log, index, check, status,
today, agenda; `--json` everywhere; `--since` on status/log.

**Gate:**
- [ ] `fusion check examples/crazy-ones` → 0 errors, 0 warnings.
- [ ] `fusion index` regenerates the fixture's INDEX files byte-identical
      (golden-file test).
- [ ] pytest suite green; every SPEC §11 rule has a failing-fixture test
      proving detection.
- [ ] Round-trip: `fusion new` a scratch bucket → log all 11 verbs →
      check green → status/today/agenda sane.
- [ ] Docs: `--help` complete for all 8 commands; README Status updated.

## Phase 3 — The skill family (the judgment)

**Ships:** fusion-intake, fusion-librarian, fusion-planner, fusion-analyst
— agentskills.io-compliant, self-contained, byte-identical conventions copy.

**Gate:**
- [ ] Duplication check green (conventions copies byte-identical).
- [ ] Each skill exercised on a scratch bucket; every scenario leaves
      `fusion check` green and the ledger correctly signed.
- [ ] Intake gate proven on real legacy formats (xlsx, docx, pdf, csv).
- [ ] Skills reviewed against the writing-skills quality bar.

## Phase 4 — Dogfood + release (the life)

**Ships:** two real buckets (personal + pro), first reflection cycles,
open-source readiness.

**Gate:**
- [ ] `fusion today` composes a real morning correctly across buckets.
- [ ] One full reflection cycle per bucket: proposals → judgment →
      conventions updated → `reflected` signed.
- [ ] A week of real use; frictions recorded and triaged.
- [ ] Open-source pass: no personal paths, install-from-clean-machine
      test, README truthful.

## The improvement loop (all phases)

At every gate: run the phase's checks · record what the phase taught ·
fold lessons into the next plan · amend the spec only through a versioned
change. The system that tells its users to reflect, reflects.
```

- [ ] **Step 3: Verify links resolve**

Run: `for f in SPEC.md LICENSE.md examples/crazy-ones docs/specs/2026-07-10-fusion-design.md docs/ROADMAP.md; do test -e "$f" || echo "BROKEN $f"; done; echo LINKS-OK`
Expected: `LINKS-OK` with no `BROKEN` lines

- [ ] **Step 4: Commit**

```bash
git add README.md docs/ROADMAP.md
git commit -m "docs: README manifesto and roadmap with phase QA gates"
```

---

## Self-review (performed at plan-writing time)

1. **Spec coverage:** design-spec §§1–4, 5 (formats), 7, 8 (layout/license), 9 (fixture), 12 → Tasks 1–8 ✓. CLI behavior, skills, real buckets are Phases 2–4 by decomposition. Gaps: none for Phase 1 scope.
2. **Placeholders:** one deliberate token — `<HASH16>` in Task 5 — with the exact command that produces its replacement; verification step proves substitution happened. No TBDs elsewhere.
3. **Consistency:** ledger paths in Task 4 match files created in Tasks 5–6 (`press-kit-draft.md` is promoted → only `press-kit.md` exists in output; `liner-notes-draft.md` stays in workbench; `demo-ep` exists only under `activities/archive/`) ✓. Aurora vocabulary and 11 verbs identical across SPEC, fixture, and constraints ✓. INDEX grammar identical in SPEC §8 and both fixture INDEX files ✓.
