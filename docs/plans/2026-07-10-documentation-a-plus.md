# Documentation A+ Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Take the doc corpus from a strong B to A+: fix every Critical/Important finding from the 2026-07-10 five-lens documentation audit (cold-read, truthfulness, consistency, agent-operator, presentation) — an honest front door, a navigable docs tree, a drift-free conventions card, and skill docs precise enough that two cold agents act identically.

**Architecture:** Six tasks, docs-only except one code docstring. Tasks 1–3 fix the human-facing tier (README, GETTING-STARTED, docs/ navigation, CONTRIBUTING). Tasks 4–6 fix the agent-facing tier (conventions card ×4, intake truth pass, skill boundaries). No SPEC.md changes — every fix aligns docs TO the spec/code, never the reverse.

**Tech Stack:** Markdown. Verification via the existing gates: `cd cli && uv run --group dev pytest -q` (135), `uv run fusion check ../examples/crazy-ones` (0/0), intake suite (77), librarian suite (22).

## Global Constraints

1. Work on `main`, one commit per task, never push.
2. `examples/crazy-ones/` content files are byte-frozen — never touch them. (`examples/README.md` is a doc, editable.)
3. `SPEC.md` is untouched — no spec change was approved for this plan.
4. The four `skills/*/references/fusion-conventions.md` must stay byte-identical to each other after every task (`cd cli && uv run --group dev pytest tests/test_skill_family.py -q` green).
5. Single-writer registers are never edited; no personal paths (`/Users/…`) in any committed file.
6. Voice: match the corpus register — declarative, warm-but-terse, no exclamation marks, hand-wrapped ~76 chars in prose files that already wrap.
7. Every relative link added must resolve; every task ends with the fixture check green.
8. Human decisions already made (2026-07-10, recorded here as binding): skip/reject = delete from inbox + `noted`; activity archiving belongs to fusion-planner's close; trigger disambiguation = bucket guard only (no trigger renames); CONTRIBUTING.md = yes, short, spec-first model.

---

### Task 1: README + cli/README — the front door

**Files:**
- Modify: `README.md`
- Modify: `cli/README.md`

- [ ] **README: bucket-anatomy diagram.** Insert after the `## What it is` bullet list (currently ends line 28, before `## How it's built`), a new section:

````markdown
## The shape of a bucket

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

Six zones, two registers, one shape in every bucket forever. The full
anatomy: [SPEC.md §2](SPEC.md).
```` 

(The tree is byte-identical to the one in the conventions card and SPEC §2 — keep it so.)

- [ ] **README: direct-link the two layers.** In `## How it's built` (lines 32–37), link the CLI and skills to their READMEs. Replace:

```markdown
Three layers: a **convention** ([SPEC.md](SPEC.md) — the actual product),
a small **CLI** (`fusion` — the notary: ledger, registers, hub, checks,
your cross-bucket day), and a **skill family** (the judgment: intake,
librarian, planner, analyst) for any agent that reads
```

with:

```markdown
Three layers: a **convention** ([SPEC.md](SPEC.md) — the actual product),
a small **[CLI](cli/README.md)** (`fusion` — the notary: ledger, registers,
hub, checks, your cross-bucket day), and a
**[skill family](skills/README.md)** (the judgment: intake, librarian,
planner, analyst) for any agent that reads
```

- [ ] **README: inline quickstart.** Replace the `## Get started` section body (lines 43–45: "Two moves — install the CLI, copy the skills — then make your first bucket. The walkthrough: …") with:

````markdown
```bash
git clone https://github.com/bluewaves-creations/fusion.git
uv tool install ./fusion/cli                       # move one — the CLI
cp -r fusion/skills/fusion-* ~/.agents/skills/     # move two — the skills
fusion new ~/buckets/personal --kind personal \
  --description "Home base: admin, health, house, money."
fusion today
```

Ten minutes, no wizard. The walkthrough:
[docs/GETTING-STARTED.md](docs/GETTING-STARTED.md).
````

- [ ] **README: docs map.** Insert a new section between `## Lineage` and `## License`:

```markdown
## Docs map

| Doc | What |
|---|---|
| [SPEC.md](SPEC.md) | The convention — normative, versioned, the actual product |
| [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md) | Ten-minute walkthrough |
| [examples/README.md](examples/README.md) | A finished bucket to wander |
| [cli/README.md](cli/README.md) | The CLI, command by command |
| [skills/README.md](skills/README.md) | The four skills |
| [docs/README.md](docs/README.md) | The rest: design rationale, roadmap, build records |
| [CONTRIBUTING.md](CONTRIBUTING.md) | The spec is the contribution |

`SPEC.md` is the contract — root, stable name, changes rarely and only
versioned. `docs/specs/` holds the dated design rationale behind it — the
argument, not the contract.
```

(The `docs/README.md` and `CONTRIBUTING.md` rows point at files Task 3 creates — Tasks 1 and 3 are both in this plan, so the final tree resolves; if executing out of order, note it and continue.)

- [ ] **README: define "the librarian" at first use.** Line 23 currently opens `**The librarian owns the library.**` before the term is introduced. Change that bullet's opening to: `**The librarian — your AI colleague wearing its curator hat — owns the library.**` and drop the now-redundant "The AI colleague" from the next sentence: "You never file. It places, names, curates, restructures — and signs every act in an append-only ledger."
- [ ] **cli/README: honest install.** Replace the `## Install` block (lines 8–12):

````markdown
## Install

From a clone (PyPI publication lands with Phase 4):

```sh
git clone https://github.com/bluewaves-creations/fusion.git
uv tool install ./fusion/cli
fusion --version
```

Once published: `uv tool install fusion-cli`.
````

- [ ] Verify: every link added resolves from its file's directory; `cd cli && uv run fusion check ../examples/crazy-ones` → 0 errors, 0 warnings.
- [ ] Commit: `docs: the front door earns its job — anatomy at a glance, quickstart inline, honest install`

### Task 2: GETTING-STARTED + skills/README — the walkthrough speaks

**Files:**
- Modify: `docs/GETTING-STARTED.md`
- Modify: `skills/README.md`

- [ ] **Prerequisites tell the whole truth.** In `## What you need` (lines 8–12): add a `git` line and extend the LibreOffice line. The list becomes:

```markdown
- [uv](https://docs.astral.sh/uv/) — installs and runs the CLI.
- `git` — every bucket is its own repo; `fusion new` runs `git init` and
  the first commit for you (and only warns if git is missing).
- An agent that reads [Agent Skills](https://agentskills.io) — Claude Code,
  Pi, Goose, or whatever comes next.
- Optional: LibreOffice (`soffice` on PATH) — only fusion-intake's
  docx/pptx/legacy-office/html route needs it.
```

- [ ] **Show the words.** In `## Live in it`, after the paragraph ending "You judge; it operates; the files remember." (line 68), insert:

````markdown
It looks like this:

```
You:    process the inbox
Agent:  Intake report — 3 files.
        contract.pdf     → new        converting
        brochure.pdf     → duplicate  auto-skipped (exact)
        q1-report.xlsx   → updated    supersede q1-report.xlsx — confirm?
You:    yes
Agent:  Admitted, converted, ledger signed, fusion check green.
```

"Process the inbox", "run intake", "archive this", "what's on my plate",
"report on X" — plain words; the skills know their triggers.
````

- [ ] **Reorder "Where to go next"** (lines 81–86) so the example precedes the spec:

```markdown
- [A finished bucket to wander](../examples/README.md) — see the
  convention instantiated before you read it abstract.
- [The convention itself](../SPEC.md) — SPEC.md is the actual product.
- [The CLI, command by command](../cli/README.md).
- [The four skills](../skills/README.md).
```

- [ ] **Troubleshooting block.** Insert a new section between `## Live in it` and `## Where to go next`:

```markdown
## When something goes wrong

- `fusion: command not found` — install from the clone
  (`uv tool install ./fusion/cli`); PyPI publication lands with Phase 4.
- `fusion check` is red — every code (E1–E8 errors, W1–W5 warnings) is
  defined in [SPEC.md §11](../SPEC.md); the message names the file. And a
  bucket is a git repo: `git diff` shows what changed, `git checkout`
  undoes it. Nothing is unrecoverable.
- `git` was missing when you ran `fusion new` — the bucket scaffolded
  without a repo; install git, then `git init && git add -A && git commit`
  inside the bucket.
```

- [ ] **skills/README: scoped glob + honest requirement.** Replace line 18's `cp -r skills/* ~/.agents/skills/        # or your agent's skills directory` with `cp -r skills/fusion-* ~/.agents/skills/   # or your agent's skills directory` (the bare `*` also copies this README into the skills dir). In the Requirements paragraph (line 21), replace `` (`uv tool install fusion-cli`) `` with `` (from a clone: `uv tool install ./fusion/cli`) ``.
- [ ] Verify links resolve; fixture check 0/0.
- [ ] Commit: `docs: the walkthrough shows the words — prerequisites, a transcript, a way out of trouble`

### Task 3: docs/ index, records honesty, CONTRIBUTING

**Files:**
- Create: `docs/README.md`
- Create: `CONTRIBUTING.md`
- Modify: `docs/specs/2026-07-10-fusion-design.md` (header only)
- Modify: `docs/ROADMAP.md` (one line)
- Modify: `examples/README.md` (one sentence)

- [ ] **docs/README.md** (new):

```markdown
# The docs tree — a map

Start at the repository [README](../README.md); the convention itself is
[SPEC.md](../SPEC.md). This folder holds everything else:

| Where | What | Read it when |
|---|---|---|
| [GETTING-STARTED.md](GETTING-STARTED.md) | The ten-minute walkthrough | You're new |
| [ROADMAP.md](ROADMAP.md) | Phases and their QA gates | You want the state of things |
| [specs/](specs/) | Dated design rationale — the argument behind SPEC.md | You want the *why* |
| [plans/](plans/) | Implementation plans, task by task | You're archaeologizing a change |
| [acceptance/](acceptance/) | Signed phase-gate evidence | You want proof, not claims |
| [dogfood/](dogfood/) | The live-use protocol + frictions log | You want to see the loop run |

`plans/`, `acceptance/`, and `dogfood/` are the engineering record — dated
(`YYYY-MM-DD-…`), append-mostly, never guides. They show how the thing was
built and verified; nothing in them is needed to *use* Fusion.
```

- [ ] **Design spec header stops claiming pre-implementation.** In `docs/specs/2026-07-10-fusion-design.md:4`, replace `**Status:** Approved design, pre-implementation` with `**Status:** Approved design — implemented through Phase 3; kept as the dated rationale behind [SPEC.md](../../SPEC.md) (see [ROADMAP](../ROADMAP.md) for live state)`.
- [ ] **ROADMAP ships what it shipped.** Line 47: replace `**Ships:** two real buckets (personal + pro),` with `**Ships:** real buckets (it turned out to be three: personal, bluewaves, ocean-way),` — the Evidence block below it already names all three.
- [ ] **examples/README: scope the "don't edit".** Line 6, replace `Wander it; don't edit it.` with `Wander it; don't edit it — the freeze is this fixture's, not a rule of Fusion (your own buckets are yours to edit, INDEX.md aside).`
- [ ] **CONTRIBUTING.md** (new, repo root):

```markdown
# Contributing

The spec is the contribution. Fusion is a convention first
([SPEC.md](SPEC.md)); the CLI and skills in this repository are reference
implementations. That shapes what contributing means here:

## Amend the convention

SPEC.md changes rarely, and only through a versioned change: open an issue
stating the problem the current convention causes (real usage evidence
beats taste), the amendment lands with a version bump and a line in the
spec's history. Vocabulary sets (auroras, ledger verbs, error codes) are
closed on purpose — the bar for widening them is high.

## Improve the reference tools

Bug fixes and capability work on the CLI (`cli/`) and skills (`skills/`)
are welcome as pull requests. House rules: TDD (the suites are the spec's
teeth), `fusion check examples/crazy-ones` stays at zero errors and zero
warnings, the four `references/fusion-conventions.md` stay byte-identical,
and single-writer registers are never hand-edited — not even in tests.

## Rewrite it entirely

The intended fork: reimplement the tools in any language you like. Buckets
that follow the convention are Fusion, whether or not our tools ever touch
them. You don't need permission — but we'd love an issue telling us it
exists.
```

- [ ] Verify all new links resolve (docs/README.md links are relative to `docs/`); fixture check 0/0.
- [ ] Commit: `docs: a map for the tree, honest headers, and what contributing means here`

### Task 4: The conventions card learns `due` and what to do when blocked (×4, byte-identical)

**Files:**
- Modify: `skills/fusion-intake/references/fusion-conventions.md`
- Modify: `skills/fusion-librarian/references/fusion-conventions.md`
- Modify: `skills/fusion-planner/references/fusion-conventions.md`
- Modify: `skills/fusion-analyst/references/fusion-conventions.md`

All four edits identical — edit one, `cp` it over the other three, then verify identity.

- [ ] **`due` joins the optional fields.** In the `## The document format` bullet list, the Optional bullet currently reads:

```markdown
- Optional: `tags`, `created`/`updated` (ISO dates), `source` (path into
  `sources/`), `resource` (URI or bucket path of the thing this document
  describes), `status` (`active`|`done`|`dormant`, activities only),
  `data_sources` (paths list, output only).
```

Replace with:

```markdown
- Optional: `tags`, `created`/`updated` (ISO dates), `due` (ISO date the
  thing falls due — `fusion agenda` surfaces it), `source` (path into
  `sources/`), `resource` (URI or bucket path of the thing this document
  describes), `status` (`active`|`done`|`dormant`, activities only),
  `data_sources` (paths list, output only).
```

(This matches SPEC §4's optional-fields table — the card had a bug: it omitted `due` while its own CLI crib credits `fusion agenda` with surfacing dated items.)

- [ ] **A blocked operator knows the move.** Insert a new section between `## The CLI crib` and `## The four accountabilities`:

```markdown
## When you're blocked

- `fusion` not on PATH: stop and tell the human — the install is
  `uv tool install ./fusion/cli` from a clone of the Fusion repository.
  Never imitate the notary by hand: no register writes while the CLI is
  missing.
- `fusion check` red and you cannot fix it: stop, show the findings
  verbatim, leave the bucket as it stands, and sign nothing that claims
  the work is done. A bucket is a git repo — nothing is unrecoverable.
- The human rejects a proposal: that is a result, not a failure. Record
  it if the gear's protocol says to (`noted`), and move on.
```

- [ ] Propagate: `cp skills/fusion-intake/references/fusion-conventions.md skills/fusion-librarian/references/ && cp skills/fusion-intake/references/fusion-conventions.md skills/fusion-planner/references/ && cp skills/fusion-intake/references/fusion-conventions.md skills/fusion-analyst/references/`
- [ ] Verify: `shasum skills/*/references/fusion-conventions.md` → one hash, four files; `cd cli && uv run --group dev pytest tests/test_skill_family.py -q` green; full CLI suite green (135); fixture 0/0.
- [ ] Commit: `skills: the card catches up to the spec — due exists, and a blocked operator knows the move`

### Task 5: Intake docs truth pass — six buckets, `--reconcile` named, every `noted` act has its line

**Files:**
- Modify: `skills/fusion-intake/scripts/gate.py` (docstring only — no behavior)
- Modify: `skills/fusion-intake/references/gate.md`
- Modify: `skills/fusion-intake/SKILL.md`

- [ ] **gate.py docstring counts its own output.** Lines 8–10 currently say "writes a gate manifest with four buckets: exact_dups, near_dups, update_candidates, clean_new." Replace that sentence with: "writes a gate manifest with six buckets: exact_dups, near_dups, update_candidates, clean_new, containers, inbox_dups." Run the intake suite (77) to prove no behavior change: `cd skills/fusion-intake && uv run --group dev pytest -q` (or the repo's established invocation — check `tests/`; the count must not drop).
- [ ] **gate.md intro matches its own protocol sections.** Lines 3–5: replace "with five buckets: `exact_dups`, `near_dups`, `update_candidates`, `clean_new`, `containers`." with "with six buckets: `exact_dups`, `near_dups`, `update_candidates`, `clean_new`, `containers`, `inbox_dups`."
- [ ] **SKILL.md pipeline diagram too.** Line 22 (`│        four buckets → gate-<runid>.json`): replace `four buckets` with `six buckets`.
- [ ] **Skip/reject gets mechanics (human decision 2026-07-10: delete + `noted`).** In gate.md:
  - In the `**near_dups**` paragraph (lines 59–61), append: "A confirmed skip deletes the file from `inbox/` and signs it: `fusion log noted "skipped <name> (near-duplicate of <source>): <the human's words>" --bucket <root> --as <you>` — nothing lives in inbox, not even a rejected guest."
  - In the `**Contradiction detection**` paragraph (lines 50–57), after "reject (skip)", add "(delete from `inbox/` + `noted`, same line as a near-dup skip)".
- [ ] **Every `noted` act shows its literal line.** In gate.md:
  - `**inbox_dups**` paragraph (lines 27–30): after "(delete, signed with a `noted` ledger line)", add the template: `` `fusion log noted "inbox duplicate deleted: <name> (same bytes as <kept>)" --bucket <root> --as <you>` ``.
  - `**containers**` paragraph (lines 63–69): after "sign the act `noted`", add: `` `fusion log noted "unpacked inbox/<name> → inbox/<stem>/ (<n> members; container discarded)" --bucket <root> --as <you>` ``.
- [ ] **`--reconcile` is named where updates are worked.** 
  - gate.md `## After confirmation` (lines 93–96): replace "`prepare` targets the existing document (`--dest`/`--slug` set to its current path pieces) and the reconciliation edits that document in place." with "`prepare` targets the existing document — pass `--reconcile` plus `--dest`/`--slug` set to its current path pieces (without `--reconcile`, prepare refuses to touch an existing document) — and the reconciliation edits that document in place."
  - SKILL.md step 3 invocation (line 69): change to `` `uv run <skill>/scripts/convert.py prepare --bucket <root> --source <cat>/<name> [--dest …] [--slug …] [--type …] [--aurora …] [--reconcile]` `` and append to that step's text: "`--reconcile` (with the existing doc's `--dest`/`--slug`) is the confirmed-update path — prepare refuses an existing destination without it."
  - SKILL.md "Supersede, the Fusion way" paragraph (lines 95–100): after "RECONCILES the existing library document in place", add "(`prepare --reconcile`)".
- [ ] **The four classes read as four at a glance.** SKILL.md lines 83–89: relabel the two duplicate rows `duplicate — exact` and `duplicate — near`, and add directly under the table: "Four classes — `duplicate` splits into exact (auto-skip) and near (ask)."
- [ ] Verify: intake suite green (77), fixture 0/0, `grep -c "noted" skills/fusion-intake/references/gate.md` shows the new templates present.
- [ ] Commit: `fusion-intake: docs tell the whole truth — six buckets, --reconcile named, every noted act has its line`

### Task 6: Skill boundaries — the bucket guard, one owner per act

**Files:**
- Modify: `skills/fusion-intake/SKILL.md` (frontmatter + body)
- Modify: `skills/fusion-librarian/SKILL.md` (frontmatter + body)
- Modify: `skills/fusion-planner/SKILL.md` (frontmatter + body)
- Modify: `skills/fusion-analyst/SKILL.md` (frontmatter + body)
- Modify: `skills/fusion-librarian/references/archive.md`
- Modify: `skills/fusion-librarian/references/create.md`
- Modify: `skills/fusion-planner/references/horizon.md`

- [ ] **Bucket guard in all four descriptions (human decision 2026-07-10: guard, no trigger renames).** Append to each SKILL.md frontmatter `description`, before the closing quote, the same sentence: ` Applies only inside a Fusion bucket — a directory tree with BUCKET.md and LEDGER.md at its root; if there is no such bucket in play, this skill does not apply.` (Watch YAML: the descriptions are double-quoted scalars; keep them single-line.)
- [ ] **Bucket guard in all four bodies.** Each SKILL.md has an early paragraph instructing "read the bucket's `BUCKET.md`" (intake lines 14–16; the other three have their equivalent). Append to that paragraph, in each: "No `BUCKET.md` up the tree and none named? Stop — this is not a Fusion bucket, and no Fusion skill applies (`fusion hub` lists the real ones)."
- [ ] **Activities archive through the planner (human decision 2026-07-10).** In `skills/fusion-librarian/references/archive.md`:
  - Step 3: replace `Edit its frontmatter: `aurora: archive` (and `status: done` for an activity, if not already).` with `Edit its frontmatter: `aurora: archive`.`
  - Replace the final paragraph (`Whole activities archive as a folder: …`) with: `Activities are the planner's: closing or archiving one is fusion-planner's close gear (it also writes the final Log line in plan.md). This gear archives library/ and output/ documents.`
  - Insert a new step between current steps 2 and 3: `Repair what pointed at it: run `uv run <skill>/scripts/link-repair.py scan --bucket <root>` and apply exact-confidence repairs per the sweep protocol in [cross-reference.md](cross-reference.md) (or a standing delegation); fuzzy always asks.` Renumber the following steps.
- [ ] **Librarian routing table follows.** In `skills/fusion-librarian/SKILL.md`, the gear table's `archive` row trigger words currently include activity phrasing (`done with this`); change that row's trigger cell to `archive / put away (documents — a finished *activity* closes via fusion-planner)` — keep the row's gear/reference columns unchanged.
- [ ] **create.md checks for a twin first.** In `skills/fusion-librarian/references/create.md`, append to step 1: `Before writing, triage `library/INDEX.md` for an existing document on the same subject — extending or reconciling one beats creating a twin; when a candidate exists, propose the edit instead and let the human choose.`
- [ ] **horizon.md batches its flips honestly.** In `skills/fusion-planner/references/horizon.md` step 4, after the per-flip `fusion log noted …` template, add: `(several flips confirmed in one pass may share one `noted` line naming them all)`.
- [ ] Verify: `cd cli && uv run --group dev pytest tests/test_skill_family.py -q` green (frontmatter still parses, card identity holds); intake 77, librarian 22, CLI 135; fixture 0/0.
- [ ] Commit: `skills: a bucket guard on every door, one owner per act — the cold agent acts like the warm one`

---

## Acceptance (after all six)

- All suites green at their current counts (CLI 135, intake 77, librarian 22); `fusion check examples/crazy-ones` 0/0; conventions card one hash × four files.
- Link sweep: every relative link in every modified/created doc resolves.
- Cold-read re-test: dispatch a fresh reader over README → GETTING-STARTED → examples → SPEC and confirm the audit's two Criticals are gone (install command honest everywhere; the literal words to say to the agent are on the page).
- Operator re-test: a fresh agent reading only fusion-intake's docs can state, without reading code: the six gate buckets, the `--reconcile` invocation, and the exact ledger line for a skipped near-dup.
- Sync the installed copies: `cp -r skills/fusion-* ~/.agents/skills/` (description changes need an agent restart to re-trigger).

## Non-goals (dispositioned, not forgotten)

- `examples/crazy-ones/sources/MANIFEST.md`'s 16-hex short hash: spec-legal (§7, "first 8+ hex chars minimum"); the fixture freeze outweighs a cosmetic ellipsis.
- Badges on README: a taste call, deliberately not made here.
- `SPEC.md:242`'s long line and any SPEC rewrap: SPEC is untouched by this plan.
- Shaping Room's own trigger vocabulary: out of scope; owner plans to retire those skills.
