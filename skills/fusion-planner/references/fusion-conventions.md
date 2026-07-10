# The Fusion Conventions — operator's card

> Carried byte-identical by all four Fusion skills. SPEC.md in the Fusion
> repository is normative; this card is the working summary. When they
> disagree, SPEC.md wins and this card has a bug.

**The contract:** the human judges, the AI operates, the files remember.

**Liberal reader, strict writer.** Never refuse to read a bucket because
something is missing or unknown. Never write into `library/`, `activities/`,
`output/`, or a register without satisfying every rule below first.

## The bucket

```
<bucket>/
├── BUCKET.md        # identity card + learned conventions
├── LEDGER.md        # append-only collaboration record
├── inbox/           # drop zone — things arrive, nothing lives here
├── sources/         # immutable originals + MANIFEST.md
├── library/         # settled knowledge — documents
├── activities/      # live work — documents + status
├── workbench/       # ephemeral human+AI space — NO format rules
└── output/          # finished deliverables — documents
```

- `sources/` is immutable: never modify, rename, or delete a registered file.
- `workbench/` has no rules; leaving it (promotion) is a deliberate,
  ledger-logged act.
- Fusion holds knowledge and work, never media or code — documents point
  (`resource:`) at big things, they never swallow them.

## Before acting — always

1. Read `BUCKET.md`: the identity card, then `## Conventions` — `### Rules`
   are how this bucket works; `### Delegations` are your standing autonomy
   grants. They bind you.
2. Triage through `library/INDEX.md` and `activities/INDEX.md` plus document
   summaries before opening bodies.

## The document format

Every `.md` in `library/`, `activities/`, `output/` (except INDEX.md):

```markdown
---
title: Human-readable name
type: what-it-is        # open vocabulary, curated per bucket
aurora: library         # one of the eight — closed set
---

## Summary

Two or three lines a human or agent reads in two seconds.

---

Full body. Cross-links are plain relative markdown links.
```

- Required: `title`, `type`, `aurora` — exactly three.
- Optional: `tags`, `created`/`updated` (ISO dates), `source` (path into
  `sources/`), `resource` (external URI), `status` (`active`|`done`|`dormant`,
  activities only), `data_sources` (paths list, output only).
- Body MUST be summary-first: `## Summary`, the lines, a `---` separator,
  then everything else.
- Filenames: lowercase, hyphen-separated, `.md`, stem ≤60 chars.
- Preserve frontmatter keys you don't recognize.

## Aurora — the eight (closed)

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

Aurora says what a document means for the human's attention — never invent
a ninth value.

## Archive

No archive zone: archived items move to an `archive/` subfolder inside their
zone AND take `aurora: archive`. Path is the truth, aurora is the signal —
both, always.

## The registers — single writers, no exceptions

| File | Only writer | Your move |
|---|---|---|
| `LEDGER.md` | `fusion log` | `fusion log <verb> "<object>" [--note "…"] --as <you>` |
| `library/INDEX.md`, `activities/INDEX.md` | `fusion index` | run it after any add/move/edit that changes titles or summaries |
| `sources/MANIFEST.md` | fusion-intake's `scripts/convert.py` | everything enters `sources/` through the intake gate |

Never edit these three files by hand — not with an editor tool, not with
shell. The ledger verbs (closed set of eleven): `created`, `converted`,
`classified`, `indexed`, `moved`, `promoted`, `archived`, `restructured`,
`shipped`, `reflected`, `noted`. Sign with your agent name (`--as claude`,
or set `FUSION_ACTOR`).

## The CLI crib

| Command | What it does |
|---|---|
| `fusion new <path>` | scaffold a conformant bucket |
| `fusion hub [add\|remove]` | list / register / retire buckets |
| `fusion log <verb> <object>` | append a signed ledger entry |
| `fusion index` | regenerate INDEX files (logs `indexed` when changed) |
| `fusion check [path]` | conformance: errors, warnings, honest exit codes |
| `fusion status [--since …]` | one bucket at a glance |
| `fusion today` | the composed morning across all hub buckets |
| `fusion agenda` | dated + active items across buckets |

All take `--json`. `--since last-reflection` scopes to the current
reflection window. **Exit gate for every skill scenario: `fusion check`
green before you call the work done.**

## The four accountabilities

| Skill | Owns |
|---|---|
| fusion-intake | The gate. Everything that enters, enters through it. |
| fusion-librarian | The order. Placement, curation, restructuring, reflection. |
| fusion-planner | The horizon. Activities, agendas, what today looks like. |
| fusion-analyst | The output. Deliverables that cite their sources. |

One skill, one accountability — the ledger says which hat was worn.
