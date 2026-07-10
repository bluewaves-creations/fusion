# Fusion — Design Specification

**Date:** 2026-07-10
**Status:** Approved design, pre-implementation
**Format version target:** fusion 1.0

---

## What Fusion is

Fusion is a file-based working environment for Human + AI collaboration — knowledge,
activities, and their shared record — living entirely in markdown on a filesystem,
operable by any capable agent (Claude Code, Pi, Goose) and by the human directly.

It is built for people who deal with legacy and external documents (office files,
PDFs, images, mails, messages) and who have embraced real Human + AI collaboration.
It is not a document-management system, not a PKM, not a note app. It refuses the
category.

**The centaur contract — the sentence the whole design serves:**

> The human judges, the AI operates, the files remember.

Every design decision below traces to one of those three verbs.

## Lineage

Fusion is the deliberate synthesis of four systems, keeping from each the one thing
it got right and refusing what made it non-portable:

| Parent | Kept | Refused |
|---|---|---|
| **OKF** (Google, open spec) | Minimal specified format; untyped cross-links; `resource:`; "the spec is the contribution"; liberal reading | Absence of validation; no in-file disclosure |
| **Athena** (Bluewaves app) | Fixed opinionated structure; the aurora system; archive convention (path is truth, aurora is signal); strict validation at the gate | The app; the envelope; UUID identity |
| **Gizmo NXT** (Bluewaves app) | The session/workbench idea; agent-as-colleague posture; the Dream (reflection & pruning), reborn as files | Runtime coupling; app-locked state |
| **Shaping Room V2** (Bluewaves designs) | doc-converter intake gate; immutable sources; summary-first disclosure; registers; workbench | Convention-only reliability (registers maintained by hope) |

## Founding concepts

1. **Think Different** (Apple, 1997) — "The ones who see things differently…
   because they change things. **We make tools for these kinds of people.**"
   Fusion refuses the filing-cabinet category and takes the toolmaker's posture.
   The tone throughout — spec, CLI voice, README — is rebel misfit: not boring
   AI, not consultant, not wellbeing coach, not tech nerd.
2. **7 Flows Synergy X** (Human-AI collaboration framework) — the centaur model,
   "AI is not a feature. It is a colleague." Fusion is the place where the seven
   flows happen on disk: Context (the bucket), Delegation (skills), Judgment
   (aurora — human meaning), Quality (registers), Memory (library + ledger),
   Trust (the ledger as transparent record), Scale (buckets).
3. **"Simplicity is the ultimate sophistication"** (da Vinci) — elegance as
   *achieved* excellence. Every essential component present from the first
   version, each in its purest sufficient form. The core represents the whole
   system from first design; simplicity is designed, never accreted.

---

## 1. Architecture — three layers

| Layer | Contains | Principle |
|---|---|---|
| **The Convention** | `SPEC.md`: bucket anatomy, document format, aurora, registers | Da Vinci — minimal, specified, pure |
| **The `fusion` CLI** | Mechanical invariants: scaffold, ledger, registers, hub, validation, agenda | Trust & Quality — facts are code-kept, never model-kept |
| **The skill family** | Judgment: intake conversion, classification, curation, planning, analysis | Delegation & Judgment — the AI colleague's competencies |

The split is the deepest lesson of the four parents: Athena and Gizmo are reliable
because *code* enforces their invariants; Shaping Room V2 needed an `audit` skill
because convention-following by a model is best-effort. Registers and the ledger —
the essentials — are exactly what drifts when maintained by hope. So: **code for
invariants, model for judgment.** The CLI is the notary, not the librarian.

The CLI is optional at read time. A bucket is 100% plain markdown — readable and
even writable without the CLI. The CLI makes writes to shared state (ledger,
registers, hub) atomic and correct. A scribe, not a gatekeeper.

## 2. Topology

```
~/Developer/fusion/          # the system: spec, CLI source, skills (one git repo)
~/.fusion/hub.md             # the hub: registry of buckets (tiny, human-readable markdown)
<anywhere>/<bucket>/         # each bucket: its own directory, its own git repo
```

- **Buckets are separate git repos** — full privacy and git isolation between
  companies; per-bucket permission posture for agents; multi-machine sync via
  private remotes.
- **The hub** registers name, path, kind, one-line description per bucket. An
  agent reads it to know the user's world; `fusion hub` maintains it. The hub is
  per-machine; registering is explicit and takes one command.
- **Buckets are few and bold** — a bucket is a life-domain with its own privacy
  boundary and its own ledger, not a hobby folder. Reference shape: `personal`,
  `studio` (creative), one bucket per company.
- **Day one: two real buckets** — one personal, one pro — proving hub,
  separation, and cross-bucket discovery immediately.

## 3. Bucket anatomy

Every bucket is the same shape — all zones present from day one, scaffolded by
`fusion new`:

```
<bucket>/
├── BUCKET.md        # identity card: name, kind (pro|personal|club|…), description + § Conventions (learned rules, standing delegations)
├── LEDGER.md        # append-only record of everything done here — by human or AI
├── inbox/           # drop zone — legacy files land here, nothing lives here
├── sources/         # immutable originals, preserved forever, out of the knowledge — with MANIFEST.md
├── library/         # settled knowledge — converted, classified, aurora-tagged markdown
├── activities/      # live work — agendas, plans, campaigns, training programs
├── workbench/       # the centaur's table — ephemeral human+AI collaboration, no format rules
└── output/          # finished deliverables — what leaves the bucket
```

**Lifecycle encoded by the zones:** things *arrive* (inbox) → are *preserved*
(sources) and *transformed* (library) → get *worked* (workbench, drawing on
library + activities) → and *ship* (output). The ledger watches all of it.

| Zone | Lineage | Decision |
|---|---|---|
| `inbox/` | Athena Inbox ≈ SR intake | Ephemeral by contract: `fusion check` flags inbox files older than 7 days (default, per-bucket configurable in BUCKET.md) |
| `sources/` | SR (immutable + MANIFEST) | Preserved, accessible, never polluting the knowledge |
| `library/` | SR library + Athena Library | Reference knowledge; summary-first documents |
| `activities/` | Athena Areas/Projects — the piece SR never had | Live, stateful work. Same document format plus `status`. The expandable zone: a new kind of activity is a new folder, not a new system |
| `workbench/` | SR workbench ≈ Athena Scratchpad ≈ Gizmo session | Zero format rules. Half-baked stays here; promotion out is deliberate and logged |
| `output/` | SR output | Deliverables with provenance (`data_sources`) |

**Archive — Athena's convention, adopted whole:** no archive zone. Archived items
move to an `archive/` subfolder *within their zone* (`library/archive/…`,
`activities/archive/…`) and take `aurora: archive`. **Path is the truth, aurora is
the signal.**

**Registers (code-kept facts):** `LEDGER.md` (root, append-only, written only by
`fusion log`), `sources/MANIFEST.md` (provenance of originals), `INDEX.md` in
`library/` and `activities/` (generated by `fusion index` — OKF-style one-page
triage before opening anything).

### The librarian principle

- **The agent owns the library.** Humans never file. They drop things in
  `inbox/`, create freely in `workbench/`, and *ask* for what they need. The
  librarian — the AI colleague wearing that hat — decides placement, naming,
  classification, structure. `library/` and its taxonomy are its domain; its
  INDEX is always current.
- **Ownership means accountability.** Every act of curation is a `fusion log`
  entry — the ledger is the librarian's signed register; `fusion check` is the
  audit it answers to.
- **Ownership means maintenance.** The librarian runs the reflection ritual
  (§7): the bucket is introspected, curated, pruned, and refined on a cadence —
  order that isn't maintained isn't owned.
- **Clean, bold, opinionated structure.** Few, strongly-named folders — no
  `misc/`, no fifteen half-overlapping categories. The librarian has the
  authority to say "this goes here" and to *restructure* when the taxonomy stops
  serving (a logged, justified act). A timid librarian breeds clutter; Fusion's
  librarian is not timid.
- **One owner of order, two owners of content.** The human drives activities
  (their work, their words); the librarian still owns their *order* — naming,
  folders, status hygiene, archiving — across the whole bucket.

## 4. Document format

One format everywhere in `library/`, `activities/`, and `output/`:

```markdown
---
title: Supplier Scorecard — Meridian Textiles
type: scorecard
aurora: ops
tags: [suppliers, textiles, q3]
created: 2026-07-10
updated: 2026-07-10
source: sources/audits/meridian-2026.xlsx    # when converted from an original
resource: https://…                           # when the doc describes an external thing
status: active                                # activities only: active | done | dormant
data_sources: [library/suppliers/meridian-textiles.md]   # output only: what it was built from
---

## Summary

Three lines a human or agent can read in two seconds and know
whether to open the rest.

---

Full content below the separator. Standard markdown. Cross-links are plain
relative paths: [the campaign](../activities/q3-campaign/plan.md).
```

**Decisions:**

- **Three required fields: `title`, `type`, `aurora`.** `type` says what a
  document *is* — open vocabulary, curated per bucket by the librarian (OKF's
  lesson: don't over-register). `aurora` says what it *means for the human's
  attention* — the closed eight. Everything else optional. Two axes of meaning,
  one of identity, stop.
- **Aurora** (from Athena/WaveData, verbatim): `commitments`, `focus`, `ops`,
  `collab`, `life`, `explore`, `archive`, `library`. An attention model, not a
  category taxonomy — it spans obligations through reference, work through life,
  and is what makes the system calm instead of a compulsive hoard. It is a
  cross-cutting lens *over* structure, never a replacement for it. **The eight
  are the eight** — not configurable.
- **Summary-first, always** — `## Summary`, then `---`, then the body (SR's
  within-file disclosure). With the generated INDEX files (between-file
  disclosure), an agent triages a bucket in two reads without opening a single
  full document.
- **Provenance is one field** — `source:` (a path into `sources/`); MANIFEST and
  git carry the rest. SR's four-field quartet collapses to one.
- **`resource:` (optional, from OKF)** — for documents that describe an external
  thing: an instrument, a production app, a Lightroom catalog, a code repo.
  Fusion documents are the knowledge layer over things that rightly live
  elsewhere.
- **Cross-links are plain relative markdown links** — untyped edges survive any
  move and render on GitHub. No wikilinks, no UUIDs, no app-isms.
- **Filenames:** lowercase-hyphenated slugs, `.md`, meaningful, ≤60 chars —
  librarian-enforced.

**Boundary, stated proudly: Fusion holds knowledge and work, never media or
code.** Photos, audio, repos stay in their native homes; Fusion references them
via links and `resource:`. The moment it tries to be a DAM or a monorepo, it dies
of obesity.

## 5. The ledger and the CLI

**The ledger is the collaboration record, not a changelog.** Git remembers what
bytes changed; the ledger remembers *what was done, by whom, and why*. One is
versioning; the other is trust between colleagues.

```markdown
## 2026-07-10
- 07:42 · claude · converted · sources/manuals/jazzmaster-1962.pdf → library/instruments/jazzmaster-1962.md
- 07:44 · claude · indexed · library/ (42 documents)
- 09:10 · bertrand · promoted · workbench/q3-draft.md → output/reports/q3-review.md
- 18:30 · pi · restructured · library/clients/ (merged emea/ + apac/ → by-account/) — "taxonomy stopped serving"
```

- **Append-only, chronological, one writer: `fusion log`.** No agent or human
  edits it by hand.
- **Entry: time · actor · verb · object, optional note.** Actor from
  `FUSION_ACTOR` env or `--as` — `claude`, `pi`, `goose`, the human. The
  centaur's two hands, distinguishable forever.
- **Closed verb set:** `created, converted, classified, indexed, moved,
  promoted, archived, restructured, shipped, reflected, noted`. Small and
  greppable so agents can reason over the record. `noted` is the escape hatch;
  `reflected` signs off a reflection cycle (§7).
- The librarian's accountability lives here: `restructured` entries carry the
  justification.

**The CLI — eight commands, no ninth:**

| Command | Does |
|---|---|
| `fusion new <path>` | Scaffold a complete bucket (all zones, registers, BUCKET.md) + register in hub |
| `fusion hub` | List / register / retire buckets |
| `fusion log …` | Append a ledger entry (the only writer) |
| `fusion index` | Regenerate `INDEX.md` in library/ and activities/ |
| `fusion check` | Audit a bucket: frontmatter validity, summary-first, naming, stale inbox, orphans, broken links, register drift |
| `fusion status` | One bucket at a glance: counts by aurora/type/status, recent ledger |
| `fusion today` | The cross-bucket day: active commitments and activities across the hub, grouped by aurora |
| `fusion agenda` | The wider horizon: everything dated or active, across the hub |

`fusion today` is the hub's reason to exist: a day spans buckets (training —
life; LP block — focus; client call — commitments; surf window — life), and only
the hub can compose it. Aurora is what makes the composition possible: eight
words that mean the same thing across the user's entire existence.

`fusion status` and `fusion log` accept `--since <date|last-reflection>` so
reflection cycles (§7) scope cleanly over the ledger.

**Implementation posture:** Python, installed as a uv tool. Dependencies near
zero (pyyaml and little else). No daemon, no database, no config beyond the hub
file — the buckets are the state. Every command offers `--json` (agents parse,
never scrape); exit codes honest so `fusion check` gates automation. Human output
carries the rebel voice; JSON stays deadpan.

**What the CLI refuses:** convert, classify, summarize, decide placement —
anything requiring judgment. That is the skill family's territory.

## 6. The skill family

Four skills, four accountabilities — self-contained per the
[agentskills.io](https://agentskills.io) standard, identical across Claude Code,
Pi, and Goose.

| Skill | Accountability | Lineage |
|---|---|---|
| **fusion-intake** | The gate. Everything that enters, enters through it. | doc-converter, elevated |
| **fusion-librarian** | The owner. Order, placement, retrieval, curation. | V2 librarian + the ownership principle |
| **fusion-planner** | The horizon. Activities: plans, campaigns, programs, agendas. | The piece none of the parents had |
| **fusion-analyst** | The output. Reports, assessments, exports that leave the bucket. | V2 analyst |

- **fusion-intake** — takes whatever lands in `inbox/` (xlsx, docx, pptx, pdf,
  csv, images, mails, message exports): preserve original in `sources/`
  (MANIFEST updated), convert to faithful summary-first markdown, propose
  `type` + `aurora`, hand to the librarian for placement, log, clear the inbox.
  Contract: **nothing enters the library except through the gate.**
- **fusion-librarian** — the accountable owner as a skill: queries, creation,
  tagging, cross-referencing, promotion from workbench, archiving, and its
  distinctive power — **restructuring**, executed and signed in the ledger with
  reasons. Also owns activity *hygiene* across `activities/`, and runs the
  **reflection ritual** (§7) — introspection, curation, pruning, and the
  maintenance of `BUCKET.md § Conventions`.
- **fusion-planner** — the human drives activities; the planner structures them:
  creates activities (folders + stateful documents with `status`, dates,
  aurora), keeps the horizon honest (stalled activities, expiring commitments,
  what `fusion today` shows tomorrow). Makes "expandable to agendas, plans,
  programs, campaigns" true with zero new machinery.
- **fusion-analyst** — turns library + activities into deliverables in
  `output/`: reports, assessments, comparisons, exports. Always cites
  `data_sources`, always logs `shipped`.

**The contract all four obey:**

1. Self-contained (no escapes, PEP 723 scripts run with `uv run`, no
   harness-specific variables).
2. All register/ledger writes go through the CLI — judgment proposes, `fusion`
   records.
3. The convention travels with them: each skill carries a byte-identical copy of
   the Fusion conventions reference (`check-duplication` discipline).
4. One skill, one accountability — the ledger says which hat was worn.

V2's audit became `fusion check`; scaffold became `fusion new`; workspace's
promote folds into the librarian. Six skills became four skills and a CLI.

## 7. The metabolism — reflection, learning, pruning

A system that only operates is a filing cabinet with better manners. Fusion
lives: **the files remember → the AI reflects → the human judges → the system
learns.** The loop needs no ninth command and no fifth skill — everything
required already exists; this section defines the ritual and the place where
learning lands.

### The Reflection

Per bucket, on a cadence suggested in BUCKET.md (weekly for hot buckets,
monthly for calm ones), triggered by the human or their agent's scheduler —
Fusion itself still refuses watchers. The librarian runs it:

1. **Introspect** — read `LEDGER.md` since the last reflection (`--since
   last-reflection`), run `fusion check` and `fusion status`. The ledger doubles
   as telemetry: what got converted, promoted, touched — and what never did.
2. **Curate & prune** — propose: stale workbench items (expire or promote),
   dormant activities (no ledger touch in N days → `dormant` or archive),
   superseded library docs → `archive/`, duplicates to merge, fat documents to
   split, summaries that no longer match their bodies, taxonomy that stopped
   serving.
3. **Judge** — proposals go to the human. Destructive and archival acts need a
   yes — except where standing delegation applies (below).
4. **Learn** — what the reflection taught lands in `BUCKET.md § Conventions`;
   the cycle signs off with a `reflected` ledger entry.

Episodic reflection reports are ephemeral (workbench); only conventions and
ledger entries persist.

### BUCKET.md § Conventions — where the system learns

A living section the librarian maintains: bucket-specific rules discovered
through operation — "scorecards are filed by supplier, not by date," "never
archive client contracts." The long-term memory of *how this bucket works*; the
ledger is the episodic memory of *what happened*. Every convention added or
changed is logged. Skills read § Conventions before acting — the system
genuinely behaves differently after it learns.

### The trust dial — standing delegations

Also in § Conventions: explicit grants — *"the librarian may archive dormant
explore-aurora docs without asking."* Trust between colleagues grows the way it
does between humans: earned, explicit, recorded, revocable. Synergy's Trust flow
made structural — delegation widens as the ledger proves reliability.

### Honest boundary

File-based reflection sees *actions*, not *reads* — no `accessCount` without an
app, and the app was refused. Fusion learns from what the centaur *did*, not
what it glanced at. That is the portable trade, stated proudly.

**Lineage:** this is Gizmo's Dream reborn as files — the pruner that ran in a
Core Data store becomes a ritual over a ledger anyone can read.

## 8. Installation & open-source posture

```
fusion/
├── README.md          # the manifesto — rebel voice
├── SPEC.md            # the Fusion convention, versioned — the actual product
├── cli/               # the fusion CLI (Python package, uv-native)
├── skills/            # fusion-intake · fusion-librarian · fusion-planner · fusion-analyst
├── examples/          # a complete example bucket — doubles as test fixture
└── docs/              # design docs, decisions
```

**Install — two moves, no wizard:**

1. `uv tool install fusion` (PyPI name availability to verify; `fusion-cli` as
   fallback).
2. Copy `skills/*` into the agent's skills directory. Standard-compliant skills
   need no installer; `cp -r` is the installer.

Then `fusion new <path>` and you're living in it.

- **MIT license.** The spec is the contribution; CLI and skills are the
  reference implementation. Someone could rewrite the CLI in Rust and their
  buckets would still be Fusion.
- No personal paths anywhere; installable by anyone from a clean machine.
- Spec versioned (`fusion_version` in BUCKET.md); spec changes rare and
  versioned.

## 9. Error posture — liberal reader, strict writer

- **Reading (OKF's lesson):** no tool ever rejects a bucket for missing optional
  fields, unknown types, or broken links. A half-migrated bucket is still a
  bucket.
- **Writing (Athena's lesson):** the intake gate and `fusion check` are strict
  *before* damage — invalid aurora, missing summary, orphan source caught at the
  gate, named loudly, never silently skipped.
- CLI: honest exit codes, locked appends, nothing destructive without
  `--force`. Append-only ledger + git = recovery always trivial.

## 10. Testing

- **CLI:** pytest golden-file suites — scaffold → index → check round-trips
  against `examples/`.
- **Skills:** every skill scenario must leave `fusion check` green — the check
  is the invariant oracle.
- **Dogfood:** the two day-one buckets are living fixtures. When `fusion today`
  composes a real morning correctly, v1 works.

## 11. What v1 refuses

| Refused | Why |
|---|---|
| App, server, daemon, database | The files are the system. Runtime coupling is how Gizmo became unportable. |
| Media storage, code hosting | `resource:` points; Fusion never swallows. Obesity is death. |
| Sync service | git is sync. Solved problem, not our problem. |
| Calendar/notification integrations | `fusion today` reads files. Integrations are v2 temptations. |
| Typed knowledge graph | Untyped links survive everything. Frontmatter extensibility leaves the door open. |
| Watchers/automation | Agent-invoked only. Nothing moves unless a colleague — human or AI — moves it. |
| Custom auroras | The eight are the eight. A configurable attention system is no system at all. |

## 12. Decisions log (from the brainstorm)

1. **Whole-system-first:** the core represents the complete system from first
   design — all zones, aurora, registers, buckets, expandability — each in its
   simplest sufficient form. No spine-then-layers.
2. **Buckets:** separate roots + hub (privacy/git isolation per company; hub for
   discovery).
3. **Lineage:** completely new system named **Fusion**, learning from the legacy
   siblings; dedicated `~/Developer/fusion` repo. Shaping Room V2 stays
   functional; a one-way importer can bring V2 workspaces in as buckets (post-v1).
4. **First buckets:** both personal and pro from day one.
5. **Architecture:** Approach B — convention + skills + small CLI for
   invariants. (A: pure convention — rejected, registers drift; C: app-backed —
   rejected, runtime coupling.)
6. **Adoptable by anyone; open-source intended. Tone: rebel misfit.**
7. **The agent is the librarian** — accountable owner of the library; clean bold
   opinionated structures.
8. **Life-scale test passed:** 3 companies + personal + studio = 5 buckets;
   `fusion today` and `resource:` added as consequences.
9. **The metabolism (user-identified gap):** the system must learn, introspect,
   improve, curate, prune, refine. Answered structurally — reflection ritual
   run by the librarian, `BUCKET.md § Conventions` as learning store, standing
   delegations as the trust dial, `reflected` verb — with no new command and no
   new skill.
