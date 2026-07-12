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
  `output/` MAY additionally hold non-markdown deliverable files (exports);
  their filenames MUST still be lowercase-hyphen slugs (≤60 characters
  before the extension) with a lowercase extension.
- `workbench/` — no rules. Half-baked work belongs here. Leaving workbench
  (promotion) is a deliberate, ledger-logged act.
- Fusion holds knowledge and work, never media or code. Big binaries and
  repositories stay in their native homes; documents point to them
  (`resource:`, §4).
- Containers (`.athena`, `.zip`) are delivery vehicles, not originals:
  fusion-intake unpacks one and discards it at admit; the members become
  the originals. A container committed anywhere in the bucket is a
  conformance warning (§11 W6) — worst in `inbox/`, where it means a
  delivery that should have been unpacked and discarded is lingering
  instead.

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
| `resource` | URI or path of a thing this document describes but does not contain | anywhere |
| `status` | `active` \| `done` \| `dormant` | activities only |
| `due` | ISO 8601 date the thing falls due — `fusion agenda` surfaces it | anywhere |
| `data_sources` | YAML list of bucket paths this was built from | output only |

`updated` SHOULD reflect content changes only; moves, renames, and
restructures do not bump it.

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
append-only, chronological, and has exactly one writer: the ledger tool (reference implementation: `fusion log`).
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
- `verb` is one of the CLOSED set of eleven: `created`, `converted`, `classified`, `indexed`, `moved`, `promoted`, `archived`, `restructured`, `shipped`, `reflected`, `noted`. `noted` is the escape hatch; `reflected` signs off a reflection cycle (§10).
- `restructured` entries SHOULD carry a note with the justification —
  ownership means showing your reasons.

A bucket that lives on more than one machine merges parallel work with
git's built-in union driver: the reference scaffold writes a
`.gitattributes` at bucket birth marking `LEDGER.md merge=union` (and
the manifest, §7), so entries appended on both machines survive the
merge. The merged ledger may hold two headings for the same
date — consumers already tolerate this (liberal reader); it is the
honest record of parallel work. A union merge is the only way LEDGER.md
bytes change outside the one writer.

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
- On multi-machine buckets the manifest merges with the same union
  driver as the ledger (§6): rows admitted on two machines both survive.

## 8. INDEX.md

`library/INDEX.md` and `activities/INDEX.md` are GENERATED files
(reference implementation: `fusion index`) giving one-page triage before opening anything. They MUST
carry the marker and MUST NOT be hand-edited:

```markdown
<!-- generated by fusion index — do not edit -->
# Library Index

## instruments/

- [Jazzmaster 1962](instruments/jazzmaster-1962.md) — A 1962 Fender Jazzmaster in sunburst — provenance, setup, and service (library)
- [Pedalboard](instruments/pedalboard.md) — The current pedalboard: five pedals, one job — the sound of the record. (library)
```

Entry grammar: `- [<title>](<relative-path>) — <summary first line> (<aurora>)`.

Generation rules, so two implementations produce identical bytes: each
section heading is a document's parent directory path relative to the zone
root, with a trailing `/`; sections are ordered alphabetically, except
sections under `archive/` which sort last (alphabetical among themselves);
entries within a section are ordered alphabetically by relative path;
documents at the zone root come first, under a `./` heading. The summary
text is the first non-blank physical line of the document's `## Summary` section,
verbatim. An INDEX is *stale* when regeneration would produce different
bytes.

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

Exemptions: registers are not documents — `MANIFEST.md` is exempt from
E7's coverage requirement and `INDEX.md` from E8's filename rule (both are
upper-case precisely so they stand apart) — and dotfiles such as
`.gitkeep` are invisible to E7, E8, and W1. Non-markdown deliverables in
`output/` are exempt from E8's `.md` requirement — their stems MUST still
be slug-shaped; they are not documents, so E3–E5 never apply to them.

**Warnings** (drift, not damage):

1. Inbox files older than `inbox_max_age_days` (§2).
2. INDEX.md stale or missing (§8).
3. Archived path without `aurora: archive`, or vice versa (§9).
4. Broken relative links between documents (§4).
5. Activities with `status: active` and no ledger mention between the two
   most recent `reflected` entries (§10) — an activity untouched across a
   full reflection window. Buckets that have never reflected do not trigger
   this warning; after the first reflection the window runs from the
   bucket's birth. Activities whose first ledger mention postdates the
   window are exempt — a thing born after the reflection has not yet lived
   through one.
6. A container file (`.athena`, `.zip`) tracked anywhere in the bucket
   (§2) — a delivery vehicle left behind in `inbox/` instead of being
   unpacked and discarded, or a sealed archive committed elsewhere whose
   content belongs unpacked in `sources/` and `library/`.
7. A tracked file exceeding 95MB — GitHub's hard push limit is 100MB, and
   a bucket that crosses it becomes unpushable.
8. A document that is only a summary — nothing beneath the `---` line
   that closes it (§4) — and whose frontmatter carries neither `source:`
   nor `resource:`. Pointer documents are exempt: a converted scan's
   designed shape IS summary + pointer. A warning, not an error: whether
   a stub deserves to exist is operator judgment, and a stub that
   carries boilerplate text is a semantic call no checker should fake.

W6 and W7 stay warnings, not errors: a bucket MUST remain usable offline
even mid-drift, and both are caught before they cause damage, not after.

A consumer MUST NOT refuse to read a bucket with errors; a producer MUST
NOT add to one without flagging them. Recovery is always possible: the
ledger is append-only and the bucket is a git repository.
