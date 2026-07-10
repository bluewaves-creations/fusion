# Bucket Scenarios Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps
> use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the four gaps found in the 2026-07-11 bucket-lifecycle
review: the skills' bucket guard blocks the onboarding conversation, git
sync has an undefined ledger-merge story, dangling hub entries vanish
silently, and the external-project `resource:` pattern is invisible.

**Architecture:** Four thin, independent improvements to the existing
system — no new commands beyond a `--hub` mode on `fusion check`, no new
skills, no new zones. The scaffold gains a `.gitattributes` (git's
built-in union merge driver absorbs parallel ledger/manifest appends);
the hub's consumers report what they skip; the guard paragraph in all
four skills turns from a wall into a door; the normative example bucket
gains the one activity shape it was missing.

**Tech Stack:** Python 3.11+ (uv-managed), pytest, markdown. No new
dependencies.

**User decisions (2026-07-11, do not relitigate):**

- Sync depth: scaffold writes `.gitattributes` + docs + a SPEC §6/§7 note.
- Worked example: real activity in `examples/crazy-ones` + planner
  reference (pinned tests updated).
- Dangling hub entries: surfaced in `fusion hub`, `fusion today`,
  `fusion agenda`, AND `fusion check` (hub mode).

## Global Constraints

- Voice: warm-terse declarative, **no exclamation marks**, prose
  hand-wrapped at ~76 characters (match each file's existing wrap).
- `skills/*/references/fusion-conventions.md` ×4 MUST stay byte-identical
  (`cli/tests/test_skill_family.py::test_conventions_cards_byte_identical`).
- Skill descriptions MUST stay ≤1024 characters (same test file).
- No `/Users/` paths and no `bertrand` anywhere under `skills/`
  (`test_no_personal_paths`); `bertrand` IS allowed in `examples/` (the
  fictional example actor — user's decision, kept).
- All committed text files LF-only (`.gitattributes` at repo root pins
  it); every Python write of bucket files uses
  `encoding="utf-8", newline="\n"`.
- Registers are single-writer: never hand-run `fusion index` or
  `fusion log` against `examples/crazy-ones` (a real ledger entry with
  the real machine user would leak in). Regenerate the fixture INDEX via
  `indexer.write_indexes(root, actor=None)` (logs nothing), and author
  fixture LEDGER lines as file edits in chronological position.
- SPEC.md stays **Version 1.0** — the §6/§7 additions describe scaffold
  behavior and restate liberal-reader tolerance; they add no new
  requirement on existing buckets, so no version bump and no
  `fusion_version` ripple.
- QA bar before the final review: `cd cli && uv run pytest` green
  (167 tests + this plan's additions), `uv run fusion check
  ../examples/crazy-ones` prints `0 errors · 0 warnings`, intake suite
  (77) and librarian suite (22) untouched and green.
- Working branch: create `bucket-scenarios` off `main`; do not push
  (user pushes manually unless they authorize).

## File Structure

| File | Change |
|---|---|
| `cli/src/fusion/scaffold.py` | write `.gitattributes` at bucket birth |
| `cli/src/fusion/checker.py` | `check_hub()` + H-code note on `Finding` |
| `cli/src/fusion/views.py` | `missing_hub_entries()`; `today()`/`agenda()` report skips |
| `cli/src/fusion/cli.py` | hub-list annotation, today/agenda stderr notes, `check --hub` + outside-bucket fallback |
| `cli/tests/test_scaffold.py` | gitattributes test |
| `cli/tests/test_checker_warnings.py` | `check_hub` tests |
| `cli/tests/test_views.py` | missing-entry reporting + fixture count updates |
| `cli/tests/test_cli.py` | hub/check/today/agenda contract updates + fixture counts |
| `cli/tests/test_ledger.py`, `cli/tests/test_hub_bucket.py` | fixture count updates |
| `skills/*/SKILL.md` ×4 | guard paragraph + description tail |
| `skills/*/references/fusion-conventions.md` ×4 | no-bucket bullet, sync note, crib row (byte-identical) |
| `skills/fusion-planner/references/create-activity.md` | external-project section |
| `SPEC.md` | §6 union-merge note, §7 manifest-merge sentence |
| `examples/crazy-ones/` | `.gitattributes`, `activities/band-site/plan.md`, LEDGER lines, INDEX regen |
| `docs/BUCKETS-EVERYWHERE.md` | new field guide |
| `docs/README.md`, `docs/GETTING-STARTED.md`, `README.md` | link the field guide |
| `docs/dogfood/frictions.md` | friction #9 row |

---

### Task 1: Born syncable — `.gitattributes` at birth + SPEC note

**Files:**
- Modify: `cli/src/fusion/scaffold.py`
- Modify: `cli/tests/test_scaffold.py`
- Modify: `SPEC.md` (§6, §7)
- Create: `examples/crazy-ones/.gitattributes`

**Interfaces:**
- Produces: `scaffold.GITATTRIBUTES` (module constant, exact bytes below)
  — Task 5's docs quote its content; the fixture copy must be identical.

- [ ] **Step 1: Write the failing test**

Append to `cli/tests/test_scaffold.py` (match its existing style — it
already imports `new_bucket` and uses `tmp_path` + an autouse hub
monkeypatch):

```python
def test_new_bucket_writes_gitattributes(tmp_path):
    root, _ = new_bucket(tmp_path / "b", description="d", actor="test")
    text = (root / ".gitattributes").read_text(encoding="utf-8")
    assert "LEDGER.md merge=union" in text
    assert "sources/MANIFEST.md merge=union" in text
    assert "* text=auto eol=lf" in text
    assert "\r" not in text
```

If the file's existing tests import `new_bucket` differently (e.g.
`from fusion.scaffold import new_bucket`), follow the file.

- [ ] **Step 2: Run it to make sure it fails**

Run: `cd cli && uv run pytest tests/test_scaffold.py -v`
Expected: the new test FAILS with `FileNotFoundError` on `.gitattributes`.

- [ ] **Step 3: Implement**

In `cli/src/fusion/scaffold.py`, add the constant after
`MANIFEST_HEADER`:

```python
GITATTRIBUTES = (
    "# written by fusion new — multi-machine merges stay safe (SPEC §6)\n"
    "* text=auto eol=lf\n"
    "LEDGER.md merge=union\n"
    "sources/MANIFEST.md merge=union\n"
)
```

In `new_bucket()`, right after the `sources/MANIFEST.md` write:

```python
    (root / ".gitattributes").write_text(
        GITATTRIBUTES, encoding="utf-8", newline="\n"
    )
```

(Before the ledger/index/git steps, so the birth commit includes it.)

- [ ] **Step 4: Run the scaffold suite**

Run: `cd cli && uv run pytest tests/test_scaffold.py -v`
Expected: ALL PASS.

- [ ] **Step 5: Give the example bucket the same file**

Create `examples/crazy-ones/.gitattributes` with byte-identical content
to `GITATTRIBUTES` (the fixture is what `fusion new` produces, lived-in).

Verify the fixture stays clean:
`cd cli && uv run fusion check ../examples/crazy-ones`
Expected: `crazy-ones: 0 errors · 0 warnings — clean, carry on.`
(dotfiles are invisible to the checker — SPEC §11 exemptions.)

- [ ] **Step 6: SPEC §6 — the union-merge note**

In `SPEC.md` §6, after the `restructured` bullet (the last bullet of the
section), append this paragraph:

```markdown
A bucket that lives on more than one machine merges parallel work with
git's built-in union driver: the reference scaffold writes a
`.gitattributes` at bucket birth marking `LEDGER.md merge=union` (and
the manifest, §7), so entries appended on both machines survive the
merge. The merged ledger may briefly hold two headings for the same
date — consumers already tolerate this (liberal reader); it is the
honest record of parallel work. A union merge is the only way LEDGER.md
bytes change outside the one writer.
```

- [ ] **Step 7: SPEC §7 — one sentence**

In `SPEC.md` §7, append to the second bullet (the `library` column
bullet) a new sibling bullet:

```markdown
- On multi-machine buckets the manifest merges with the same union
  driver as the ledger (§6): rows admitted on two machines both survive.
```

- [ ] **Step 8: Full CLI suite + commit**

Run: `cd cli && uv run pytest -q` — expected: all green.

```bash
git add cli/src/fusion/scaffold.py cli/tests/test_scaffold.py SPEC.md examples/crazy-ones/.gitattributes
git commit -m "feat: buckets are born syncable — union-merge .gitattributes at birth, SPEC §6/§7 note"
```

---

### Task 2: Hub truth — dangling entries surface everywhere

**Files:**
- Modify: `cli/src/fusion/checker.py`
- Modify: `cli/src/fusion/views.py`
- Modify: `cli/src/fusion/cli.py`
- Modify: `cli/tests/test_checker_warnings.py`, `cli/tests/test_views.py`,
  `cli/tests/test_cli.py`

**Interfaces:**
- Consumes: `hub.load()`, `hub.resolve(entry)`, `hub.hub_path()`,
  `bucket.load(root)` (existing).
- Produces: `checker.check_hub() -> list[Finding]` (H1 dangling,
  H2 name drift, both `level="warning"`);
  `views.missing_hub_entries() -> list[dict]` (`{"name", "path"}`);
  `today()`/`agenda()` payloads gain a `"missing"` key;
  `fusion hub --json` entries gain a `"missing"` bool;
  `fusion check --hub` (and `fusion check` outside any bucket with no
  path) audits the hub and exits 0.

- [ ] **Step 1: Write the failing tests**

Append to `cli/tests/test_checker_warnings.py`:

```python
def test_check_hub_dangling_and_drift(tmp_path, monkeypatch):
    from fusion import checker, hub
    from fusion.scaffold import new_bucket

    monkeypatch.setenv("FUSION_HUB", str(tmp_path / "hub.md"))
    new_bucket(tmp_path / "here", description="d", actor="test")
    hub.add(hub.HubEntry("ghost", "personal", str(tmp_path / "gone"), "x"))
    drifted, _ = new_bucket(tmp_path / "drift", name="oldname",
                            description="d", actor="test")
    text = (drifted / "BUCKET.md").read_text(encoding="utf-8")
    (drifted / "BUCKET.md").write_text(
        text.replace("name: oldname", "name: newname"), encoding="utf-8"
    )
    findings = checker.check_hub()
    assert [(f.code, f.level) for f in findings] == [
        ("H1", "warning"), ("H2", "warning")
    ]
    assert "ghost" in findings[0].message
    assert "newname" in findings[1].message


def test_check_hub_all_present_is_empty(tmp_path, monkeypatch):
    from fusion import checker
    from fusion.scaffold import new_bucket

    monkeypatch.setenv("FUSION_HUB", str(tmp_path / "hub.md"))
    new_bucket(tmp_path / "here", description="d", actor="test")
    assert checker.check_hub() == []
```

Extend `cli/tests/test_views.py::test_today_skips_hub_entries_without_bucket`
— replace its final assert with:

```python
    t = views.today()
    assert t["buckets"] == []
    assert t["missing"] == [
        {"name": "ghost", "path": str(tmp_path / "gone")}
    ]
```

Append to `cli/tests/test_cli.py`:

```python
def test_hub_list_flags_missing(tmp_path, capsys, monkeypatch):
    from fusion import hub

    monkeypatch.setenv("FUSION_HUB", str(tmp_path / "hub.md"))
    hub.add(hub.HubEntry("ghost", "personal", str(tmp_path / "gone"), "x"))
    assert main(["hub"]) == 0
    out = capsys.readouterr().out
    assert "ghost" in out and "fusion hub remove ghost" in out
    assert main(["hub", "--json"]) == 0
    assert out_json(capsys)[0]["missing"] is True


def test_check_hub_mode(tmp_path, capsys, monkeypatch):
    from fusion import hub

    monkeypatch.setenv("FUSION_HUB", str(tmp_path / "hub.md"))
    hub.add(hub.HubEntry("ghost", "personal", str(tmp_path / "gone"), "x"))
    assert main(["check", "--hub", "--json"]) == 0  # warnings never fail
    payload = out_json(capsys)
    assert payload["ok"] is False
    assert payload["warnings"][0]["code"] == "H1"
    # outside any bucket, path-less check falls back to the hub audit
    monkeypatch.chdir(tmp_path)
    assert main(["check"]) == 0
    assert "H1" in capsys.readouterr().out


def test_today_agenda_note_missing_buckets(tmp_path, capsys, monkeypatch):
    from fusion import hub

    monkeypatch.setenv("FUSION_HUB", str(tmp_path / "hub.md"))
    hub.add(hub.HubEntry("ghost", "personal", str(tmp_path / "gone"), "x"))
    assert main(["today"]) == 0
    assert "ghost" in capsys.readouterr().err
    assert main(["agenda", "--json"]) == 0
    captured = capsys.readouterr()
    assert "ghost" in captured.err
    assert json.loads(captured.out)["missing"][0]["name"] == "ghost"
```

(`test_cli.py` already has `main`, `out_json`; add `import json` if the
file lacks it. `test_check_hub_mode`'s chdir case requires `tmp_path`
not to be inside a bucket — it isn't.)

Update the existing pinned assertion in
`test_status_today_agenda_json`:

```python
    assert out_json(capsys) == {"dated": [], "active": [], "missing": []}
```

- [ ] **Step 2: Run to verify failures**

Run: `cd cli && uv run pytest tests/test_checker_warnings.py tests/test_views.py tests/test_cli.py -v`
Expected: the new/changed tests FAIL (no `check_hub`, no `missing` keys,
no `--hub` flag); everything else passes.

- [ ] **Step 3: Implement `checker.check_hub()`**

In `cli/src/fusion/checker.py`: update the `Finding.code` comment to
`# E1..E8, W1..W5 — plus H1..H2 from check_hub (CLI vocabulary, not SPEC)`,
add `from . import hub` to the module imports, and append:

```python
def check_hub() -> list[Finding]:
    """The hub's own audit — dangling entries and name drift.

    H-codes are CLI vocabulary, not SPEC conformance codes: the hub is a
    per-machine register and consumers must tolerate anything in it. All
    findings are warnings; a hub audit never fails.
    """
    findings: list[Finding] = []
    for entry in hub.load():
        root = hub.resolve(entry)
        if not (root / "BUCKET.md").is_file():
            findings.append(Finding(
                "warning", "H1", entry.path,
                f"'{entry.name}' — no bucket at this path; clone it "
                f"there, or `fusion hub remove {entry.name}`",
            ))
            continue
        name = load(root).name
        if name and name != entry.name:
            findings.append(Finding(
                "warning", "H2", entry.path,
                f"hub says '{entry.name}' but BUCKET.md says '{name}' — "
                "re-register: `fusion hub remove` then `fusion hub add`",
            ))
    return findings
```

(`load` is already imported from `.bucket` at the top of checker.py.
Check the `hub` import does not collide with a local name; it doesn't.)

- [ ] **Step 4: Implement `views.missing_hub_entries()` + payload keys**

In `cli/src/fusion/views.py`, after `_hub_buckets()`:

```python
def missing_hub_entries() -> list[dict]:
    """Hub entries whose path holds no readable BUCKET.md — a bucket not
    yet cloned to this machine, moved, or gone."""
    return [
        {"name": entry.name, "path": entry.path}
        for entry in hub.load()
        if not (hub.resolve(entry) / "BUCKET.md").is_file()
    ]
```

In `today()` and `agenda()`, add `"missing": missing_hub_entries()` to
the returned dict (same key in both).

- [ ] **Step 5: Implement the CLI surface**

In `cli/src/fusion/cli.py`:

**cmd_hub list branch** — replace the list rendering with:

```python
    entries = hub.load()
    flagged = [
        (e, not (hub.resolve(e) / "BUCKET.md").is_file()) for e in entries
    ]
    lines = []
    for e, missing in flagged:
        lines.append(f"- **{e.name}** · {e.kind} · {e.path} — {e.description}")
        if missing:
            lines.append(
                f"  ⚠ no bucket at that path — clone it there, "
                f"or `fusion hub remove {e.name}`"
            )
    human = "\n".join(lines) or "the hub is empty — `fusion new` a bucket."
    _emit([{**asdict(e), "missing": missing} for e, missing in flagged],
          args.json, human)
    return 0
```

**cmd_today / cmd_agenda** — after computing `t = views.today()` (resp.
`a = views.agenda()`), before rendering:

```python
    for m in t["missing"]:
        print(
            f"note: hub bucket '{m['name']}' is not at {m['path']} — "
            f"clone it there, or `fusion hub remove {m['name']}`",
            file=sys.stderr,
        )
```

(same loop over `a["missing"]` in cmd_agenda).

**cmd_check** — add hub mode at the top, and the outside-bucket
fallback:

```python
def cmd_check(args) -> int:
    if getattr(args, "hub", False):
        return _check_hub(args)
    root = _root_from(args)
    if root is None:
        given = getattr(args, "path", None)
        if given is None:
            return _check_hub(args)  # outside any bucket: audit the hub
        return _fail(f"no bucket at: {given}", args.json)
    ...  # rest unchanged
```

New helper above cmd_check:

```python
def _check_hub(args) -> int:
    findings = checker.check_hub()
    entries = hub.load()
    if args.json:
        _emit({
            "hub": str(hub.hub_path()),
            "buckets": len(entries),
            "ok": not findings,
            "warnings": [asdict(f) for f in findings],
        }, True, "")
    else:
        for f in findings:
            print(f"  {f.code} · {f.path} — {f.message}")
        n, w = len(entries), len(findings)
        verdict = ("every bucket answers." if not findings
                   else "some buckets are not where the hub says.")
        print(f"hub: {n} bucket{'s' if n != 1 else ''} · "
              f"{w} warning{'s' if w != 1 else ''} — {verdict}")
    return 0
```

**Parser** — in the `check` parser block:

```python
    p.add_argument("--hub", action="store_true",
                   help="audit the hub instead: every entry answers at its path")
```

Also update the check parser `description` to mention it:
`"Audit a bucket against the convention (SPEC §11). Exit 1 on errors; warnings never fail the check. --hub (or running outside any bucket) audits the hub instead: every registered bucket present and answering to its name."`

- [ ] **Step 6: Run the three test files, then the full suite**

Run: `cd cli && uv run pytest tests/test_checker_warnings.py tests/test_views.py tests/test_cli.py -v`
Expected: ALL PASS.
Run: `cd cli && uv run pytest -q` — expected: green.

- [ ] **Step 7: Commit**

```bash
git add cli/src/fusion/checker.py cli/src/fusion/views.py cli/src/fusion/cli.py cli/tests/
git commit -m "feat: dangling hub entries surface in hub, today, agenda, and check --hub"
```

---

### Task 3: The guard becomes a door — skills offer `fusion new`

**Files:**
- Modify: `skills/fusion-intake/SKILL.md`,
  `skills/fusion-librarian/SKILL.md`, `skills/fusion-planner/SKILL.md`,
  `skills/fusion-analyst/SKILL.md`
- Modify: `skills/*/references/fusion-conventions.md` ×4 (byte-identical)

**Interfaces:**
- Consumes: `fusion new` / `.gitattributes` behavior from Task 1 (the
  card describes it — Task 1 must land first).

- [ ] **Step 1: Description tails (all four SKILL.md frontmatter)**

In each description, replace the final clause

```
if there is no such bucket in play, this skill does not apply.
```

with

```
if there is no such bucket in play, offer to create one with `fusion new` instead of improvising structure.
```

Lengths after the +45-char edit: librarian 1007, intake 890, analyst
890, planner 857 — all ≤1024. Do not reflow anything else in the
description strings.

- [ ] **Step 2: Body guards (all four SKILL.md)**

Each body has a guard ending. Replace, per file:

`fusion-librarian/SKILL.md` — replace

```
No
`BUCKET.md` up the tree and none named? Stop — this is not a Fusion
bucket, and no Fusion skill applies (`fusion hub` lists the real ones).
```

`fusion-intake/SKILL.md` — replace

```
No `BUCKET.md` up the tree and none named? Stop — this is not a Fusion
bucket, and no Fusion skill applies (`fusion hub` lists the real ones).
```

`fusion-planner/SKILL.md` — replace

```
No `BUCKET.md` up the
tree and none named? Stop — this is not a Fusion bucket, and no Fusion
skill applies (`fusion hub` lists the real ones).
```

`fusion-analyst/SKILL.md` — replace

```
No `BUCKET.md` up the tree and
none named? Stop — this is not a Fusion bucket, and no Fusion skill
applies (`fusion hub` lists the real ones).
```

Each with this text (rewrap to the file's ~76-char flow, joining
naturally with the sentence before it):

```
No `BUCKET.md` up the tree and none named? Then nothing here is a
Fusion bucket and no Fusion skill applies — but offer the door instead
of walking away: `fusion new <path>` scaffolds a conformant bucket and
registers it in the hub (`fusion hub` lists the ones that exist).
Buckets are life-domains — few and bold — never improvised by hand.
```

- [ ] **Step 3: The conventions card (edit once, copy ×3)**

Edit `skills/fusion-librarian/references/fusion-conventions.md`:

**(a)** In `## The CLI crib`, replace the check row

```
| `fusion check [path]` | conformance: errors, warnings, honest exit codes |
```

with

```
| `fusion check [path]` | conformance: errors, warnings, honest exit codes |
| `fusion check --hub` | is every registered bucket where the hub says? |
```

**(b)** In `## The registers — single writers, no exceptions`, append a
new paragraph after the closing "Sign with your agent name…" paragraph:

```
On a bucket that lives on more than one machine, git's union driver
(`.gitattributes`, written at bucket birth) merges parallel `LEDGER.md`
and `MANIFEST.md` appends. After any git merge: `fusion index`, then
`fusion check`.
```

**(c)** In `## When you're blocked`, insert as the FIRST bullet:

```
- No bucket in play anywhere: never improvise Fusion structure by hand.
  Offer `fusion new <path> --kind <kind> --description "…"` — six zones,
  BUCKET.md, an opened ledger, a merge-safe `.gitattributes`, registered
  in the hub. Guide the human toward few, bold, life-domain buckets
  (personal, one per company, a studio).
```

Then copy the file byte-identically over the other three:

```bash
for s in fusion-intake fusion-planner fusion-analyst; do
  cp skills/fusion-librarian/references/fusion-conventions.md \
     "skills/$s/references/fusion-conventions.md"
done
```

- [ ] **Step 4: Run the gates**

Run: `cd cli && uv run pytest tests/test_skill_family.py -v`
Expected: ALL PASS (description length, card byte-identity, no personal
paths).

- [ ] **Step 5: Commit**

```bash
git add skills/
git commit -m "feat: the bucket guard becomes a door — skills offer fusion new instead of walking away"
```

---

### Task 4: The worked example — an activity whose code lives outside

**Files:**
- Create: `examples/crazy-ones/activities/band-site/plan.md`
- Modify: `examples/crazy-ones/LEDGER.md` (two lines, chronological
  position), `examples/crazy-ones/activities/INDEX.md` (regenerated)
- Modify: `skills/fusion-planner/references/create-activity.md`
- Modify: `cli/tests/test_views.py`, `cli/tests/test_ledger.py`,
  `cli/tests/test_hub_bucket.py`, `cli/tests/test_cli.py`

**Interfaces:**
- Consumes: fixture counts pinned in the four test files (exact updated
  values below).
- Produces: the normative `resource:`-points-outside activity that
  Task 5's field guide links as `examples/crazy-ones/activities/band-site/plan.md`.

- [ ] **Step 1: Update the pinned tests first (they become the spec)**

`cli/tests/test_views.py::test_status_fixture`:

```python
    assert s["documents"] == 7
    assert s["auroras"] == {"archive": 1, "collab": 1, "focus": 2, "library": 3}
    assert s["types"] == {"instrument": 2, "plan": 3, "press-kit": 1, "recipe": 1}
    assert s["activities"] == {"active": 2, "done": 1}
    assert len(s["ledger"]) == 10  # last ten of nineteen
    assert s["ledger"][-1]["verb"] == "reflected"
```

`cli/tests/test_views.py::test_status_since_date`: `len(s["ledger"]) == 7`.

`cli/tests/test_ledger.py::test_parse_fixture`: `len(entries) == 19`
(the other asserts hold — still exactly one `reflected`).

`cli/tests/test_hub_bucket.py::test_iter_documents_fixture`:
`len(docs) == 7` and
`zone_counts == {"library": 3, "activities": 3, "output": 1}`.

`cli/tests/test_cli.py::test_status_today_agenda_json`:
`out_json(capsys)["documents"] == 7`.

- [ ] **Step 2: Run to verify they fail**

Run: `cd cli && uv run pytest tests/test_views.py tests/test_ledger.py tests/test_hub_bucket.py tests/test_cli.py -v`
Expected: exactly the edited tests FAIL against the current fixture.

- [ ] **Step 3: Create the activity**

`examples/crazy-ones/activities/band-site/plan.md`:

```markdown
---
title: Band Site
type: plan
aurora: focus
tags: [web, code]
created: 2026-07-10
updated: 2026-07-10
status: active
resource: ~/Code/band-site
---

## Summary

The band's website; the code lives outside, in its own repository.
This activity keeps the plan, the decisions, and the progress.

---

## The rule

Fusion holds knowledge and work, never code. The repository at
`~/Code/band-site` stays a normal git repo with its own history —
`resource:` above points at it. What lives here is what the code
cannot remember: why, what is next, what was decided.

## Decisions

- Static site, no framework — the band pays for nothing monthly.
- One page per release; the [press kit](../../output/press-kit.md) is
  the source of truth for copy.

## Progress

| Week | Done |
|---|---|
| 2026-W28 | Repo created, domain pointed, press kit copy drafted |

Next: the LP page goes up when
[First Light](../lp-first-light/plan.md) settles its tracklist.
```

- [ ] **Step 4: The ledger lines (chronological, before the reflection)**

In `examples/crazy-ones/LEDGER.md`, under `## 2026-07-10`, insert
between the `10:05 · claude · indexed` line and the `10:30 · claude ·
reflected` line:

```markdown
- 10:20 · bertrand · created · activities/band-site/plan.md — "code stays in its own repo; resource: points at it"
- 10:21 · claude · indexed · activities/ (3 documents)
```

(The `reflected` entry stays last — the day still closes on the
reflection, and the tests assert it.)

- [ ] **Step 5: Regenerate the activities INDEX (never via `fusion index`)**

```bash
cd cli && uv run python -c "
from pathlib import Path
from fusion import indexer
indexer.write_indexes(Path('../examples/crazy-ones'), actor=None)
"
```

`actor=None` regenerates without touching the ledger. Verify the new
`activities/INDEX.md` gained (sections alphabetical, archive last):

```markdown
## band-site/

- [Band Site](band-site/plan.md) — The band's website; the code lives outside, in its own repository. (focus)
```

- [ ] **Step 6: Run the suite + the fixture gate**

Run: `cd cli && uv run pytest -q` — expected: green (golden INDEX tests
regenerate to the committed bytes).
Run: `cd cli && uv run fusion check ../examples/crazy-ones`
Expected: `crazy-ones: 0 errors · 0 warnings — clean, carry on.`
(W5 does not fire: band-site's first ledger mention, 10:20, sits inside
the first reflection window.)

- [ ] **Step 7: Teach the planner the pattern**

In `skills/fusion-planner/references/create-activity.md`, append after
step 4:

```markdown
## The external project

An activity about building something that is code — an app, a site, a
tool — keeps the repository OUTSIDE the bucket (Fusion holds knowledge
and work, never code). Point at it instead:

    ---
    title: <name>
    type: plan
    aurora: focus
    status: active
    created: <today>
    resource: <path or URL of the repository>
    ---

The repo keeps its own history; the activity keeps what the code cannot
remember — the plan, the decisions, the progress log, links to the
bucket documents it draws on. The normative example:
`examples/crazy-ones/activities/band-site/plan.md` in the Fusion
repository.
```

- [ ] **Step 8: Commit**

```bash
git add examples/crazy-ones/ cli/tests/ skills/fusion-planner/references/create-activity.md
git commit -m "feat: the external-project pattern gets its normative example — band-site, resource: pointing out"
```

---

### Task 5: The field guide — docs/BUCKETS-EVERYWHERE.md

**Files:**
- Create: `docs/BUCKETS-EVERYWHERE.md`
- Modify: `docs/README.md`, `docs/GETTING-STARTED.md`, `README.md`,
  `docs/dogfood/frictions.md`

**Interfaces:**
- Consumes: `.gitattributes` content (Task 1), `fusion check --hub`
  (Task 2), band-site example (Task 4).

- [ ] **Step 1: Write the page**

Create `docs/BUCKETS-EVERYWHERE.md` with exactly this content:

````markdown
# Buckets everywhere

A bucket is a directory and a git repository — which means everything
git can do, a bucket can do: absorb an old mess, travel to a new
machine, live on two at once, stand beside a code repo it describes.
This page holds the recipes. The ten-minute basics are in
[GETTING-STARTED.md](GETTING-STARTED.md).

## Moving in — a messy folder becomes a bucket

`fusion new` refuses a non-empty target on purpose: it never builds on
top of something it might damage. So the move is scaffold-beside, then
feed the mess through the gate:

```bash
fusion new ~/buckets/studio --kind studio --description "…"
mv ~/old-mess/* ~/buckets/studio/inbox/
```

Then tell your agent to **process the inbox**. The intake gate handles
a folder of dozens to hundreds of files as one delivery: byte-identical
duplicates are swept, folder structure becomes filing categories,
originals land immutable under `sources/`, and every document comes out
summary-first and conformant. You confirm the judgment calls (updates,
conflicts); the ledger records the lot.

Two placements the gate will not make for you:

- Half-formed personal notes with no original worth preserving can go
  straight to `workbench/` — no rules apply there.
- Things that are neither knowledge nor work (installers, media
  libraries, code) do not belong in a bucket at all. Leave them where
  they live; documents can point at them (see the last section).

Finish with `fusion check` — green means the mess is now a library.

## Handoffs — an archive arrives

`.zip` and `.athena` packages are delivery vehicles, not originals: drop
one in `inbox/` and the gate unpacks it, treats the members as the
originals, and walks the same delivery pipeline. A retiring workspace —
a shaping room, an export from another tool — hands off the same way:
export, drop, process the inbox.

## One bucket, two machines

Every bucket is born a git repository with a `.gitattributes` that makes
parallel work merge safely:

```gitattributes
# written by fusion new — multi-machine merges stay safe (SPEC §6)
* text=auto eol=lf
LEDGER.md merge=union
sources/MANIFEST.md merge=union
```

Give the bucket a private remote and it travels like any repo:

```bash
cd ~/buckets/studio
git remote add origin git@github.com:you/studio-bucket.git
git push -u origin main
```

Work on both machines, push and pull as you go. When both sides
appended to the ledger, git's union driver keeps both sets of entries —
the merged ledger may briefly hold two headings for the same date,
which every Fusion reader tolerates; it is the honest record of
parallel work. After any merge, settle the registers:

```bash
fusion index && fusion check
```

A bucket born before this page (no `.gitattributes` at its root) gets
one by copying the four lines above into `<bucket>/.gitattributes` and
committing.

Two things deliberately do not sync: the hub (`~/.fusion/hub.md` is
per-machine — see the next section) and anything `resource:` points at
(the bucket carries the pointer, not the thing).

## A new machine

Fusion's install is one line; your buckets are git clones; the hub is
rebuilt by registration, not by copying:

```bash
curl -fsSL https://raw.githubusercontent.com/bluewaves-creations/fusion/main/install.sh | sh
git clone git@github.com:you/studio-bucket.git ~/buckets/studio
fusion hub add ~/buckets/studio        # once per bucket
fusion check --hub                     # every entry answers at its path
fusion today                           # the composed morning is back
```

`fusion hub add` reads the bucket's own BUCKET.md, so the path can
differ from the old machine's — buckets are the durable objects, the
hub is just this machine's map. If `fusion today` ever goes quiet about
a bucket you expected, `fusion check --hub` names what is missing and
how to fix it.

## The project that lives outside

An app, a site, a tool — the code belongs in its own repository, never
inside a bucket. The bucket keeps what the code cannot remember:

```markdown
---
title: Band Site
type: plan
aurora: focus
status: active
resource: ~/Code/band-site
---
```

`resource:` points at the repo; the activity holds the plan, the
decisions, and the progress; `fusion today` surfaces it every morning
like any other live work. The worked example is
[band-site in the example bucket](../examples/crazy-ones/activities/band-site/plan.md)
— wander it before you build your own.
````

- [ ] **Step 2: Link it everywhere it belongs**

`docs/README.md` — add a row to the table, after GETTING-STARTED:

```markdown
| [BUCKETS-EVERYWHERE.md](BUCKETS-EVERYWHERE.md) | Moving in, syncing, new machines, code repos | Your buckets meet the world |
```

`docs/GETTING-STARTED.md` — in `## Where to go next`, insert after the
examples line:

```markdown
- [Buckets everywhere](BUCKETS-EVERYWHERE.md) — migrate a messy folder
  in, sync a bucket between machines, rebuild the hub on a new one,
  track a project whose code lives outside.
```

`README.md` — in the docs table (around line 108), add after the
GETTING-STARTED row:

```markdown
| [docs/BUCKETS-EVERYWHERE.md](docs/BUCKETS-EVERYWHERE.md) | Migration, git sync, new machines, external projects |
```

- [ ] **Step 3: Record the friction**

Append to the table in `docs/dogfood/frictions.md`:

```markdown
| 9 | 2026-07-11 | all | design review | six common lifecycle scenarios probed (first bucket, addition, conversion, git sync, new machine, external project): the skills' own guard blocked the onboarding conversation, ledger merges were undefined, dangling hub entries skipped silently, the resource: pattern was invisible | grind | **fixed** — the bucket-scenarios batch (this plan): guard becomes a door, union-merge .gitattributes at birth + SPEC §6/§7, hub truth in hub/today/agenda/check --hub, band-site worked example, BUCKETS-EVERYWHERE field guide |
```

- [ ] **Step 4: Cold-read pass + gates**

Read the new page start to finish as a newcomer: every command runnable
as written, every link resolves (`docs/` → `../examples/…` and
`GETTING-STARTED.md` are siblings — verify both), voice matches
GETTING-STARTED, no exclamation marks, ~76-char wrap.

Run: `cd cli && uv run pytest -q` — green (no code touched; the gate is
for regressions).

- [ ] **Step 5: Commit**

```bash
git add docs/
git commit -m "docs: BUCKETS-EVERYWHERE — moving in, two machines, new machines, projects that live outside"
```

---

## After the tasks

- Final whole-branch review (SDD): most capable model, package via
  `review-package MERGE_BASE HEAD`.
- Merge to `main` per the user's git preference (minimal branching,
  linear history); **do not push** — the user pushes, or grants a
  one-time authorization.
- Release note for the user to decide (not part of this plan): the CLI
  gained `check --hub` and scaffold behavior — a v1.2.0 PyPI release
  would ship it to one-liner users; skills changed too, so installed
  agents want `fusion setup` (and a restart where descriptions are
  cached).
