# Phase 3 — The Skill Family Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the four Fusion skills — fusion-intake, fusion-librarian, fusion-planner, fusion-analyst — agentskills.io-compliant, self-contained, carrying a byte-identical conventions reference, with the intake gate proven lossless on real legacy formats.

**Architecture:** Router skills in `skills/` at the repo root: each SKILL.md is a thin dispatcher; procedures live in `references/*.md` loaded on demand; deterministic work lives in PEP 723 scripts run with `uv run`. The skills hold the judgment; every fact-write goes through a code-kept single writer (`fusion log`, `fusion index`, or intake's own register script). fusion-intake elevates the legacy doc-converter's two-stage gate + two-stage conversion engine to the Fusion convention; fusion-librarian absorbs the legacy librarian's gears plus workspace's promote and the reflection ritual; fusion-planner is new; fusion-analyst adapts the legacy analyst.

**Tech Stack:** Markdown skills per the agentskills.io standard · Python ≥3.11 scripts with PEP 723 inline deps (PyYAML, openpyxl, pymupdf) via `uv run` · LibreOffice (`soffice`) for docx/pptx/legacy-office (fail-fast, declared in `compatibility:`) · pytest for script suites · the Phase-2 `fusion` CLI as the invariant oracle.

## Global Constraints

Copied from SPEC.md 1.0, the design spec §6, and standing project rules. Every task's requirements implicitly include this section.

1. **Exactly four skills** — `fusion-intake`, `fusion-librarian`, `fusion-planner`, `fusion-analyst` — in `skills/<name>/`. No fifth skill, no ninth CLI command.
2. **agentskills.io frontmatter whitelist:** only `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`. `name` MUST equal the directory name. `description` ≤1024 chars, imperative, with trigger phrases AND boundary lines against the sibling skills. `compatibility` ≤500 chars. SKILL.md body ≤500 lines. All paths inside a skill are relative; nothing reaches outside its own directory except the `fusion` binary and the bucket it operates on.
3. **The conventions card travels:** every skill carries `references/fusion-conventions.md`, byte-identical across all four (enforced by `cli/tests/test_skill_family.py`). The canonical copy is authored once in Task 1; later tasks copy it with `cp` — never retype it.
4. **Single writers (SPEC §6, §7, §8):** `LEDGER.md` is written ONLY by `fusion log`. `INDEX.md` ONLY by `fusion index`. `sources/MANIFEST.md` ONLY by fusion-intake's `scripts/convert.py`. Skills NEVER hand-edit these three files — not with Edit, not with Bash.
5. **Skills call the CLI as a binary** (`fusion …` on PATH); skill scripts never import the `fusion` Python package. In-repo tests may invoke it as `uv run --project cli fusion …` from the repo root.
6. **Closed sets, verbatim:** auroras = `commitments`, `focus`, `ops`, `collab`, `life`, `explore`, `archive`, `library` (eight, closed). Ledger verbs = `created`, `converted`, `classified`, `indexed`, `moved`, `promoted`, `archived`, `restructured`, `shipped`, `reflected`, `noted` (eleven, closed).
7. **Document rules (SPEC §4):** required frontmatter exactly `title`, `type`, `aurora`; body summary-first (`## Summary`, then a `---` line, then content); filenames `^[a-z0-9]+(?:-[a-z0-9]+)*\.md$`, stem ≤60 chars.
8. **`sources/` is immutable (SPEC §7):** files are never modified, renamed, or deleted after registration. A confirmed *update* admits a NEW source file and reconciles the existing library document in place (same path, content updated, `updated:` bumped, `source:` repointed) — never a source overwrite, never a `-v2` library twin.
9. **The lossless fidelity contract (fusion-intake):**
   - The original is preserved byte-identical in `sources/`, full sha256 in MANIFEST.
   - Vision paths: `page_count == len(pages)`; every page below 100 extracted chars is flagged `needs_vision` — silent-empty output is structurally impossible.
   - Tables: every row, every column — no column cap, no row sampling. Numbers verbatim, never paraphrased or rounded.
   - Figures get a one-line caption describing what they show.
   - An inbox file is deleted ONLY after: document written → MANIFEST `library` column linked → ledger signed → `fusion check` green. Doubtful fidelity (blurry scan, unreadable region) is flagged to the human and the file STAYS in inbox.
10. **Confirm-before-act (the gate's locked rule):** class `new` auto-proceeds; exact `duplicate` auto-skips (recorded); near-`duplicate`, `updated`, and `conflicting` STOP and ask. The gate never picks a winner in a factual conflict.
11. **Skills read `BUCKET.md ## Conventions` before acting** (SPEC §3 MUST) and honor `### Delegations` as standing autonomy grants.
12. **Scripts:** PEP 723 headers, `requires-python = ">=3.11"`, run with `uv run`. Dependency ceiling: PyYAML, openpyxl, pymupdf (intake); openpyxl (analyst export). Nothing else.
13. **License MIT, Copyright Bluewaves Boutique. No personal paths anywhere** — not in skills, tests, fixtures, or committed acceptance transcripts (scratch buckets live under `/tmp/`).
14. **`examples/crazy-ones` is normative and never mutated.** Skill exercises use scratch buckets created with `fusion new`.
15. **Voice:** rebel-light in SKILL.md prose (the Fusion register: "the gate", "the notary objects"); procedures themselves deadpan-crisp. No boring-AI filler.
16. Work on `main`, linear history, one commit per task, **never push**.
17. **Review lens for skill-authoring tasks (4, 6, 8, 9):** reviewers apply the writing-skills quality bar — description states what + when-to-use with trigger phrases and boundaries against sibling skills; body ≤500 lines with detail pushed to references loaded on demand; procedures concrete enough that a fresh agent needs no other context; guardrails stated as "never" rules. This satisfies ROADMAP gate line 4.

## What we elevate from the legacy skills (the lineage contract)

| Legacy | Kept in Phase 3 | Changed for Fusion |
|---|---|---|
| doc-converter gate (Stage 1 script) | sha256 hashing, filename normalization, 3-word-shingle Jaccard similarity, thresholds 0.85 near-dup / 0.30 update floor, four buckets, git-history evidence | Compares `inbox/` against `sources/`; manifest lands in `workbench/.intake/` |
| doc-converter gate (Stage 2 agent) | Four classes, identity guard ("never guess a supersede"), claim-by-claim conflict detection, intake-report-as-prompt-surface, confirm-before-act | Topic-match procedure inlined (reads INDEX.md + summaries — no cross-skill dependency); supersede semantics per Constraint 8 |
| doc-converter engine | Routing table (extractive / libreoffice / pdf_text / pdf_scanned), `TEXT_COVERAGE_MIN_CHARS = 100`, `RENDER_DPI = 150`, no-column-cap tables, cell sanitization, page-coverage invariant, fail-fast on missing soffice | 7-field legacy frontmatter → Fusion 3+2 (`title`/`type`/`aurora` + `source`/`created`); summary-first body; NEW paths: images, `.eml` mail, `.md`/`.txt` passthrough; admit step owns MANIFEST |
| librarian | Router pattern, query-as-safe-default, gear references, CHANGELOG discipline → ledger discipline, context-cost notices | CHANGELOG → `fusion log`; reindex → `fusion index`; research/translate/summarize/extract gears REFUSED in v1 (YAGNI — the design spec names query, creation, tagging, cross-referencing, promotion, archiving, restructuring, reflection) |
| workspace promote | Pre-flight explicit-invocation guard, validate-then-move, STOP on failed validation, one-sentence destructive plan | Validation = Fusion strict writer (3 fields, aurora valid, summary-first, filename); logs `promoted` via CLI |
| audit | — | Became `fusion check` in Phase 2; skills run it as their exit gate |
| analyst | report/assess/compare/export gears, citation discipline, `data_sources`, progressive disclosure, export.py stdin-JSON contract | Outputs are Fusion documents in `output/`; dashboard and timeline gears REFUSED in v1; logs `shipped` |

## Fixture and oracle facts (pinned)

- Repo root: the `fusion` repo (Phase 2 complete at `36a4306`). CLI lives in `cli/`, 90 tests green: `cd cli && uv run --group dev pytest -q`.
- CLI invocation from repo root: `uv run --project cli fusion <cmd>`. `fusion check <path>` exits 0 with `0 errors · 0 warnings — clean, carry on.` on a conformant bucket.
- `fusion new /tmp/<name> --kind <kind> --description "…" --as <actor>` scaffolds a conformant bucket (git repo, all zones, BUCKET.md, empty MANIFEST header, INDEX files, `created` ledger entry) and ALWAYS registers it in the hub (there is no `--no-register` flag). Tests and acceptance runs MUST sandbox the hub: `export FUSION_HUB=/tmp/<scratch>/hub.md` before any `fusion new`/`fusion hub` call, so the user's real `~/.fusion/hub.md` is never touched.
- Ledger entry grammar: `- HH:MM · <actor> · <verb> · <object>[ — "<note>"]` under `## YYYY-MM-DD` headings. `fusion log <verb> <object> [--note …] [--as <actor>]`.
- MANIFEST format (SPEC §7): header `# Manifest`, blank line, then a 5-column table `| file | added | by | sha256 | library |` with `|---|---|---|---|---|` separator. `file` is the path relative to `sources/`. `library` is `—` until converted. The Phase-2 reader is `cli/src/fusion/manifest.py::read()` — it skips the header and separator rows and strips cells.
- INDEX entry grammar: `- [<title>](<rel>) — <summary first line> (<aurora>)` with marker `<!-- generated by fusion index — do not edit -->`.
- The ` · ` in ledger/hub grammars is U+00B7 with spaces; ` — ` is U+2014 with spaces. Load-bearing.
- Actor resolution: `--as` > `FUSION_ACTOR` env > system user. Skills sign with their agent name (`claude`, `pi`, `goose`).

## File structure (what Phase 3 creates)

```
skills/
├── README.md                          # family overview + cp -r install (Task 1)
├── fusion-intake/
│   ├── SKILL.md                       # Task 4
│   ├── references/
│   │   ├── fusion-conventions.md      # Task 1 (canonical copy)
│   │   ├── gate.md                    # Task 4 — Stage-2 gate protocol
│   │   └── convert.md                 # Task 4 — Stage-2 conversion protocol + fidelity contract
│   ├── scripts/
│   │   ├── gate.py                    # Task 2 — Stage-1 deterministic classifier
│   │   └── convert.py                 # Task 3 — admit / prepare / link / cleanup
│   └── tests/
│       ├── conftest.py                # Task 2
│       ├── make_fixtures.py           # Task 3 — generates real xlsx/csv/pdf/docx/eml
│       ├── test_gate.py               # Task 2
│       ├── test_convert.py            # Task 3
│       └── test_integration.py        # Task 5
├── fusion-librarian/
│   ├── SKILL.md                       # Task 6
│   └── references/
│       ├── fusion-conventions.md      # cp from fusion-intake
│       ├── query.md · create.md · tag.md · cross-reference.md
│       ├── promote.md · archive.md · restructure.md · reflect.md
├── fusion-planner/
│   ├── SKILL.md                       # Task 8
│   └── references/
│       ├── fusion-conventions.md      # cp
│       ├── create-activity.md · horizon.md · close.md
└── fusion-analyst/
    ├── SKILL.md                       # Task 9
    ├── references/
    │   ├── fusion-conventions.md      # cp
    │   ├── report.md · assess.md · compare.md · export.md
    └── scripts/
        └── export.py                  # Task 9

cli/tests/test_skill_family.py         # Task 1 — duplication + structure gate
docs/acceptance/
├── 2026-07-10-phase-3-intake.md       # Task 5
├── 2026-07-10-phase-3-librarian.md    # Task 7
└── 2026-07-10-phase-3-planner-analyst.md  # Task 10
```

Test commands (used throughout):

```bash
# Skill-family structure gate (runs inside the existing CLI suite)
cd cli && uv run --group dev pytest tests/test_skill_family.py -v
# Intake script suite (self-contained; run from repo root)
uv run --with pytest --with pyyaml --with openpyxl --with pymupdf \
  pytest skills/fusion-intake/tests/ -v
```

---
### Task 1: Family scaffold — the conventions card, skills/README, and the structure gate

**Files:**
- Create: `skills/fusion-intake/references/fusion-conventions.md` (the canonical copy)
- Create: `skills/README.md`
- Test: `cli/tests/test_skill_family.py`

**Interfaces:**
- Produces: `skills/fusion-intake/references/fusion-conventions.md` — every later skill task copies this file byte-identically with `cp`. `cli/tests/test_skill_family.py` — dynamic discovery: validates every `skills/*/` directory that exists, so it stays green as Tasks 4–9 add skills.

- [ ] **Step 1: Write the canonical conventions card**

Write `skills/fusion-intake/references/fusion-conventions.md` with EXACTLY this content (it will be byte-compared across four copies — transcribe precisely):

````markdown
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
````

- [ ] **Step 2: Write skills/README.md**

```markdown
# The Fusion skill family

Four skills, four accountabilities. The CLI keeps the facts; these keep
the judgment.

| Skill | Accountability |
|---|---|
| [fusion-intake](fusion-intake/) | The gate — everything that enters, enters through it, losslessly. |
| [fusion-librarian](fusion-librarian/) | The owner — order, placement, curation, restructuring, reflection. |
| [fusion-planner](fusion-planner/) | The horizon — activities, agendas, an honest today. |
| [fusion-analyst](fusion-analyst/) | The output — deliverables that cite their sources and ship signed. |

## Install

Standard-compliant skills need no installer:

```bash
cp -r skills/* ~/.agents/skills/        # or your agent's skills directory
```

Requirements: the `fusion` CLI on PATH (`uv tool install fusion-cli`), `uv`
for the bundled scripts. fusion-intake additionally wants LibreOffice
(`soffice` on PATH) for docx/pptx/legacy office formats — it fails fast and
loud when missing, never silently degrades.

## The contract all four obey

1. Self-contained — agentskills.io standard, PEP 723 scripts via `uv run`,
   no harness-specific anything.
2. Judgment proposes, code records — every ledger/register write goes
   through its single writer (`fusion log`, `fusion index`, intake's
   register script).
3. The convention travels — each skill carries a byte-identical
   `references/fusion-conventions.md`.
4. One skill, one accountability — the ledger says which hat was worn.
```

- [ ] **Step 3: Write the failing structure test**

Create `cli/tests/test_skill_family.py`:

```python
"""The skill-family structure gate — duplication + agentskills.io compliance.

Dynamic discovery: validates every skills/<name>/ that exists, so the gate
holds from the first skill to the fourth without edits.
"""
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / "skills"
FRONTMATTER_WHITELIST = {
    "name", "description", "license", "compatibility", "metadata",
    "allowed-tools",
}
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def skill_dirs():
    if not SKILLS_DIR.is_dir():
        return []
    return sorted(
        p for p in SKILLS_DIR.iterdir()
        if p.is_dir() and (p / "SKILL.md").is_file()
    )


def parse_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path}: no frontmatter block"
    end = text.index("\n---", 4)
    import yaml
    fm = yaml.safe_load(text[4:end])
    assert isinstance(fm, dict), f"{path}: frontmatter is not a mapping"
    return fm


def test_at_least_one_skill_exists():
    assert skill_dirs(), "skills/ holds no skill directories yet"


@pytest.mark.parametrize("skill", skill_dirs(), ids=lambda p: p.name)
def test_frontmatter_compliance(skill):
    fm = parse_frontmatter(skill / "SKILL.md")
    unknown = set(fm) - FRONTMATTER_WHITELIST
    assert not unknown, f"non-standard frontmatter fields: {unknown}"
    assert fm["name"] == skill.name, "name must equal directory name"
    assert NAME_RE.match(fm["name"]), "name must be lowercase-hyphenated"
    assert len(fm["name"]) <= 64
    assert fm["description"].strip(), "description required"
    assert len(fm["description"]) <= 1024
    if "compatibility" in fm:
        assert len(fm["compatibility"]) <= 500


@pytest.mark.parametrize("skill", skill_dirs(), ids=lambda p: p.name)
def test_body_size(skill):
    lines = (skill / "SKILL.md").read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 500, f"SKILL.md is {len(lines)} lines (limit 500)"


@pytest.mark.parametrize("skill", skill_dirs(), ids=lambda p: p.name)
def test_carries_conventions_card(skill):
    assert (skill / "references" / "fusion-conventions.md").is_file(), (
        "every skill carries references/fusion-conventions.md"
    )


def test_conventions_cards_byte_identical():
    # Discovered independently of SKILL.md so the gate holds from Task 1,
    # when the canonical card exists before any SKILL.md does.
    cards = sorted(SKILLS_DIR.glob("*/references/fusion-conventions.md"))
    assert cards, "no conventions cards found"
    reference = cards[0].read_bytes()
    for card in cards[1:]:
        assert card.read_bytes() == reference, (
            f"{card} differs from {cards[0]} — the convention travels "
            "byte-identical or not at all"
        )


@pytest.mark.parametrize("skill", skill_dirs(), ids=lambda p: p.name)
def test_no_personal_paths(skill):
    for path in sorted(skill.rglob("*")):
        if path.is_file() and path.suffix in (".md", ".py"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert "/Users/" not in text and "bertrand" not in text.lower(), (
                f"{path}: personal path or name leaked"
            )
```

- [ ] **Step 4: Run the tests — expect the discovery test to pass and structure tests to run against fusion-intake only**

Run: `cd cli && uv run --group dev pytest tests/test_skill_family.py -v`
Expected: at this point `skills/fusion-intake/` holds only the conventions card (no SKILL.md yet), so `skill_dirs()` is empty: `test_at_least_one_skill_exists` FAILS (honest RED), the parametrized tests collect zero cases, and `test_conventions_cards_byte_identical` passes on the one card. To keep main releasable between tasks, mark the discovery test expected-to-fail — add this decorator to `test_at_least_one_skill_exists` and REMOVE it in Task 4:

```python
@pytest.mark.xfail(reason="first SKILL.md lands in Task 4", strict=True)
```

Re-run: `cd cli && uv run --group dev pytest tests/test_skill_family.py -v`
Expected: all green (1 xfailed, byte-identity passed, empty parameter sets skipped).

- [ ] **Step 5: Verify the whole CLI suite still passes**

Run: `cd cli && uv run --group dev pytest -q`
Expected: 90 prior tests + new ones, all passing.

- [ ] **Step 6: Commit**

```bash
git add skills/ cli/tests/test_skill_family.py
git commit -m "skills: family scaffold — conventions card, README, structure gate"
```

---
### Task 2: fusion-intake Stage-1 gate — the deterministic classifier

**Files:**
- Create: `skills/fusion-intake/scripts/gate.py`
- Create: `skills/fusion-intake/tests/conftest.py`
- Test: `skills/fusion-intake/tests/test_gate.py`

**Interfaces:**
- Produces: `gate.py` CLI — `uv run skills/fusion-intake/scripts/gate.py --bucket <root> [--out <path>]` → writes `workbench/.intake/gate-<runid>.json` (prints its path and counts). Manifest schema: `{"version": 1, "counts": {…}, "buckets": {"exact_dups": [], "near_dups": [], "update_candidates": [], "clean_new": []}}` — entries carry `incoming` (path relative to `inbox/`), and where relevant `matched_source` (relative to `sources/`), `similarity` (float), `history` (list of `{date, subject}`), `auto_skip` (bool).
- Consumes: nothing from other tasks. Adapted from the legacy doc-converter `gate.py` — thresholds and normalization preserved verbatim.

The lineage rules preserved exactly: `NEAR_DUP_THRESHOLD = 0.85`, `UPDATE_SIM_FLOOR = 0.30`, `SHINGLE_K = 3`, filename normalization (strip date prefix, lowercase, collapse separators), best-match over ALL sources (catches renamed near-dups), moderate-sim + name-match → update candidate, moderate-sim without name-match → near-dup for review. Changes for Fusion: hashing is always SHA-256 (no git-blob variant — freshly admitted files may be uncommitted, and MANIFEST pins sha256 anyway); the classifier scans `inbox/` against the `sources/` tree on disk, skipping `MANIFEST.md` and dotfiles; output defaults into `workbench/.intake/`.

- [ ] **Step 1: Write conftest.py — the scratch-bucket factory**

```python
"""Fixtures for the fusion-intake script suite. No fusion package imports —
the skill is self-contained; buckets are built by hand to SPEC 1.0."""
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

BUCKET_CARD = """---
name: {name}
kind: personal
description: Scratch bucket for intake tests.
fusion_version: "1.0"
created: 2026-07-10
---

Scratch bucket.

## Conventions

### Rules

### Delegations
"""

MANIFEST_HEADER = (
    "# Manifest\n\n| file | added | by | sha256 | library |\n"
    "|---|---|---|---|---|\n"
)

ZONES = ("inbox", "sources", "library", "activities", "workbench", "output")


@pytest.fixture
def bucket(tmp_path):
    root = tmp_path / "scratch"
    for zone in ZONES:
        (root / zone).mkdir(parents=True)
    (root / "BUCKET.md").write_text(
        BUCKET_CARD.format(name="scratch"), encoding="utf-8")
    (root / "LEDGER.md").write_text("# Ledger\n", encoding="utf-8")
    (root / "sources" / "MANIFEST.md").write_text(
        MANIFEST_HEADER, encoding="utf-8")
    return root


def drop(root: Path, name: str, content: str) -> Path:
    """Put a text file in inbox/."""
    p = root / "inbox" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def seed_source(root: Path, rel: str, content: str) -> Path:
    """Put a text file in sources/ (registration in MANIFEST is not the
    gate's concern — it compares against the tree on disk)."""
    p = root / "sources" / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p
```

- [ ] **Step 2: Write the failing tests**

```python
"""Stage-1 gate: deterministic classification of inbox/ against sources/."""
import json

from conftest import drop, seed_source

import gate


# Non-repeating texts: word shingles must be distinct enough that a prefix
# scores ~0.5 (update band) and a near-copy scores >0.85 (near-dup band).
LONG_A = (
    "the quarterly supplier scorecard for acme corporation shows steady "
    "delivery performance and improving quality metrics across twelve "
    "categories measured this period with lead times shrinking notably "
    "while defect rates fell under one percent and the audit team praised "
    "warehouse traceability packaging compliance and the newly digitised "
    "certificate register maintained by the procurement office in lyon"
)
LONG_B = (
    "annual brand review for northwind traders covering social reach "
    "engagement conversion and the ambassador program launched during the "
    "spring campaign window with television spend redirected toward short "
    "form video creators whose audiences overlap the target demographic "
    "according to the panel study commissioned from the media lab"
)


def run_gate(root):
    idx = gate.index_sources(root / "sources")
    return gate.classify_intake(root / "inbox", root / "sources", idx)


def test_exact_duplicate_auto_skips(bucket):
    seed_source(bucket, "reports/q1.csv", LONG_A)
    drop(bucket, "q1-copy.csv", LONG_A)
    result = run_gate(bucket)
    assert len(result["exact_dups"]) == 1
    entry = result["exact_dups"][0]
    assert entry["matched_source"] == "reports/q1.csv"
    assert entry["auto_skip"] is True


def test_clean_new_when_nothing_matches(bucket):
    seed_source(bucket, "reports/q1.csv", LONG_A)
    drop(bucket, "totally-else.csv", LONG_B)
    result = run_gate(bucket)
    assert [e["incoming"] for e in result["clean_new"]] == ["totally-else.csv"]


def test_near_dup_flagged_never_skipped(bucket):
    seed_source(bucket, "reports/q1.csv", LONG_A)
    drop(bucket, "renamed-thing.csv", LONG_A + " one extra trailing clause")
    result = run_gate(bucket)
    assert len(result["near_dups"]) == 1
    assert result["near_dups"][0]["auto_skip"] is False
    assert result["near_dups"][0]["similarity"] >= gate.NEAR_DUP_THRESHOLD


def test_update_candidate_needs_name_match(bucket):
    seed_source(bucket, "reports/q1-report.csv", LONG_A)
    # Same normalized name, ~half-overlapping content -> update band
    half = LONG_A[: len(LONG_A) // 2]
    drop(bucket, "2026-07-01_q1-report.csv", half)
    result = run_gate(bucket)
    assert len(result["update_candidates"]) == 1
    cand = result["update_candidates"][0]
    assert cand["matched_source"] == "reports/q1-report.csv"
    assert gate.UPDATE_SIM_FLOOR <= cand["similarity"] < gate.NEAR_DUP_THRESHOLD


def test_moderate_overlap_without_name_match_is_near_dup(bucket):
    seed_source(bucket, "reports/q1-report.csv", LONG_A)
    half = LONG_A[: len(LONG_A) // 2]
    drop(bucket, "different-name.csv", half)
    result = run_gate(bucket)
    assert len(result["near_dups"]) == 1
    assert not result["update_candidates"]


def test_manifest_and_dotfiles_ignored(bucket):
    drop(bucket, ".DS_Store", "junk")
    result = run_gate(bucket)
    assert all(not v for v in result.values())
    # MANIFEST.md in sources/ never appears as a match candidate
    seed_source(bucket, "notes/a.txt", LONG_A)
    idx = gate.index_sources(bucket / "sources")
    assert "MANIFEST.md" not in {p for paths in idx.by_hash.values() for p in paths}


def test_normalize_filename():
    assert gate.normalize_filename("2026-07-01_Q1 Report.xlsx") == "q1-report"
    assert gate.normalize_filename("Price__List--FINAL.csv") == "price-list-final"


def test_main_writes_manifest_into_workbench(bucket):
    seed_source(bucket, "reports/q1.csv", LONG_A)
    drop(bucket, "new-doc.csv", LONG_B)
    rc = gate.main(["--bucket", str(bucket)])
    assert rc == 0
    runs = list((bucket / "workbench" / ".intake").glob("gate-*.json"))
    assert len(runs) == 1
    data = json.loads(runs[0].read_text(encoding="utf-8"))
    assert data["counts"] == {"exact_dups": 0, "near_dups": 0,
                              "update_candidates": 0, "clean_new": 1}
```

- [ ] **Step 3: Run to verify failure**

Run: `uv run --with pytest pytest skills/fusion-intake/tests/test_gate.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'gate'`

- [ ] **Step 4: Write gate.py**

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""fusion-intake Stage 1 — the deterministic gate classifier.

Hashes every file in inbox/, compares against the sources/ tree, normalizes
filenames, scores content similarity, and writes a gate manifest with four
buckets: exact_dups, near_dups, update_candidates, clean_new. It classifies
and reports — it never writes to sources/ or library/. Stage 2 (the agent,
references/gate.md) assigns the final class and asks the human where the
locked rule requires it.

Usage:
    uv run <skill>/scripts/gate.py --bucket <bucket-root> [--out <path>]
"""
import argparse
import hashlib
import json
import re
import subprocess
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# Locked lineage thresholds (doc-converter, kept verbatim).
NEAR_DUP_THRESHOLD = 0.85   # best content sim >= this (and not exact) -> near-dup
UPDATE_SIM_FLOOR = 0.30     # [floor, near): name match -> update candidate
SHINGLE_K = 3               # word-shingle size for similarity

_DATE_PREFIX = re.compile(r"^(?:\d{4}-\d{2}-\d{2}|\d{8})[_-]")
_SEP_RUN = re.compile(r"[\s_-]+")
_WORD = re.compile(r"\w+")

SKIP_NAMES = {"MANIFEST.md", "README.md"}


def normalize_filename(name: str) -> str:
    """Strip a leading date prefix, lowercase, collapse separators to '-',
    drop the extension."""
    stem = Path(name).stem
    stem = _DATE_PREFIX.sub("", stem)
    stem = stem.lower()
    stem = _SEP_RUN.sub("-", stem).strip("-")
    return stem


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_text(path: Path) -> str:
    """Text for similarity scoring. Binary formats decode to noise and
    effectively compare on filename only — full content comparison is
    Stage 2's judgment work."""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


@dataclass
class SourceIndex:
    by_hash: dict = field(default_factory=lambda: defaultdict(list))
    by_name: dict = field(default_factory=lambda: defaultdict(list))
    text_by_path: dict = field(default_factory=dict)


def _iter_files(root: Path):
    for p in sorted(root.rglob("*")):
        if p.is_file() and not p.name.startswith(".") and p.name not in SKIP_NAMES:
            yield p


def index_sources(sources_dir: Path) -> SourceIndex:
    idx = SourceIndex()
    sources_dir = Path(sources_dir)
    for p in _iter_files(sources_dir):
        rel = str(p.relative_to(sources_dir))
        idx.by_hash[sha256_of(p)].append(rel)
        idx.by_name[normalize_filename(p.name)].append(rel)
        idx.text_by_path[rel] = extract_text(p)
    return idx


def _shingles(text: str, k: int = SHINGLE_K) -> set:
    tokens = _WORD.findall(text.lower())
    if len(tokens) < k:
        return set(tokens)
    return {" ".join(tokens[i:i + k]) for i in range(len(tokens) - k + 1)}


def similarity(a: str, b: str) -> float:
    """Jaccard over word k-shingles: 0.0 disjoint .. 1.0 identical."""
    sa, sb = _shingles(a), _shingles(b)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    union = len(sa | sb)
    return len(sa & sb) / union if union else 0.0


def git_history(path: Path, cwd: Path, limit: int = 10) -> list:
    """Prior-version evidence via git log --follow; [] outside a repo or on
    any failure (liberal reader)."""
    try:
        out = subprocess.run(
            ["git", "log", "--follow", "--date=short",
             f"-n{limit}", "--format=%ad\t%s", "--", str(path)],
            cwd=str(cwd), capture_output=True, text=True, timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    if out.returncode != 0:
        return []
    history = []
    for line in out.stdout.splitlines():
        date, _, subject = line.partition("\t")
        if date:
            history.append({"date": date, "subject": subject})
    return history


def _best_match(incoming_text: str, idx: SourceIndex):
    """Best (path, sim) over ALL sources — catches renamed near-dups."""
    best_path, best_sim = None, 0.0
    for path, src_text in idx.text_by_path.items():
        s = similarity(incoming_text, src_text)
        if s >= best_sim:
            best_path, best_sim = path, s
    return best_path, best_sim


def classify_intake(inbox_dir: Path, sources_dir: Path, idx: SourceIndex) -> dict:
    result = {"exact_dups": [], "near_dups": [],
              "update_candidates": [], "clean_new": []}
    for f in _iter_files(Path(inbox_dir)):
        rel = str(f.relative_to(inbox_dir))
        h = sha256_of(f)

        if h in idx.by_hash:
            result["exact_dups"].append({
                "incoming": rel,
                "matched_source": idx.by_hash[h][0],
                "hash": h,
                "auto_skip": True,
            })
            continue

        name_match = normalize_filename(f.name) in idx.by_name
        match_path, sim = _best_match(extract_text(f), idx)

        if match_path is not None and sim >= NEAR_DUP_THRESHOLD:
            result["near_dups"].append({
                "incoming": rel, "matched_source": match_path,
                "similarity": round(sim, 4), "auto_skip": False,
            })
        elif match_path is not None and sim >= UPDATE_SIM_FLOOR and name_match:
            result["update_candidates"].append({
                "incoming": rel, "matched_source": match_path,
                "similarity": round(sim, 4),
                "history": git_history(Path("sources") / match_path,
                                       Path(sources_dir).parent),
                "auto_skip": False,
            })
        elif match_path is not None and sim >= UPDATE_SIM_FLOOR:
            result["near_dups"].append({
                "incoming": rel, "matched_source": match_path,
                "similarity": round(sim, 4), "auto_skip": False,
            })
        else:
            result["clean_new"].append({"incoming": rel})
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="fusion-intake Stage-1 gate classifier")
    ap.add_argument("--bucket", required=True, help="bucket root")
    ap.add_argument("--out", help="manifest path "
                    "(default: <bucket>/workbench/.intake/gate-<runid>.json)")
    args = ap.parse_args(argv)

    root = Path(args.bucket).expanduser().resolve()
    inbox, sources = root / "inbox", root / "sources"
    if not inbox.is_dir() or not sources.is_dir():
        print(f"not a bucket (no inbox/ + sources/): {root}")
        return 1

    idx = index_sources(sources)
    buckets = classify_intake(inbox, sources, idx)
    manifest = {
        "version": 1,
        "counts": {k: len(v) for k, v in buckets.items()},
        "buckets": buckets,
    }
    out = Path(args.out) if args.out else (
        root / "workbench" / ".intake" / f"gate-{uuid.uuid4().hex[:12]}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"gate: {manifest['counts']} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run the tests**

Run: `uv run --with pytest pytest skills/fusion-intake/tests/test_gate.py -v`
Expected: 8 passed

- [ ] **Step 6: Commit**

```bash
git add skills/fusion-intake/scripts/gate.py skills/fusion-intake/tests/
git commit -m "fusion-intake: Stage-1 gate classifier — four buckets, locked thresholds"
```

---
### Task 3: fusion-intake Stage-1 engine — admit, prepare, link, cleanup

**Files:**
- Create: `skills/fusion-intake/scripts/convert.py`
- Create: `skills/fusion-intake/tests/make_fixtures.py`
- Test: `skills/fusion-intake/tests/test_convert.py`

**Interfaces:**
- Consumes: nothing from Task 2 (gate.py and convert.py are independent scripts).
- Produces: `convert.py` with four subcommands, each printing JSON to stdout:
  - `admit --bucket R --file <inbox-rel> --category C --actor A` → moves `inbox/<file>` to `sources/<C>/<original-name>`, appends the MANIFEST row → `{"source": "<C>/<name>", "sha256": "<full>", "manifest_row": true}`
  - `prepare --bucket R --source <sources-rel> [--dest <zone-rel-dir>] [--slug S] [--type T] [--aurora A] ` → routes by format; extractive finishes (`{"path": "extractive", "done": true, "output_file": …}`); all other paths return `{"done": false, "run_dir": …, "manifest": …, "front_matter_seed": {…}, "pages": […], "images": […], "page_count": N}` for the Stage-2 agent
  - `link --bucket R --source <sources-rel> --doc <bucket-rel-doc>` → sets the MANIFEST row's `library` column (comma-appends on reconversion)
  - `cleanup --run-dir <path>` → deletes one work dir under `workbench/.intake/`
- Later tasks rely on: exact JSON keys above; work dirs under `workbench/.intake/<runid>/`; front_matter_seed keys `title`, `type`, `aurora`, `source`, `created`.

Lineage preserved verbatim: routing table, `TEXT_COVERAGE_MIN_CHARS = 100`, `RENDER_DPI = 150`, page-coverage invariant, no-column-cap `rows_to_table`, cell sanitization (Excel errors → empty, pipes escaped, newlines → `<br>`, floats trimmed, dates ISO). New for Fusion: the `admit` step owns MANIFEST (Constraint 4), Fusion frontmatter (`title`/`type`/`aurora`/`source`/`created`), summary-first extractive documents born conformant, image / `.eml` / `.md`+`.txt` paths.

- [ ] **Step 1: Write make_fixtures.py — real files, generated deterministically**

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["openpyxl>=3.1.0", "pymupdf>=1.24.0"]
# ///
"""Generate real legacy-format fixtures for the intake tests. Imported by
the test modules; also runnable standalone to eyeball the artifacts."""
import zipfile
from email.message import EmailMessage
from pathlib import Path


def make_xlsx(path: Path):
    """Two sheets, exact numbers, a pipe cell, an all-empty column."""
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Scores"
    ws.append(["supplier", "score", None, "notes"])   # 3rd column all-empty
    ws.append(["Acme Corp", 78.5, None, "steady | improving"])
    ws.append(["Northwind", 91, None, "top tier"])
    ws2 = wb.create_sheet("Meta")
    ws2.append(["generated", "2026-07-01"])
    wb.save(path)


def make_csv(path: Path):
    path.write_bytes(
        ("\ufeff" "item,qty,price\nJazzmaster 1962,1,12500.50\n"
         "Pedalboard,1,2300\n").encode("utf-8"))


def make_text_pdf(path: Path):
    """Two pages with a healthy text layer."""
    import fitz
    doc = fitz.open()
    for n in (1, 2):
        page = doc.new_page()
        text = (f"Page {n} of the supplier audit. " * 12)
        page.insert_text((72, 72), text, fontsize=11)
    doc.save(path)
    doc.close()


def make_scanned_pdf(path: Path):
    """One page, no text layer at all — drawing only."""
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.draw_line((72, 72), (400, 400))
    doc.save(path)
    doc.close()


DOCX_DOCUMENT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body>
<w:p><w:r><w:t>Onboarding procedure for the studio bucket.</w:t></w:r></w:p>
<w:p><w:r><w:t>Step one: read the conventions. Step two: sign the ledger.</w:t></w:r></w:p>
</w:body></w:document>"""

DOCX_CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""

DOCX_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""


def make_docx(path: Path):
    """Minimal valid OOXML — LibreOffice opens it happily."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", DOCX_CONTENT_TYPES)
        z.writestr("_rels/.rels", DOCX_RELS)
        z.writestr("word/document.xml", DOCX_DOCUMENT)


def make_eml(path: Path):
    msg = EmailMessage()
    msg["From"] = "gilberte@example.com"
    msg["To"] = "studio@example.com"
    msg["Subject"] = "Re: rehearsal schedule"
    msg["Date"] = "Thu, 09 Jul 2026 10:15:00 +0200"
    msg.set_content("Rehearsal moves to Thursday. Bring the Jazzmaster.\n")
    msg.add_attachment(b"setlist,song\n1,First Light\n",
                       maintype="text", subtype="csv", filename="setlist.csv")
    path.write_bytes(bytes(msg))


def make_png(path: Path):
    """Tiny valid PNG (1x1, red) — hand-assembled, no dependencies."""
    import struct, zlib
    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(
            ">I", zlib.crc32(c) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    idat = zlib.compress(b"\x00\xff\x00\x00")
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
                     + chunk(b"IDAT", idat) + chunk(b"IEND", b""))


if __name__ == "__main__":
    out = Path("fixtures-preview")
    out.mkdir(exist_ok=True)
    make_xlsx(out / "scores.xlsx"); make_csv(out / "inventory.csv")
    make_text_pdf(out / "audit.pdf"); make_scanned_pdf(out / "scan.pdf")
    make_docx(out / "procedure.docx"); make_eml(out / "mail.eml")
    make_png(out / "photo.png")
    print(f"fixtures in {out}/")
```

- [ ] **Step 2: Write the failing tests**

Create `skills/fusion-intake/tests/test_convert.py`:

```python
"""Stage-1 engine: admit -> MANIFEST, extractive conversion, vision prep,
link, cleanup. The lossless contract, tested."""
import shutil

import pytest
from conftest import bucket  # noqa: F401 (fixture)

import convert
import make_fixtures as fx


def admit(root, name, category="records", actor="claude"):
    return convert.admit(root, name, category=category, actor=actor)


def put_inbox(root, name, maker):
    p = root / "inbox" / name
    maker(p)
    return p


# ── admit ────────────────────────────────────────────────────────────────

def test_admit_moves_and_registers(bucket):
    put_inbox(bucket, "scores.xlsx", fx.make_xlsx)
    rec = admit(bucket, "scores.xlsx")
    assert rec["source"] == "records/scores.xlsx"
    assert len(rec["sha256"]) == 64
    assert not (bucket / "inbox" / "scores.xlsx").exists()
    assert (bucket / "sources" / "records" / "scores.xlsx").is_file()
    manifest = (bucket / "sources" / "MANIFEST.md").read_text(encoding="utf-8")
    row = manifest.strip().splitlines()[-1]
    cells = [c.strip() for c in row.strip("|").split("|")]
    assert cells[0] == "records/scores.xlsx"
    assert cells[2] == "claude"
    assert cells[3] == rec["sha256"]
    assert cells[4] == "—"


def test_admit_refuses_source_collision(bucket):
    put_inbox(bucket, "scores.xlsx", fx.make_xlsx)
    admit(bucket, "scores.xlsx")
    put_inbox(bucket, "scores.xlsx", fx.make_xlsx)
    with pytest.raises(convert.IntakeError, match="immutable"):
        admit(bucket, "scores.xlsx")


def test_admit_missing_file(bucket):
    with pytest.raises(convert.IntakeError, match="inbox"):
        admit(bucket, "ghost.xlsx")


# ── extractive paths ─────────────────────────────────────────────────────

def test_xlsx_extractive_is_born_conformant(bucket):
    put_inbox(bucket, "Q1 Scores.xlsx", fx.make_xlsx)
    rec = admit(bucket, "Q1 Scores.xlsx")
    out = convert.prepare(bucket, rec["source"])
    assert out["done"] is True
    doc = (bucket / out["output_file"]).read_text(encoding="utf-8")
    # frontmatter
    assert doc.startswith("---\n")
    assert "title:" in doc and "type:" in doc and "aurora: library" in doc
    assert "source: sources/records/Q1 Scores.xlsx" in doc
    # summary-first
    body = doc.split("---\n", 2)[2]
    assert body.lstrip().startswith("## Summary")
    assert "\n---\n" in body
    # lossless table facts: exact numbers, pipe escaped, empty col pruned
    assert "78.5" in doc and "| 91 |" in doc
    assert "steady \\| improving" in doc
    assert "| supplier | score | notes |" in doc   # all-empty column pruned
    assert "## Scores" in doc and "## Meta" in doc
    # slug filename
    assert out["output_file"].endswith("library/records/q1-scores.md")


def test_csv_extractive_bom_and_numbers(bucket):
    put_inbox(bucket, "inventory.csv", fx.make_csv)
    rec = admit(bucket, "inventory.csv")
    out = convert.prepare(bucket, rec["source"])
    doc = (bucket / out["output_file"]).read_text(encoding="utf-8")
    assert "12500.50" in doc          # verbatim, never rounded
    assert "\ufeff" not in doc      # BOM consumed
    assert "Jazzmaster 1962" in doc


def test_invalid_aurora_refused(bucket):
    put_inbox(bucket, "inventory.csv", fx.make_csv)
    rec = admit(bucket, "inventory.csv")
    with pytest.raises(convert.IntakeError, match="aurora"):
        convert.prepare(bucket, rec["source"], aurora="vibes")


def test_dest_and_type_overrides(bucket):
    put_inbox(bucket, "inventory.csv", fx.make_csv)
    rec = admit(bucket, "inventory.csv", category="gear")
    out = convert.prepare(bucket, rec["source"], dest="library/instruments",
                          doc_type="inventory", slug="pedal-inventory")
    assert out["output_file"] == "library/instruments/pedal-inventory.md"
    doc = (bucket / out["output_file"]).read_text(encoding="utf-8")
    assert "type: inventory" in doc


# ── vision prep paths ────────────────────────────────────────────────────

def test_text_pdf_spotcheck(bucket):
    put_inbox(bucket, "audit.pdf", fx.make_text_pdf)
    rec = admit(bucket, "audit.pdf")
    out = convert.prepare(bucket, rec["source"])
    assert out["done"] is False and out["path"] == "pdf_text"
    assert out["page_count"] == 2 == len(out["pages"])
    assert all(not p["needs_vision"] for p in out["pages"])
    assert out["images"] == []        # nothing to spot-check
    assert out["front_matter_seed"]["aurora"] == "library"
    assert out["front_matter_seed"]["source"] == "sources/records/audit.pdf"
    assert (bucket / out["manifest"]).is_file()


def test_scanned_pdf_all_pages_rendered(bucket):
    put_inbox(bucket, "scan.pdf", fx.make_scanned_pdf)
    rec = admit(bucket, "scan.pdf")
    out = convert.prepare(bucket, rec["source"])
    assert out["path"] == "pdf_scanned"
    assert out["pages"][0]["needs_vision"] is True
    assert len(out["images"]) == out["page_count"] == 1


def test_image_path(bucket):
    put_inbox(bucket, "photo.png", fx.make_png)
    rec = admit(bucket, "photo.png")
    out = convert.prepare(bucket, rec["source"])
    assert out["path"] == "image"
    assert out["pages"] == [{"page": 1, "text": "", "text_chars": 0,
                             "needs_vision": True}]
    assert len(out["images"]) == 1


def test_eml_path_extracts_text_and_attachments(bucket):
    put_inbox(bucket, "mail.eml", fx.make_eml)
    rec = admit(bucket, "mail.eml")
    out = convert.prepare(bucket, rec["source"])
    assert out["path"] == "mail"
    text = out["pages"][0]["text"]
    assert "Subject: Re: rehearsal schedule" in text
    assert "Bring the Jazzmaster" in text
    assert out["attachments"] == ["setlist.csv"]
    assert (bucket / out["run_dir"] / "setlist.csv").is_file()


def test_markdown_passthrough(bucket):
    (bucket / "inbox" / "note.md").write_text(
        "# A note\n\nJust words.\n", encoding="utf-8")
    rec = admit(bucket, "note.md")
    out = convert.prepare(bucket, rec["source"])
    assert out["path"] == "text"
    assert out["pages"][0]["text"] == "# A note\n\nJust words.\n"
    assert out["pages"][0]["needs_vision"] is False


@pytest.mark.skipif(shutil.which("soffice") is None,
                    reason="LibreOffice not on PATH")
def test_docx_libreoffice_path(bucket):
    put_inbox(bucket, "procedure.docx", fx.make_docx)
    rec = admit(bucket, "procedure.docx")
    out = convert.prepare(bucket, rec["source"])
    assert out["path"] == "libreoffice"
    assert out["intermediate_pdf"].endswith(".pdf")
    assert out["page_count"] == len(out["pages"]) >= 1
    assert len(out["images"]) == out["page_count"]   # ALL pages rendered
    joined = " ".join(p["text"] for p in out["pages"])
    assert "Onboarding procedure" in joined


def test_docx_fails_fast_without_soffice(bucket, monkeypatch):
    put_inbox(bucket, "procedure.docx", fx.make_docx)
    rec = admit(bucket, "procedure.docx")
    monkeypatch.setattr(shutil, "which", lambda _: None)
    with pytest.raises(convert.IntakeError, match="LibreOffice"):
        convert.prepare(bucket, rec["source"])


# ── link + cleanup ───────────────────────────────────────────────────────

def test_link_sets_library_column(bucket):
    put_inbox(bucket, "inventory.csv", fx.make_csv)
    rec = admit(bucket, "inventory.csv")
    convert.link(bucket, rec["source"], "library/records/inventory.md")
    manifest = (bucket / "sources" / "MANIFEST.md").read_text(encoding="utf-8")
    row = manifest.strip().splitlines()[-1]
    assert row.split("|")[-2].strip() == "library/records/inventory.md"
    # a second link comma-appends
    convert.link(bucket, rec["source"], "library/records/inventory-2.md")
    manifest = (bucket / "sources" / "MANIFEST.md").read_text(encoding="utf-8")
    assert manifest.count("inventory.md, library/records/inventory-2.md") == 1


def test_link_unknown_source_refused(bucket):
    with pytest.raises(convert.IntakeError, match="manifest"):
        convert.link(bucket, "records/ghost.csv", "library/x.md")


def test_cleanup_removes_only_the_run_dir(bucket):
    put_inbox(bucket, "photo.png", fx.make_png)
    rec = admit(bucket, "photo.png")
    out = convert.prepare(bucket, rec["source"])
    run_dir = bucket / out["run_dir"]
    assert run_dir.is_dir()
    convert.cleanup(run_dir)
    assert not run_dir.exists()
    assert (bucket / "workbench" / ".intake").is_dir()


def test_slugify():
    assert convert.slugify("Q1 Scores (FINAL).xlsx") == "q1-scores-final"
    assert len(convert.slugify("x" * 200)) <= 60
```

- [ ] **Step 3: Run to verify failure**

Run: `uv run --with pytest --with pyyaml --with openpyxl --with pymupdf pytest skills/fusion-intake/tests/test_convert.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'convert'`

- [ ] **Step 4: Write convert.py**

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "openpyxl>=3.1.0",
#   "PyYAML>=6.0",
#   "pymupdf>=1.24.0",
# ]
# ///
"""fusion-intake Stage-1 engine: admit / prepare / link / cleanup.

Deterministic, no LLM. `admit` is the ONLY writer of sources/MANIFEST.md in
the whole Fusion reference implementation. `prepare` routes by format:
extractive files (xlsx/csv) become conformant documents directly; everything
else gets a work dir under workbench/.intake/ with page text + images +
manifest.json for the Stage-2 agent (references/convert.md). The page-
coverage invariant — every page recorded, low-text pages flagged
needs_vision — makes silent-empty output structurally impossible.
"""
import argparse
import csv as csv_mod
import hashlib
import json
import re
import shutil
import subprocess
import sys
import uuid
from datetime import datetime
from email import policy
from email.parser import BytesParser
from pathlib import Path

import yaml

AURORAS = ("commitments", "focus", "ops", "collab", "life", "explore",
           "archive", "library")

EXTRACTIVE_EXTS = {".xlsx", ".csv"}
LIBREOFFICE_EXTS = {".docx", ".pptx", ".doc", ".odt", ".rtf", ".key",
                    ".pages", ".ppt", ".xls"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
MAIL_EXTS = {".eml"}
TEXT_EXTS = {".md", ".txt"}

TEXT_COVERAGE_MIN_CHARS = 100   # below this a page is scanned/figure
RENDER_DPI = 150
EXCEL_ERRORS = {"#REF!", "#N/A", "#VALUE!", "#DIV/0!", "#NAME?", "#NULL!",
                "#NUM!"}

TODAY = datetime.now().strftime("%Y-%m-%d")


class IntakeError(Exception):
    """Strict-writer refusal — named loudly, never silently skipped."""


# ── shared helpers ───────────────────────────────────────────────────────

def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def slugify(name: str) -> str:
    """SPEC §4 filename: lowercase, hyphen-separated, stem <=60 chars."""
    stem = re.sub(r"\.(xlsx|docx|pptx|csv|pdf|eml|md|txt|png|jpe?g|webp|gif)$",
                  "", name, flags=re.IGNORECASE)
    stem = stem.lower()
    stem = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")
    stem = re.sub(r"-+", "-", stem)
    return stem[:60].rstrip("-") or "document"


def cell_to_string(cell) -> str:
    if isinstance(cell, str) and cell.strip() in EXCEL_ERRORS:
        return ""
    if cell is None:
        return ""
    if isinstance(cell, bool):
        return str(cell)
    if isinstance(cell, float):
        if cell == int(cell):
            return str(int(cell))
        return f"{cell:.4f}".rstrip("0").rstrip(".")
    if isinstance(cell, int):
        return str(cell)
    if isinstance(cell, datetime):
        return cell.strftime("%Y-%m-%d")
    text = str(cell).replace("|", "\\|").replace("\n", "<br>")
    return text.strip()


def _row_empty(row) -> bool:
    return all(cell_to_string(c) == "" for c in row)


def prune_empty_columns(rows):
    if not rows:
        return rows
    width = max(len(r) for r in rows)
    padded = [list(r) + [None] * (width - len(r)) for r in rows]
    keep = [i for i in range(width)
            if any(cell_to_string(r[i]) != "" for r in padded)]
    return [[r[i] for i in keep] for r in padded] if keep else []


def rows_to_table(rows) -> str:
    """One markdown table. Every row, every column — no caps, no sampling."""
    rows = [r for r in rows if not _row_empty(r)]
    rows = prune_empty_columns(rows)
    if not rows or not rows[0]:
        return "*No data*"
    string_rows = [[cell_to_string(c) for c in r] for r in rows]
    lines = ["| " + " | ".join(string_rows[0]) + " |",
             "| " + " | ".join(["---"] * len(rows[0])) + " |"]
    lines += ["| " + " | ".join(r) + " |" for r in string_rows[1:]]
    return "\n".join(lines)


def render_document(fm: dict, summary: str, body: str) -> str:
    front = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True,
                           width=2**31 - 1)
    return f"---\n{front}---\n\n## Summary\n\n{summary}\n\n---\n\n{body}\n"


# ── MANIFEST (single writer lives here) ──────────────────────────────────

def _manifest_path(root: Path) -> Path:
    return root / "sources" / "MANIFEST.md"


def manifest_append(root: Path, rel: str, actor: str, sha: str) -> None:
    path = _manifest_path(root)
    if not path.is_file():
        path.write_text("# Manifest\n\n| file | added | by | sha256 | library |\n"
                        "|---|---|---|---|---|\n", encoding="utf-8")
    text = path.read_text(encoding="utf-8")
    if not text.endswith("\n"):
        text += "\n"
    text += f"| {rel} | {TODAY} | {actor} | {sha} | — |\n"
    path.write_text(text, encoding="utf-8")


def manifest_link(root: Path, rel: str, doc: str) -> None:
    path = _manifest_path(root)
    if not path.is_file():
        raise IntakeError(f"no manifest at {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    hit = False
    for i, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 5 and cells[0] == rel:
            cells[4] = doc if cells[4] in ("—", "") else f"{cells[4]}, {doc}"
            lines[i] = "| " + " | ".join(cells) + " |"
            hit = True
            break
    if not hit:
        raise IntakeError(f"source not in manifest: {rel}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ── admit ────────────────────────────────────────────────────────────────

def admit(root: Path, inbox_rel: str, category: str, actor: str) -> dict:
    root = Path(root)
    src = root / "inbox" / inbox_rel
    if not src.is_file():
        raise IntakeError(f"not in inbox/: {inbox_rel}")
    if not actor or any(c.isspace() for c in actor):
        raise IntakeError(f"actor must be a single token: {actor!r}")
    category = category.strip().strip("/")
    if not category:
        raise IntakeError("category required")
    dest = root / "sources" / category / src.name
    if dest.exists():
        raise IntakeError(
            f"sources/ is immutable and {category}/{src.name} already "
            "exists — rename the incoming file before admitting it")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dest))
    sha = sha256_of(dest)
    rel = f"{category}/{src.name}"
    manifest_append(root, rel, actor, sha)
    return {"source": rel, "sha256": sha, "manifest_row": True}


# ── prepare: routing + engines ───────────────────────────────────────────

def probe_pdf_text_layer(pdf_path: Path):
    import fitz
    records = []
    doc = fitz.open(str(pdf_path))
    try:
        for i, page in enumerate(doc, 1):
            text = page.get_text().strip()
            records.append({"page": i, "text": text, "text_chars": len(text),
                            "needs_vision": len(text) < TEXT_COVERAGE_MIN_CHARS})
    finally:
        doc.close()
    return records


def render_pdf_pages(pdf_path: Path, out_dir: Path, pages=None):
    import fitz
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    doc = fitz.open(str(pdf_path))
    try:
        targets = (list(range(1, doc.page_count + 1))
                   if pages is None else sorted(pages))
        for n in targets:
            if 1 <= n <= doc.page_count:
                pix = doc.load_page(n - 1).get_pixmap(dpi=RENDER_DPI)
                img = out_dir / f"page-{n:03d}.png"
                pix.save(str(img))
                written.append(img)
    finally:
        doc.close()
    return written


def require_soffice() -> str:
    exe = shutil.which("soffice") or shutil.which("libreoffice")
    if not exe:
        raise IntakeError(
            "LibreOffice not found: 'soffice' must be on PATH for "
            "docx/pptx/legacy office formats (declared in SKILL.md "
            "compatibility). Install it or add it to PATH. No fallback.")
    return exe


def soffice_to_pdf(src: Path, out_dir: Path) -> Path:
    exe = require_soffice()
    out_dir.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [exe, "--headless", "--convert-to", "pdf", "--outdir",
         str(out_dir), str(src)],
        capture_output=True, text=True, timeout=300)
    pdf = out_dir / (src.stem + ".pdf")
    if proc.returncode != 0 or not pdf.exists():
        raise IntakeError(
            f"soffice failed on {src.name} (rc={proc.returncode}): "
            f"{proc.stderr.strip()[:400]}")
    return pdf


def eml_to_text(path: Path, work_dir: Path):
    msg = BytesParser(policy=policy.default).parse(open(path, "rb"))
    lines = [f"{h}: {msg[h]}" for h in ("From", "To", "Date", "Subject")
             if msg[h]]
    body = msg.get_body(preferencelist=("plain", "html"))
    content = body.get_content() if body else ""
    if body and body.get_content_subtype() == "html":
        content = re.sub(r"<[^>]+>", " ", content)
    attachments = []
    for part in msg.iter_attachments():
        name = Path(part.get_filename() or "attachment.bin").name
        (work_dir / name).write_bytes(part.get_payload(decode=True) or b"")
        attachments.append(name)
    return "\n".join(lines) + "\n\n" + content, attachments


def _route(ext: str) -> str:
    ext = ext.lower()
    if ext in EXTRACTIVE_EXTS:
        return "extractive"
    if ext in LIBREOFFICE_EXTS:
        return "libreoffice"
    if ext == ".pdf":
        return "pdf"
    if ext in IMAGE_EXTS:
        return "image"
    if ext in MAIL_EXTS:
        return "mail"
    if ext in TEXT_EXTS:
        return "text"
    raise IntakeError(f"unsupported format: {ext} — the gate refuses "
                      "what it cannot preserve")


def _xlsx_body(path: Path):
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True)
    sections, sheets, rows_total = [], 0, 0
    for name in wb.sheetnames:
        rows = list(wb[name].iter_rows(values_only=True))
        live = [r for r in rows if not _row_empty(r)]
        if live:
            sheets += 1
            rows_total += max(len(live) - 1, 0)
            sections.append(f"## {name}\n\n{rows_to_table(rows)}")
    return "\n\n".join(sections) or "*No data*", sheets, rows_total


def _csv_body(path: Path):
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv_mod.reader(fh))
    return rows_to_table(rows), 1, max(len(rows) - 1, 0)


def _work_dir(root: Path) -> Path:
    d = root / "workbench" / ".intake" / uuid.uuid4().hex[:12]
    d.mkdir(parents=True, exist_ok=True)
    return d


def prepare(root: Path, source_rel: str, dest: str | None = None,
            slug: str | None = None, doc_type: str | None = None,
            aurora: str = "library") -> dict:
    root = Path(root)
    src = root / "sources" / source_rel
    if not src.is_file():
        raise IntakeError(f"not in sources/: {source_rel}")
    if aurora not in AURORAS:
        raise IntakeError(f"aurora must be one of the eight, got: {aurora!r}")
    category = Path(source_rel).parts[0] if "/" in source_rel else "reference"
    doc_type = doc_type or category.rstrip("s")
    dest = (dest or f"library/{category}").strip("/")
    slug = slug or slugify(src.name)
    out_rel = f"{dest}/{slug}.md"
    seed = {"title": src.stem, "type": doc_type, "aurora": aurora,
            "source": f"sources/{source_rel}", "created": TODAY}
    path = _route(src.suffix)

    if path == "extractive":
        if src.suffix.lower() == ".xlsx":
            body, sheets, nrows = _xlsx_body(src)
        else:
            body, sheets, nrows = _csv_body(src)
        summary = (f"Tabular data converted from {src.name}: "
                   f"{sheets} sheet(s), {nrows} data row(s).")
        out = root / out_rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_document(seed, summary, body), encoding="utf-8")
        return {"path": "extractive", "done": True, "source": source_rel,
                "output_file": out_rel, "front_matter_seed": seed}

    # vision / structured paths get a work dir + manifest for Stage 2
    work = _work_dir(root)
    record = {"path": path, "done": False, "source": source_rel,
              "run_dir": str(work.relative_to(root)),
              "output_file": out_rel, "front_matter_seed": seed,
              "pages": [], "images": [], "attachments": [],
              "intermediate_pdf": None}

    if path == "libreoffice":
        pdf = soffice_to_pdf(src, work)
        record["intermediate_pdf"] = str(pdf.relative_to(root))
        record["pages"] = probe_pdf_text_layer(pdf)
        imgs = render_pdf_pages(pdf, work)                    # ALL pages
        record["images"] = [str(p.relative_to(root)) for p in imgs]
    elif path == "pdf":
        probe = probe_pdf_text_layer(src)
        record["pages"] = probe
        if all(p["needs_vision"] for p in probe):
            record["path"] = "pdf_scanned"
            imgs = render_pdf_pages(src, work)                # ALL pages
        else:
            record["path"] = "pdf_text"
            imgs = render_pdf_pages(
                src, work, pages=[p["page"] for p in probe if p["needs_vision"]])
        record["images"] = [str(p.relative_to(root)) for p in imgs]
    elif path == "image":
        copy = work / src.name
        shutil.copy2(src, copy)
        record["pages"] = [{"page": 1, "text": "", "text_chars": 0,
                            "needs_vision": True}]
        record["images"] = [str(copy.relative_to(root))]
    elif path == "mail":
        text, attachments = eml_to_text(src, work)
        record["pages"] = [{"page": 1, "text": text,
                            "text_chars": len(text), "needs_vision": False}]
        record["attachments"] = attachments
    else:  # text passthrough
        text = src.read_text(encoding="utf-8", errors="replace")
        record["pages"] = [{"page": 1, "text": text,
                            "text_chars": len(text), "needs_vision": False}]

    record["page_count"] = len(record["pages"])
    manifest = work / "manifest.json"
    manifest.write_text(json.dumps(record, indent=2), encoding="utf-8")
    record["manifest"] = str(manifest.relative_to(root))
    return record


def link(root: Path, source_rel: str, doc_rel: str) -> dict:
    manifest_link(Path(root), source_rel, doc_rel)
    return {"source": source_rel, "library": doc_rel}


def cleanup(run_dir: Path) -> None:
    run_dir = Path(run_dir)
    if run_dir.exists():
        shutil.rmtree(run_dir)


# ── CLI ──────────────────────────────────────────────────────────────────

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="fusion-intake Stage-1 engine")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("admit", help="inbox -> sources + MANIFEST row")
    p.add_argument("--bucket", required=True)
    p.add_argument("--file", required=True, help="path relative to inbox/")
    p.add_argument("--category", required=True)
    p.add_argument("--actor", required=True)

    p = sub.add_parser("prepare", help="route + convert / stage for vision")
    p.add_argument("--bucket", required=True)
    p.add_argument("--source", required=True, help="path relative to sources/")
    p.add_argument("--dest", help="zone-relative output dir "
                   "(default library/<category>)")
    p.add_argument("--slug")
    p.add_argument("--type", dest="doc_type")
    p.add_argument("--aurora", default="library")

    p = sub.add_parser("link", help="set the MANIFEST library column")
    p.add_argument("--bucket", required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--doc", required=True)

    p = sub.add_parser("cleanup", help="delete one work dir")
    p.add_argument("--run-dir", required=True)

    args = ap.parse_args(argv)
    try:
        if args.cmd == "admit":
            out = admit(Path(args.bucket), args.file, args.category, args.actor)
        elif args.cmd == "prepare":
            out = prepare(Path(args.bucket), args.source, dest=args.dest,
                          slug=args.slug, doc_type=args.doc_type,
                          aurora=args.aurora)
        elif args.cmd == "link":
            out = link(Path(args.bucket), args.source, args.doc)
        else:
            cleanup(Path(args.run_dir))
            out = {"cleaned": args.run_dir}
    except IntakeError as exc:
        print(f"intake: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run the tests**

Run: `uv run --with pytest --with pyyaml --with openpyxl --with pymupdf pytest skills/fusion-intake/tests/ -v`
Expected: all passing (gate suite + ~18 new; `test_docx_libreoffice_path` runs — soffice IS on this machine; if it skips, that is a failure of the task, investigate PATH).

- [ ] **Step 6: Cross-implementation round-trip check (the Phase-2 lesson: the writer guarantees its own reader)**

The CLI's `manifest.py::read()` must parse what `admit` writes. Run from repo root:

```bash
T=$(mktemp -d) && mkdir -p $T/b/inbox $T/b/sources && \
printf 'a,b\n1,2\n' > $T/b/inbox/x.csv && \
printf '# Manifest\n\n| file | added | by | sha256 | library |\n|---|---|---|---|---|\n' > $T/b/sources/MANIFEST.md && \
uv run skills/fusion-intake/scripts/convert.py admit --bucket $T/b --file x.csv --category recs --actor claude && \
cd cli && uv run python -c "
from pathlib import Path; import sys
sys.path.insert(0, 'src')
from fusion import manifest
rows = manifest.read(Path('$T/b'))
assert len(rows) == 1 and rows[0].file == 'recs/x.csv', rows
print('round-trip ok:', rows[0])
"
```

Expected: `round-trip ok: ManifestRow(...)`. If the reader drops the row, fix `convert.py`'s writer (never the fixture, never the CLI reader).

- [ ] **Step 7: Commit**

```bash
git add skills/fusion-intake/scripts/convert.py skills/fusion-intake/tests/
git commit -m "fusion-intake: Stage-1 engine — admit/prepare/link/cleanup, lossless routing"
```

---
### Task 4: fusion-intake SKILL.md and the Stage-2 protocols

**Files:**
- Create: `skills/fusion-intake/SKILL.md`
- Create: `skills/fusion-intake/references/gate.md`
- Create: `skills/fusion-intake/references/convert.md`
- Modify: `cli/tests/test_skill_family.py` (remove the `xfail` decorator from `test_at_least_one_skill_exists`)

**Interfaces:**
- Consumes: `scripts/gate.py` (Task 2) and `scripts/convert.py` (Task 3) — invoke them exactly as their `--help` documents; the JSON keys are in Tasks 2–3 Interfaces blocks.
- Produces: the complete fusion-intake skill. Task 5 exercises it verbatim.

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: fusion-intake
description: "The Fusion intake gate — everything that enters a bucket enters through it, losslessly. Classify what landed in inbox/ (new, updated, duplicate, conflicting), preserve the original in sources/ with its sha256 in the MANIFEST, convert to a faithful summary-first document (xlsx, csv, docx, pptx, pdf, images, .eml mail, markdown/text exports), propose type and aurora, sign the ledger, clear the inbox. Use when the user says 'process the inbox', 'intake', 'ingest', 'convert this file', or drops files into a Fusion bucket's inbox/. For placement, curation, or restructuring of what is already inside, use fusion-librarian; for deliverables out of the bucket, use fusion-analyst."
license: MIT
compatibility: "Requires the fusion CLI on PATH and uv. LibreOffice (soffice on PATH) required for docx/pptx/legacy office formats — fails fast when missing, never silently degrades. Script deps via PEP 723 (openpyxl, PyYAML, pymupdf)."
---

# fusion-intake — the gate

Nothing enters the library except through the gate. The gate preserves
originals forever, converts losslessly, and asks before it acts on anything
that isn't clean and new.

Read `references/fusion-conventions.md` once per session. Then, before
touching anything: read the bucket's `BUCKET.md` — `## Conventions` may
contain filing rules and standing delegations that bind this whole run.

## The pipeline

```
inbox/ ─► STAGE 1 gate (scripts/gate.py)      deterministic: hash, similarity
              │        four buckets → gate-<runid>.json
              ▼
          STAGE 2 gate (references/gate.md)   judgment: final class + intake report
              │        new → auto-proceed · exact dup → auto-skip
              │        near-dup / updated / conflicting → ASK FIRST
              ▼
          ADMIT + CONVERT (scripts/convert.py) original → sources/ + MANIFEST row
              │        xlsx/csv finish here; everything else stages pages
              ▼
          STAGE 2 convert (references/convert.md)  vision reconstruction,
              │        fidelity checklist, summary, type + aurora
              ▼
          CLOSE       link MANIFEST → fusion log → fusion index → fusion check
                      inbox file deleted ONLY when check is green
```

## Running it

Every command runs with the bucket root as `--bucket`; `<skill>` is this
skill's directory.

1. **Classify:** `uv run <skill>/scripts/gate.py --bucket <root>`
   → read the printed manifest path, then load `references/gate.md` and
   follow it to the intake report. Stop for confirmation where it says stop.
2. **Admit** each approved file:
   `uv run <skill>/scripts/convert.py admit --bucket <root> --file <name> --category <cat> --actor <you>`
   Category follows the bucket's filing rules (BUCKET.md), else a short
   plural noun (`reports`, `mails`, `gear`). The MANIFEST row is the
   script's job — never edit MANIFEST.md yourself.
3. **Prepare:**
   `uv run <skill>/scripts/convert.py prepare --bucket <root> --source <cat>/<name> [--dest …] [--type …] [--aurora …]`
   Extractive files (`done: true`) are already conformant documents.
   Everything else returns a work-dir manifest — load
   `references/convert.md` and reconstruct.
4. **Close** (per file): refine the document summary if it's the
   deterministic placeholder, then
   `uv run <skill>/scripts/convert.py link --bucket <root> --source <cat>/<name> --doc <zone-rel-doc>`
   `fusion log converted "sources/<cat>/<name> → <doc>" --as <you>`
   `fusion index` · `fusion check <root>` — green, then and only then
   delete the inbox file and `cleanup --run-dir <dir>`.

## The four classes (locked)

| Class | Meaning | Action |
|---|---|---|
| new | nothing matches | auto-proceed |
| duplicate (exact) | byte-identical to a source | auto-skip, recorded |
| duplicate (near) | re-export / trivial edit | ASK: skip / update / new |
| updated | newer version of an existing source | ASK, then supersede |
| conflicting | claims contradict the library | ASK — the gate never picks a winner |

**Supersede, the Fusion way:** `sources/` is immutable — a confirmed update
ADMITS THE NEW FILE as its own source (rename it first if the name
collides) and RECONCILES the existing library document in place: same
path, content updated, `updated:` bumped, `source:` repointed to the new
original. One document, no `-v2` twin. The old original stays in
`sources/` and the MANIFEST, superseded but never erased.

## The fidelity contract (lossless, non-negotiable)

- The original lands in `sources/` byte-identical, full sha256 in MANIFEST.
- Every page is accounted for (`page_count == len(pages)`); a page the
  text layer can't cover is flagged `needs_vision` and YOU read its image.
- Tables: every row, every column. Numbers verbatim — never rounded,
  never paraphrased. Figures get a one-line caption.
- Doubtful fidelity (blurry scan, unreadable region)? Flag it to the human
  and leave the file in inbox. A lossy conversion is a failed conversion.
- The inbox file is deleted only after MANIFEST link + ledger + green
  `fusion check`.

## Never

- Never modify, rename, or delete anything in `sources/`.
- Never hand-edit `MANIFEST.md`, `LEDGER.md`, or any `INDEX.md`.
- Never convert a near-dup, update, or conflict without a yes.
- Never leave a converted file's ledger entry unsigned.
```

- [ ] **Step 2: Write references/gate.md**

```markdown
# The intake gate — Stage 2 (judgment)

Stage 1 (`scripts/gate.py`) wrote `workbench/.intake/gate-<runid>.json`
with four buckets: `exact_dups`, `near_dups`, `update_candidates`,
`clean_new`. This stage assigns each file's final class and writes the
intake report. It writes NOTHING to `sources/` or `library/` — admission
and conversion happen only after this stage's confirmations.

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
```

- [ ] **Step 3: Write references/convert.md**

```markdown
# Conversion — Stage 2 (reconstruction)

`prepare` returned `done: false` and a work-dir manifest. You are the
vision half of the engine: reconstruct the document faithfully, then close
the loop. All paths below are bucket-relative.

## Reconstruct

Read `manifest.json` (`run_dir`, `pages`, `images`, `front_matter_seed`,
`output_file`, `attachments`).

Walk `pages` in order:
- `needs_vision: false` → use the page's `text` verbatim. Do not
  paraphrase; do not "clean up" numbers.
- `needs_vision: true` → Read the corresponding `page-NNN.png` (or the
  staged image) and transcribe what you see: headings, paragraphs, FULL
  tables — every column, every row, no cap — and figures as a one-line
  caption (`*Figure: monthly deliveries trending up since March.*`).

Format-specific notes:
- **mail** (`path: mail`): the page text carries headers + body. Body
  becomes the document; headers land in the summary and frontmatter
  (`created:` from the Date header). Attachments were extracted into the
  work dir — tell the user, and offer to move them to `inbox/` so each
  goes through the gate itself.
- **text** (`path: text`): the content is already prose. Normalize it
  into the document body; if it carried frontmatter, preserve unknown
  keys (liberal reader) and merge the required three.
- **image**: transcribe or describe honestly — a photo gets a faithful
  description, a screenshot of text gets the text.

## Write the document

To `output_file`, exactly this shape:

```markdown
---
title: <refined from content — the seed title is just the filename>
type: <seed, or better from content>
aurora: <see the guidance below>
source: <seed verbatim>
created: <seed verbatim, or the mail Date>
---

## Summary

<2–3 lines a human reads in two seconds to decide whether to open the rest.
Write it from the content — never "converted from X.">

---

<the reconstructed body>
```

Aurora guidance (the eight are the eight):
| Content | Aurora |
|---|---|
| Settled reference: manuals, records, data, mail worth keeping | `library` |
| Something to act on with a deadline or promise | `commitments` |
| Material for current deep work | `focus` |
| Recurring process, ops docs | `ops` |
| Shared work, other people's input | `collab` |
| Personal, non-work | `life` |
| Unvetted research, curiosity | `explore` |

When unsure between two: propose one, note the alternative in the intake
report. The bucket's own Rules (BUCKET.md) override this table.

## The fidelity checklist (run it before closing)

1. Document is non-empty and summary-first.
2. Every manifest page is represented in the body (count them).
3. Every table's row and column counts match the source page (spot-check
   against the image).
4. All three required frontmatter fields present; aurora is one of the
   eight; `source:` points at the admitted original.
5. Anything you could not read faithfully is flagged in your report to
   the human — and the inbox file stays put.

## Close the loop (per file, in this order)

```bash
uv run <skill>/scripts/convert.py link --bucket <root> --source <cat>/<file> --doc <output_file>
fusion log converted "sources/<cat>/<file> → <output_file>" --as <you>
fusion index
fusion check <root>
```

Green check → delete the inbox file, then
`uv run <skill>/scripts/convert.py cleanup --run-dir <run_dir>`.
Extractive files (`done: true`) skip reconstruction but get the same
close: refine their placeholder summary and title from the tables first
(Edit the document — that is a content change, so bump nothing else),
then link → log → index → check.
```

- [ ] **Step 4: Remove the xfail and run the family gate**

Remove the `@pytest.mark.xfail(...)` decorator from `test_at_least_one_skill_exists` in `cli/tests/test_skill_family.py`.

Run: `cd cli && uv run --group dev pytest tests/test_skill_family.py -v`
Expected: all passing — fusion-intake now has SKILL.md, conventions card, compliant frontmatter, ≤500-line body, no personal paths.

- [ ] **Step 5: Validate against the agentskills.io reference validator**

Run: `uvx --from skills-ref agentskills validate skills/fusion-intake`
Expected: valid. If the tool is unavailable offline, note it in the report; the family test covers the same rules.

- [ ] **Step 6: Commit**

```bash
git add skills/fusion-intake cli/tests/test_skill_family.py
git commit -m "fusion-intake: SKILL.md + Stage-2 gate and conversion protocols"
```

---

### Task 5: Intake acceptance — the gate proven on real formats

**Files:**
- Create: `skills/fusion-intake/tests/test_integration.py`
- Create: `docs/acceptance/2026-07-10-phase-3-intake.md`

**Interfaces:**
- Consumes: everything from Tasks 2–4, verbatim — this task EXERCISES the skill; it changes skill code only by looping defects back through review.

This is ROADMAP gate line 3: "Intake gate proven on real legacy formats (xlsx, docx, pdf, csv)." Two halves: a scripted integration test (deterministic pipeline, CLI as oracle) and a played acceptance run (you, following SKILL.md like a user's agent would, on a scratch bucket).

- [ ] **Step 1: Write the integration test**

```python
"""End-to-end: real formats through gate -> admit -> prepare -> link,
with the fusion CLI as the conformance oracle. Requires the repo checkout
(uses uv --project cli); skipped outside it."""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
from conftest import bucket  # noqa: F401

import convert
import gate
import make_fixtures as fx

REPO = Path(__file__).resolve().parents[3]
CLI = REPO / "cli"
HAVE_CLI = (CLI / "pyproject.toml").is_file()


def fusion(*args, cwd):
    return subprocess.run(
        ["uv", "run", "--project", str(CLI), "fusion", *args],
        cwd=str(cwd), capture_output=True, text=True, timeout=120,
        env={**os.environ, "FUSION_ACTOR": "claude"},
    )


@pytest.mark.skipif(not HAVE_CLI, reason="fusion CLI checkout not found")
def test_real_formats_end_to_end(bucket):
    drops = {
        "scores.xlsx": fx.make_xlsx,
        "inventory.csv": fx.make_csv,
        "audit.pdf": fx.make_text_pdf,
        "mail.eml": fx.make_eml,
    }
    if shutil.which("soffice"):
        drops["procedure.docx"] = fx.make_docx
    for name, maker in drops.items():
        maker(bucket / "inbox" / name)

    # Stage-1 gate: all clean_new on an empty sources/
    idx = gate.index_sources(bucket / "sources")
    buckets = gate.classify_intake(bucket / "inbox", bucket / "sources", idx)
    assert len(buckets["clean_new"]) == len(drops)

    for name in drops:
        rec = convert.admit(bucket, name, category="records", actor="claude")
        out = convert.prepare(bucket, rec["source"])
        if out["done"]:
            doc_rel = out["output_file"]
        else:
            # Deterministic stand-in for the vision half: text pages only.
            body = "\n\n".join(
                p["text"] for p in out["pages"]) or "*(image content)*"
            doc_rel = out["output_file"]
            doc = bucket / doc_rel
            doc.parent.mkdir(parents=True, exist_ok=True)
            doc.write_text(convert.render_document(
                out["front_matter_seed"],
                "Converted for the integration run.", body), encoding="utf-8")
            convert.cleanup(bucket / out["run_dir"])
        convert.link(bucket, rec["source"], doc_rel)
        r = fusion("log", "converted",
                   f"sources/{rec['source']} → {doc_rel}", cwd=bucket)
        assert r.returncode == 0, r.stderr

    r = fusion("index", cwd=bucket)
    assert r.returncode == 0, r.stderr
    r = fusion("check", str(bucket), "--json", cwd=bucket)
    assert r.returncode == 0, f"check not green:\n{r.stdout}\n{r.stderr}"
    report = json.loads(r.stdout)
    assert report["errors"] == [] and report["warnings"] == []

    # inbox cleared last — everything green, so clear and re-check
    for name in drops:
        (bucket / "inbox" / name).unlink()
    r = fusion("check", str(bucket), cwd=bucket)
    assert r.returncode == 0
```

Note: if `fusion check --json` emits different top-level keys (verify with `uv run --project cli fusion check examples/crazy-ones --json` first), adapt the two assertion lines to the real keys — the CLI is the oracle, the test bends to it.

- [ ] **Step 2: Run it**

Run: `uv run --with pytest --with pyyaml --with openpyxl --with pymupdf pytest skills/fusion-intake/tests/test_integration.py -v`
Expected: 1 passed (docx leg included — soffice is present).

- [ ] **Step 3: Play the acceptance run (agent-in-the-loop)**

You (the implementer) now ACT AS the intake skill on a live scratch bucket, following `skills/fusion-intake/SKILL.md` and its references exactly — no shortcuts, no reading the scripts' source. Sandbox first:

```bash
export FUSION_HUB=/tmp/fusion-accept/hub.md FUSION_ACTOR=claude
mkdir -p /tmp/fusion-accept
cd "$(git rev-parse --show-toplevel)"   # the fusion repo root — never write the absolute path into committed files
uv run --project cli fusion new /tmp/fusion-accept/intake-demo --kind personal --description "Intake acceptance bucket."
uv run skills/fusion-intake/tests/make_fixtures.py   # then move fixtures-preview/* into /tmp/fusion-accept/intake-demo/inbox/
```

Scenarios (all six, in order):
1. **Clean new xlsx + csv + pdf + docx + eml** — full pipeline per SKILL.md; every close step's `fusion check` green; ledger shows one `converted` entry per file signed `claude`; MANIFEST rows complete with full sha256; INDEX regenerated. For the pdf and docx, actually Read the rendered page images where `needs_vision` and reconstruct; verify numbers verbatim against the fixtures.
2. **Exact duplicate** — re-drop `scores.xlsx`; gate auto-skips, no prompt, report records it.
3. **Near duplicate** — drop a lightly-edited csv under a new name; gate STOPS and asks (in the transcript, note where you would ask and pick "skip").
4. **Update** — drop `2026-07-09_inventory.csv` (same normalized name, half content changed): gate proposes supersede + reconcile; play the confirmed path; verify ONE library document, `updated:` bumped, two MANIFEST rows, both sources present.
5. **Conflict** — drop a csv restating a figure from scenario 1 with a different value; gate classifies conflicting, presents both claims, converts nothing.
6. **Unsupported format** — drop `mystery.xyz`; the engine refuses loudly; file stays in inbox.

- [ ] **Step 4: Write the acceptance transcript**

`docs/acceptance/2026-07-10-phase-3-intake.md`: per scenario — commands run, gate classifications, the intake report you produced, `fusion check` results, ledger tail, MANIFEST tail. End with a verdict line and any frictions found (frictions feed the Phase-4 list). Use `/tmp/...` paths only; actor `claude`.

- [ ] **Step 5: Clean up and commit**

```bash
rm -rf /tmp/fusion-accept fixtures-preview
git add skills/fusion-intake/tests/test_integration.py docs/acceptance/
git commit -m "fusion-intake: integration test + acceptance run on real formats"
```

---
### Task 6: fusion-librarian — the accountable owner

**Files:**
- Create: `skills/fusion-librarian/SKILL.md`
- Create: `skills/fusion-librarian/references/query.md`, `create.md`, `tag.md`, `cross-reference.md`, `promote.md`, `archive.md`, `restructure.md`, `reflect.md`
- Create: `skills/fusion-librarian/references/fusion-conventions.md` — COPY, never retype:

```bash
mkdir -p skills/fusion-librarian/references
cp skills/fusion-intake/references/fusion-conventions.md skills/fusion-librarian/references/
```

**Interfaces:**
- Consumes: the conventions card (Task 1); the `fusion` CLI.
- Produces: the complete librarian skill; Task 7 exercises it verbatim.

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: fusion-librarian
description: "The Fusion librarian — the accountable owner of a bucket's order. One entry, eight gears: query (natural-language search over the bucket — the default), create (a new conformant document), tag (bulk frontmatter metadata), cross-reference (map what relates to what), promote (workbench → a real zone, validated), archive (out of the way, path + aurora agreeing), restructure (reorganize and sign your reasons), reflect (the reflection ritual: introspect the ledger, propose curation, land what was learned). Use for 'find', 'search', 'where is', 'create a document', 'tag', 'what links to', 'promote', 'archive this', 'reorganize', 'restructure', 'run a reflection'. For files arriving from outside use fusion-intake; for activity planning use fusion-planner; for reports and exports use fusion-analyst."
license: MIT
compatibility: "Requires the fusion CLI on PATH."
---

# fusion-librarian — the owner

The agent is the librarian: not a search box, an accountable owner. Clean,
bold, opinionated structures — and every structural act signed in the
ledger with its reasons.

Read `references/fusion-conventions.md` once per session. Before any gear:
read the bucket's `BUCKET.md` — `### Rules` bind how this bucket files
things; `### Delegations` say what you may do without asking.

## Pick the gear

Explicit intent beats inference. Bare or ambiguous intent defaults to
**query** — the one gear that changes nothing.

| Signal | Gear | Load |
|---|---|---|
| find / search / where is / what do we know about | query (default) | references/query.md |
| create / new document / write down | create | references/create.md |
| tag / label / set field across docs | tag | references/tag.md |
| what links to / related / map connections | cross-reference | references/cross-reference.md |
| promote / finalize / move out of workbench | promote | references/promote.md |
| archive / put away / done with this | archive | references/archive.md |
| reorganize / restructure / new taxonomy | restructure | references/restructure.md |
| reflect / reflection / review the bucket | reflect | references/reflect.md |

Destructive gears — promote, archive, restructure — are never reached by
near-miss inference: if you arrived at one without the user naming it,
stop and confirm by name. reflect proposes destructive acts but executes
them only on a yes (or a standing delegation).

## Ledger discipline (which hat, which verb)

| Gear | Verb logged |
|---|---|
| create | `created` |
| tag | `classified` |
| promote | `promoted` |
| archive | `archived` |
| restructure | `restructured` — always with a `--note` giving the reasons |
| reflect | `reflected` to sign the cycle; `noted` for each convention change |
| query / cross-reference | nothing — reading is free |

All writes via `fusion log … --as <you>`. After any gear that adds, moves,
or edits documents: `fusion index`, then `fusion check` — green before you
report done.

## Never

- Never hand-edit `LEDGER.md`, `INDEX.md`, or `MANIFEST.md`.
- Never touch `sources/` — originals are immutable.
- Never restructure or archive without either a yes or a written
  delegation in BUCKET.md.
- Never leave `fusion check` red behind you.
```

- [ ] **Step 2: Write the eight gear references**

`references/query.md`:

```markdown
# query — answer from the bucket, cited

Read-only. Changes nothing, logs nothing.

1. Parse the question: entities, concepts, constraints (type, aurora,
   dates, status).
2. Triage via `library/INDEX.md` + `activities/INDEX.md` — titles and
   summary lines first. `fusion status` helps scope what exists.
3. Grep frontmatter for structured hits (`type:`, `aurora:`, `tags:`),
   then content for the rest.
4. Read the most relevant documents — summaries first, bodies only for
   the finalists (keep it under ~10 full reads).
5. Answer with a `## Sources` table: document path · what it contributed.
   Every claim cites a path. If the bucket is silent on part of the
   question, say what is known and what is missing — never fill gaps
   from your own general knowledge without labelling it as outside the
   bucket.
```

`references/create.md`:

```markdown
# create — a document born conformant

1. Establish title, type, aurora, and destination zone/folder. Infer type
   and folder from the bucket's existing taxonomy and BUCKET.md Rules;
   ask only when genuinely ambiguous. Aurora is the human-attention call —
   propose, and let an explicit instruction override.
2. Write the document: the three required fields (plus `created:` today,
   `tags:` when useful), `## Summary` (2–3 lines), `---`, then the body.
   Filename: lowercase-hyphen slug, ≤60 chars.
3. `fusion log created "<zone>/<path>" --as <you>` · `fusion index` ·
   `fusion check` green.
```

`references/tag.md`:

```markdown
# tag — bulk metadata, honestly reported

1. Parse the field and value; `--scope`-like constraints (a folder, a
   type) narrow the set. Value "auto" means you infer per document from
   its content — say so in the report.
2. Edit each document's frontmatter, preserving every existing key and
   the body untouched. `updated:` does NOT bump (metadata, not content).
3. Report a table: file · field · old → new.
4. One ledger entry for the batch:
   `fusion log classified "<scope> — <field>: <value> (<N> documents)" --as <you>`
   then `fusion index` (summaries unchanged, but titles/auroras may have
   moved in the index) and `fusion check`.
```

`references/cross-reference.md`:

```markdown
# cross-reference — map what relates to what

Read-only. For a target document or topic:

1. Extract its entities (names, projects, products, periods).
2. Sweep the bucket: direct mentions (grep), shared frontmatter values
   (type, tags, aurora), thematic kinship (summaries that talk about the
   same thing).
3. Report three buckets, every line carrying a path:
   **Direct references** · **Shared attributes** · **Thematic connections**.
4. Offer (don't apply) link edits: "these two documents should point at
   each other" — applying them is a content change the user approves,
   then edit, `fusion index`, `fusion check`.
```

`references/promote.md`:

```markdown
# promote — leaving the workbench is a deliberate act

workbench/ has no rules; the zones do. Promotion is the moment the rules
attach.

Pre-flight (all three, before anything moves):
1. Explicit invocation confirmed — arrived here by inference? Stop, ask.
2. Source is in `workbench/`; destination zone/folder named or clearly
   inferable from the document's nature (`library/` knowledge,
   `activities/` live work, `output/` deliverables). Ask if unclear.
3. State the plan in one sentence: "Promoting workbench/<x> to
   <zone>/<folder>/<slug>.md."

Validate BEFORE moving (strict writer — a failed check stops the
promotion, nothing moves):
- frontmatter parses; `title`, `type`, `aurora` present; aurora one of
  the eight; summary-first body; slug filename ≤60.
- activities documents: `status` present. output documents: encourage
  `data_sources`.
Fix what the user wants fixed, or leave it in the workbench.

Then: move the file (Write new + delete old, or `mv`), then
`fusion log promoted "workbench/<x> → <zone>/<path>" --as <you>` ·
`fusion index` · `fusion check` green.
```

`references/archive.md`:

```markdown
# archive — out of the way, never out of reach

Path is the truth, aurora is the signal — both, always, in one move.

1. Confirm the target and the authority: explicit ask, or a standing
   delegation in BUCKET.md `### Delegations` that covers this case
   (cite it in the note when you use it).
2. Move the document to `<its-zone>/archive/<same-folder-structure>/`.
3. Edit its frontmatter: `aurora: archive` (and `status: done` for an
   activity, if not already).
4. `fusion log archived "<zone>/<old> → <zone>/archive/<new>"
   [--note "delegation: <rule>"] --as <you>` · `fusion index` ·
   `fusion check` — the checker's W3 watches exactly this agreement.

Whole activities archive as a folder: `activities/archive/<name>/`, every
document inside taking `aurora: archive`.
```

`references/restructure.md`:

```markdown
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
   (grep for the old paths); keep filenames conformant.
4. **Sign.** One ledger entry for the operation:
   `fusion log restructured "<zone>/<scope>" --note "<the reason>" --as <you>`
   — the note is not optional here. Then `fusion index` and
   `fusion check` (W4 watches the links you just moved).
```

`references/reflect.md`:

```markdown
# reflect — the metabolism (SPEC §10)

The files remember → you reflect → the human judges → the system learns.
Run on the bucket's `reflection_cadence`, or when asked.

## 1. Introspect

```bash
fusion log --since last-reflection      # what happened this window
fusion status --since last-reflection   # counts, auroras, activities
fusion check <root>                     # drift: stale INDEX, W1 inbox age…
```

Read the window's ledger like telemetry: what got converted, promoted,
touched — and what never did.

## 2. Curate & prune — the proposal list

Propose, with paths and evidence, whichever apply:
- workbench items older than the window → promote or expire;
- activities with `status: active` and no ledger touch → `dormant` or
  archive (W5 already names them);
- superseded or stale library documents → `archive/`;
- duplicates to merge, fat documents to split;
- summaries that no longer match their bodies;
- taxonomy that stopped serving → a restructure proposal;
- rules the window taught: "we always filed X under Y — make it a Rule?"
- delegations earned: acts the human approved repeatedly this window.

## 3. Judge

Present the list. Destructive and archival acts need a yes — EXCEPT where
`### Delegations` already grants it (cite the delegation, act, and note
it). Never bundle: the human can take proposal 3 and refuse proposal 4.

## 4. Learn & sign

- Approved rule/delegation changes: edit `BUCKET.md ## Conventions`, one
  `fusion log noted "BUCKET.md — <the change>" --as <you>` per change.
- Execute approved acts via their own gears (archive, restructure…) so
  each carries its own verb.
- Sign the cycle LAST:
  `fusion log reflected "<bucket> — <N> proposals, <M> adopted" --as <you>`
- Episodic reports are ephemeral: the proposal list lives in workbench/
  and can die there; only conventions and ledger entries persist.
```

- [ ] **Step 3: Copy the conventions card and run the family gate**

```bash
cp skills/fusion-intake/references/fusion-conventions.md skills/fusion-librarian/references/
cd cli && uv run --group dev pytest tests/test_skill_family.py -v
```
Expected: all passing (two skills discovered, cards byte-identical).

- [ ] **Step 4: Validate**

Run: `uvx --from skills-ref agentskills validate skills/fusion-librarian` — expected: valid (skip gracefully if offline).

- [ ] **Step 5: Commit**

```bash
git add skills/fusion-librarian
git commit -m "fusion-librarian: the owner — eight gears, signed structural acts"
```

---

### Task 7: Librarian acceptance — exercised on a scratch bucket

**Files:**
- Create: `docs/acceptance/2026-07-10-phase-3-librarian.md`

**Interfaces:**
- Consumes: fusion-librarian (Task 6) followed verbatim; the `fusion` CLI.

Play the librarian on a live scratch bucket. Same sandbox discipline as Task 5 (`FUSION_HUB=/tmp/fusion-accept/hub.md`, `FUSION_ACTOR=claude`, bucket at `/tmp/fusion-accept/librarian-demo`, created with `fusion new`).

- [ ] **Step 1: Seed** — create 4 documents via the **create** gear (two `library/gear/`, one `activities/lp-first-light/plan.md` with `status: active` + `aurora: focus`, one workbench draft `workbench/q3-ideas.md` WITHOUT frontmatter). Each create: ledger `created`, index, check green (workbench draft needs no conformance — verify check stays green precisely because workbench is ruleless).
- [ ] **Step 2: query** — ask "what do we know about the Jazzmaster?"; verify the answer cites paths and invents nothing.
- [ ] **Step 3: tag** — add `tags: [guitars]` across `library/gear/`; one `classified` ledger entry with count; check green.
- [ ] **Step 4: promote** — promote the workbench draft to `library/notes/q3-ideas.md`: the gear must STOP on missing frontmatter, you fix the draft (add the three fields + summary), re-promote, `promoted` logged, check green.
- [ ] **Step 5: archive** — archive one gear document: lands in `library/archive/gear/…`, `aurora: archive`, `archived` logged, check green (W3 silent).
- [ ] **Step 6: restructure** — rename `library/gear/` to `library/instruments/`: proposal with reasons shown, executed, links updated, `restructured` logged WITH note, check green.
- [ ] **Step 7: reflect** — run a full mini-reflection: introspect (`--since last-reflection`), propose (at least the dormant-activity and a new Rule "instruments are filed by make-model"), play the human's yes, land the Rule in BUCKET.md (`noted` logged), sign `reflected`. Verify `fusion log --since last-reflection` now shows an empty window.
- [ ] **Step 8: Transcript + commit** — write the transcript (commands, ledger tail after each gear, final `fusion check` + `fusion status` output; frictions list), then:

```bash
rm -rf /tmp/fusion-accept
git add docs/acceptance/2026-07-10-phase-3-librarian.md
git commit -m "fusion-librarian: acceptance run — eight gears on a scratch bucket"
```

---
### Task 8: fusion-planner — the horizon

**Files:**
- Create: `skills/fusion-planner/SKILL.md`
- Create: `skills/fusion-planner/references/create-activity.md`, `horizon.md`, `close.md`
- Create: `skills/fusion-planner/references/fusion-conventions.md` (cp, as in Task 6)

**Interfaces:**
- Consumes: conventions card; the `fusion` CLI (`today`, `agenda`, `status`, `log`, `index`, `check`).
- Produces: the complete planner skill; Task 10 exercises it.

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: fusion-planner
description: "The Fusion planner — the horizon keeper. The human drives activities; the planner structures them. Three gears: create-activity (a new activity folder with a stateful plan document — works for plans, campaigns, programs, agendas alike), horizon (review what's live: stalled activities, expiring commitments, what fusion today will show tomorrow), close (finish an activity: status done, archived, out of the way). Use for 'new project/activity/campaign', 'plan this', 'what's on my plate', 'review my activities', 'what's stalled', 'agenda', 'close/finish this activity'. For placing knowledge use fusion-librarian; for deliverables use fusion-analyst."
license: MIT
compatibility: "Requires the fusion CLI on PATH."
---

# fusion-planner — the horizon

Activities are live work: folders under `activities/`, stateful documents,
honest statuses. The planner keeps the horizon true — what `fusion today`
composes tomorrow morning is this skill's report card.

Read `references/fusion-conventions.md` once per session; read the
bucket's `BUCKET.md ## Conventions` before acting.

## Pick the gear

| Signal | Gear | Load |
|---|---|---|
| new activity / plan / campaign / program / agenda | create-activity | references/create-activity.md |
| what's live / stalled / on my plate / review activities (default) | horizon | references/horizon.md |
| close / finish / wrap up an activity | close | references/close.md |

The default is **horizon** — the read-only gear. close moves files;
reached by inference, it stops and confirms.

## The activity shape

```
activities/<slug>/
├── plan.md          # the stateful heart: status, dates, aurora
└── …                # notes, briefs — documents, same rules
```

`plan.md` frontmatter: the three required fields, plus `status:`
(`active` | `done` | `dormant`) and `due:` (ISO date) when a real deadline
exists. Aurora speaks for attention: `commitments` when promised,
`focus` when it is the deep work, `collab` when shared, `explore` when
tentative. Expandability is the shape, not machinery: a campaign is an
activity whose plan has phases; an agenda is an activity whose plan is
dated items.

## Ledger discipline

| Act | Verb |
|---|---|
| new activity | `created` |
| status change (active ⇄ dormant, honest corrections) | `noted` with the change in the note |
| close | `archived` |

Always `--as <you>`, then `fusion index` and `fusion check` green.

## Never

- Never let a dead activity keep `status: active` — the horizon lies.
- Never set `due:` the human didn't state or clearly imply.
- Never hand-edit the registers.
```

- [ ] **Step 2: Write the three references**

`references/create-activity.md`:

```markdown
# create-activity — structure the human's intent

1. Get the essentials from the conversation: name (→ slug), what done
   looks like, deadline (if promised), who else is involved. Ask only
   what the human hasn't said.
2. Choose aurora: promised-with-deadline → `commitments`; the current
   deep work → `focus`; shared → `collab`; tentative → `explore`. Say
   which and why in one line.
3. Create `activities/<slug>/plan.md`:

   ```markdown
   ---
   title: <name>
   type: plan
   aurora: <chosen>
   status: active
   created: <today>
   due: <date, only if real>
   ---

   ## Summary

   <what this activity is and what done looks like, 2–3 lines>

   ---

   ## Steps

   - [ ] <the first concrete steps, from the conversation>

   ## Log

   - <today> — created.
   ```

4. `fusion log created "activities/<slug>/plan.md" --as <you>` ·
   `fusion index` · `fusion check` green. Then show the human what
   `fusion today` now includes.
```

`references/horizon.md`:

```markdown
# horizon — keep today honest

Read-mostly; proposes, changes nothing without a yes.

1. `fusion agenda` — dated items and undated actives across buckets;
   `fusion today` — the attention view; `fusion status --since
   last-reflection` for the recent pulse of this bucket.
2. Read `activities/INDEX.md` + each active plan's summary. For each
   active activity judge: moving (recent ledger touches), **stalled**
   (active but untouched — W5's territory), **expiring** (due within a
   week), **done-in-fact** (finished but never closed).
3. Report the horizon in four short lists with paths and dates. No
   invented urgency: expiring means a real `due:`, stalled means real
   silence.
4. Propose the honest corrections: dormant flips, closes, due-date fixes.
   On yes: edit the frontmatter, `fusion log noted "activities/<slug> —
   status: active → dormant" --as <you>` per flip · `fusion index` ·
   `fusion check`. Closes go through the close gear.
```

`references/close.md`:

```markdown
# close — done, kept, out of the way

1. Confirm the target activity and that the human means finished (or a
   Delegation covers routine closes). State the plan in one sentence.
2. Edit `plan.md` (and any sibling documents): `status: done`,
   `aurora: archive`. Add a final Log line summarizing the outcome.
3. Move the whole folder to `activities/archive/<slug>/`.
4. `fusion log archived "activities/<slug>/ → activities/archive/<slug>/"
   --as <you>` · `fusion index` · `fusion check` green — path and aurora
   agree or W3 objects.
5. If deliverables shipped from this activity, remind the human where
   they live in `output/` (the analyst's ledger entries say).
```

- [ ] **Step 3: Copy the card, gate, validate, commit**

```bash
mkdir -p skills/fusion-planner/references
cp skills/fusion-intake/references/fusion-conventions.md skills/fusion-planner/references/
cd cli && uv run --group dev pytest tests/test_skill_family.py -v && cd ..
uvx --from skills-ref agentskills validate skills/fusion-planner || true
git add skills/fusion-planner
git commit -m "fusion-planner: the horizon — create-activity, horizon, close"
```

---

### Task 9: fusion-analyst — the output

**Files:**
- Create: `skills/fusion-analyst/SKILL.md`
- Create: `skills/fusion-analyst/references/report.md`, `assess.md`, `compare.md`, `export.md`
- Create: `skills/fusion-analyst/scripts/export.py`
- Create: `skills/fusion-analyst/references/fusion-conventions.md` (cp)
- Test: export.py gets an inline bash smoke test (Step 4); the family gate already covers structure.

**Interfaces:**
- Consumes: conventions card; the CLI.
- Produces: the complete analyst skill; Task 10 exercises it.

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: fusion-analyst
description: "The Fusion analyst — deliverables out of the bucket. Four gears: report (multi-section analysis from library + activities — the default), assess (scored assessment with explicit criteria and scale), compare (side-by-side matrix with deltas and red flags), export (CSV/JSON/XLSX data extracts). Everything lands in output/ as a summary-first document, cites every source path in data_sources, and ships signed in the ledger. Use for 'report on', 'analyze and write up', 'brief', 'assess', 'evaluate', 'score', 'compare X and Y', 'export as csv/excel'. For searching without producing a deliverable use fusion-librarian's query; for new documents of record use fusion-librarian's create."
license: MIT
compatibility: "Requires the fusion CLI on PATH; uv for the export script (PEP 723: openpyxl)."
---

# fusion-analyst — the output

Deliverables leave the bucket; their evidence never does. Every analyst
document cites the exact paths it was built from, and ships with a
`shipped` ledger entry.

Read `references/fusion-conventions.md` once per session; read
`BUCKET.md ## Conventions` before acting.

## Pick the gear

| Signal | Gear | Load |
|---|---|---|
| report / analyze / write up / brief (default) | report | references/report.md |
| assess / evaluate / score / rate | assess | references/assess.md |
| compare / versus / side by side | compare | references/compare.md |
| export / as csv / as excel / as json | export | references/export.md |

## The output contract (all four gears)

- Deliverables are documents in `output/` — frontmatter `title`, `type`,
  `aurora` (usually `library` for reference-grade output, `commitments`
  when it answers a promise), `created`, and **`data_sources`: the YAML
  list of every bucket path the deliverable was built from.** No
  uncited claims: if it isn't in a listed source, it is labelled as the
  analyst's own inference.
- Drafts live in `workbench/` while the human iterates; the finished
  piece moves to `output/` (that move is the librarian's promote gear if
  the human asks for the full ceremony, or written directly to `output/`
  when the ask was a deliverable from the start).
- Sign every deliverable:
  `fusion log shipped "output/<path>" --as <you>` · `fusion index` ·
  `fusion check` green.

## Never

- Never invent data — the bucket is the evidence, `data_sources` is the
  warrant.
- Never overwrite an existing deliverable silently; new version, new
  name, or an explicit yes.
- Never hand-edit the registers.
```

- [ ] **Step 2: Write the four references**

`references/report.md`:

```markdown
# report — from bucket to briefing

1. Scope: topic, audience, depth. A "brief" is a report whose audience
   is management: two pages, headline numbers first, no methodology.
2. Gather: INDEX triage → grep → read the relevant documents. Keep the
   list of every path you actually used — that IS `data_sources`.
3. Write to `output/reports/<slug>.md` (or workbench first if the human
   is iterating):
   `## Summary` (the 2–3-line triage), `---`, then: Key findings
   (numbers verbatim from sources) · Analysis · Recommendations ·
   `## Sources` (path · contribution — mirrors data_sources).
4. Close: `fusion log shipped "output/reports/<slug>.md" --as <you>` ·
   `fusion index` · `fusion check`.
```

`references/assess.md`:

```markdown
# assess — scored, scaled, evidenced

1. Subject + criteria + scale. No scale given → 1–5 integers
   (1 very poor … 5 excellent) and SAY SO at the top of the document.
2. Evidence per criterion from the bucket (paths kept for data_sources).
   A criterion without evidence scores nothing — mark it "no evidence
   in bucket" instead of guessing.
3. Write `output/assessments/<slug>.md`: summary + `---` + scores table
   (criterion · score · evidence path) + per-criterion rationale +
   `## Sources`.
4. `fusion log shipped …` · `fusion index` · `fusion check`.
```

`references/compare.md`:

```markdown
# compare — the matrix that shows its work

1. Items + criteria (ask for criteria only if the obvious set is
   ambiguous). Normalize units and scales before comparing; say when a
   normalization changes a number's face.
2. Matrix: criterion · item A · item B · delta. Below it: strengths,
   weaknesses, and red flags (crippling conditions get named, not
   averaged away).
3. Inline answer for a quick question; `output/reports/<slug>.md` with
   the full contract when it is a deliverable.
4. Deliverable path: `fusion log shipped …` · `fusion index` ·
   `fusion check`.
```

`references/export.md`:

```markdown
# export — data that leaves as data

1. Scope the rows: which documents, which frontmatter fields / table
   columns. Collect into JSON: `{"headers": […], "rows": [[…], …]}`.
2. Pipe through the script:

   ```bash
   echo '<json>' | uv run <skill>/scripts/export.py --format xlsx \
     --output output/exports/<slug>.xlsx
   ```

   Formats: csv (default), json, xlsx.
3. Write the companion document `output/exports/<slug>.md` — summary of
   what the export contains + `resource:` naming the binary +
   `data_sources` listing every source path. The binary is data; the
   document is its passport.
4. `fusion log shipped "output/exports/<slug>.xlsx" --as <you>` ·
   `fusion index` · `fusion check`.
```

- [ ] **Step 3: Write scripts/export.py**

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["openpyxl>=3.1.0"]
# ///
"""fusion-analyst export: stdin JSON {"headers": [...], "rows": [[...]]}
-> csv / json / xlsx on disk. Deterministic; the judgment (what to export)
happened before the pipe."""
import argparse
import csv
import json
import sys
from pathlib import Path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="fusion-analyst data export")
    ap.add_argument("--format", "-f", choices=("csv", "json", "xlsx"),
                    default="csv")
    ap.add_argument("--output", "-o", required=True)
    args = ap.parse_args(argv)

    payload = json.load(sys.stdin)
    headers = payload.get("headers") or []
    rows = payload.get("rows") or []
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    if args.format == "csv":
        with open(out, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            if headers:
                w.writerow(headers)
            w.writerows(rows)
    elif args.format == "json":
        records = ([dict(zip(headers, r)) for r in rows]
                   if headers else rows)
        out.write_text(json.dumps(records, indent=2, ensure_ascii=False),
                       encoding="utf-8")
    else:
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "export"
        if headers:
            ws.append(headers)
        for r in rows:
            ws.append(r)
        wb.save(out)

    print(json.dumps({"written": str(out), "rows": len(rows),
                      "format": args.format}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Smoke-test the script**

```bash
echo '{"headers":["a","b"],"rows":[[1,2],["x","y"]]}' | \
  uv run skills/fusion-analyst/scripts/export.py -f csv -o /tmp/e.csv && cat /tmp/e.csv
echo '{"headers":["a"],"rows":[[1]]}' | \
  uv run skills/fusion-analyst/scripts/export.py -f xlsx -o /tmp/e.xlsx && rm /tmp/e.csv /tmp/e.xlsx
```
Expected: csv shows `a,b` / `1,2` / `x,y`; both commands print a `{"written": …}` JSON line.

- [ ] **Step 5: Copy the card, gate, validate, commit**

```bash
mkdir -p skills/fusion-analyst/references
cp skills/fusion-intake/references/fusion-conventions.md skills/fusion-analyst/references/
cd cli && uv run --group dev pytest tests/test_skill_family.py -v && cd ..
uvx --from skills-ref agentskills validate skills/fusion-analyst || true
git add skills/fusion-analyst
git commit -m "fusion-analyst: the output — report, assess, compare, export"
```

---

### Task 10: Planner + analyst acceptance

**Files:**
- Create: `docs/acceptance/2026-07-10-phase-3-planner-analyst.md`

**Interfaces:**
- Consumes: fusion-planner (Task 8) and fusion-analyst (Task 9), followed verbatim.

Same sandbox discipline (`FUSION_HUB=/tmp/fusion-accept/hub.md`, `FUSION_ACTOR=claude`); one bucket `/tmp/fusion-accept/horizon-demo` via `fusion new`; seed two library documents by hand (conformant) so the analyst has evidence.

- [ ] **Step 1: create-activity** — "prepare the LP listening session, due 2026-07-24, it's a promise" → `activities/lp-listening/plan.md`, `aurora: commitments`, `status: active`, `due: 2026-07-24`; `created` logged; check green; `fusion today` shows it under commitments and `fusion agenda` dates it.
- [ ] **Step 2: second activity + horizon** — create a `focus` activity with no due; then run **horizon**: verify the report lists both correctly (one dated, one undated-active), nothing stalled (fresh bucket), no invented urgency. Play a dormant flip on the focus activity: `noted` logged with the status change; `fusion today` drops it.
- [ ] **Step 3: analyst report** — "report on what's in the library" → `output/reports/…md` with `data_sources` listing the two seeded docs, `## Sources` table, `shipped` logged, check green.
- [ ] **Step 4: assess** — score the two library items on 2 criteria, default 1–5 scale stated at top; `shipped`; check green.
- [ ] **Step 5: export** — export the library docs' `title`+`type` as csv via the script; companion `.md` with `resource:` + `data_sources`; `shipped`; check green. (The csv itself lives in `output/exports/` — verify `fusion check` treats the non-md file as invisible-to-E8/W-rules; if the checker objects to a non-document in output/, that is a REAL finding: report it, and the resolution belongs to the human — do not mutate the checker to pass.)
- [ ] **Step 6: close** — close the commitments activity through the planner's close gear: folder in `activities/archive/lp-listening/`, `status: done`, `aurora: archive`, `archived` logged, check green; `fusion today` no longer shows it.
- [ ] **Step 7: Transcript + commit**

```bash
rm -rf /tmp/fusion-accept
git add docs/acceptance/2026-07-10-phase-3-planner-analyst.md
git commit -m "fusion-planner + fusion-analyst: acceptance runs on a scratch bucket"
```

---

### Task 11: Docs close-out — README, ROADMAP gate, family README truthfulness pass

**Files:**
- Modify: `README.md` (root — the Status table's Phase 3 row)
- Modify: `docs/ROADMAP.md` (Phase 3 gate checkboxes)
- Modify: `skills/README.md` (only if Tasks 4–10 changed any fact in it)

**Interfaces:**
- Consumes: the completed skills and acceptance transcripts.

- [ ] **Step 1: Verify each Phase 3 gate line before ticking it** — run the evidence, don't trust memory:

```bash
cd cli && uv run --group dev pytest tests/test_skill_family.py -q && cd ..   # duplication check green
ls docs/acceptance/                                                          # three transcripts exist
uv run --with pytest --with pyyaml --with openpyxl --with pymupdf \
  pytest skills/fusion-intake/tests/ -q                                      # intake proven incl. real formats
```

For "Skills reviewed against the writing-skills quality bar": this is satisfied by the per-task and final reviews of this phase — cite the review reports in the commit message body, not by self-assertion.

- [ ] **Step 2: Tick the four Phase 3 gate boxes in docs/ROADMAP.md** (only those verified above).

- [ ] **Step 3: Update root README.md Status row** for Phase 3 to `✅ skills + gate` (match the phrasing pattern the table already uses for Phases 1–2).

- [ ] **Step 4: Re-read skills/README.md against reality** — command names, requirement claims, install path. Fix drift.

- [ ] **Step 5: Full-repo verification**

```bash
cd cli && uv run --group dev pytest -q && cd ..
uv run --with pytest --with pyyaml --with openpyxl --with pymupdf pytest skills/fusion-intake/tests/ -q
uv run --project cli fusion check examples/crazy-ones
grep -ri "bertrand\|/Users/" skills/ docs/acceptance/ && echo LEAK || echo clean
```
Expected: all green; fixture untouched (`git status` clean apart from staged docs); `clean`.

- [ ] **Step 6: Commit**

```bash
git add README.md docs/ROADMAP.md skills/README.md
git commit -m "docs: Phase 3 gate green — skill family shipped"
```
