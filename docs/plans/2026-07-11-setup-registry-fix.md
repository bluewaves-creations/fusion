# Setup Registry Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps
> use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `fusion setup` truthful and safe per the verified agent
landscape: never destroy a canonical skill through a symlinked agent
dir, never double-load into agents that read `~/.agents/skills`
natively (Pi, Codex), and clean up the double-loading links earlier
releases created.

**Architecture:** Three surgical changes to `cli/src/fusion/setup.py` —
a same-inode guard in `fan_out` and `remove_all`, a registry correction
(Pi and Codex flip from link-mode to standard-mode), and a
`_sweep_legacy` helper that removes OUR leftover links/copies from the
dirs fusion-cli ≤1.2.0 linked into. Plus pinned regression tests (unit
and installer e2e) for the destruction topology.

**Tech Stack:** Python 3.11+ (uv-managed), pytest, GitHub Actions.

**Verified facts driving this plan (2026-07-11, do not relitigate):**

- Pi natively reads BOTH `~/.agents/skills` and `~/.pi/agent/skills`
  (pi.dev docs) — our symlinks into the latter double-load every skill.
- Codex reads `$HOME/.agents/skills` at user level; `~/.codex/skills`
  is NOT a discovery location at all (OpenAI docs) — our symlinks there
  are dead weight AND the canonical already serves Codex.
- Claude Code does NOT read `~/.agents/skills` — link-mode stays
  correct for it.
- Live-reproduced: when an agent's skills dir is a symlink AT the
  canonical dir (e.g. `~/.claude/skills -> ~/.agents/skills`, a real
  user topology), `fan_out` rmtree's each canonical skill and replaces
  it with a self-referential symlink, reporting "linked". `remove_all`
  has the same hole (`setup.py:223-227`). Shipped in v1.1.0–v1.2.0.

## Global Constraints

- Warm-terse copy, no exclamation marks; code comments state
  constraints the code can't show, nothing else.
- Python writes use `encoding="utf-8", newline="\n"`; all files LF.
- The never-destroy policy is the product: attribution (digest match,
  `.fusion-setup` sentinel, or symlink-into-canonical) gates every
  deletion; anything unattributable is left with a report row.
- Version stays 1.2.0 during the tasks — the release bump to 1.2.1
  happens after merge, in the release step (not a task).
- QA bar per task: `cd cli && uv run pytest -q` fully green;
  final gates also include `uv run fusion check ../examples/crazy-ones`
  → `0 errors · 0 warnings`.
- Branch: `setup-registry-fix` off `main`; do not push (the release
  step pushes, already user-authorized).
- NEVER run `fusion setup` against the real HOME while testing — every
  live experiment uses a sandbox HOME under the scratchpad or tmp_path.

## File Structure

| File | Change |
|---|---|
| `cli/src/fusion/setup.py` | same-inode guards, registry rows, `_sweep_legacy` |
| `cli/src/fusion/cli.py` | setup parser description (one string) |
| `cli/tests/test_setup_agents.py` | destruction regressions, registry/mode updates, sweep tests |
| `.github/workflows/ci.yml` | e2e symlinked-topology block (POSIX) |

---

### Task 1: The same-inode guard — setup can never eat the canonical

**Files:**
- Modify: `cli/src/fusion/setup.py` (fan_out, remove_all)
- Modify: `cli/tests/test_setup_agents.py`

**Interfaces:**
- Consumes: `_points_into(link, canonical)` (existing; `resolve()` +
  `is_relative_to`, equality counts as inside).
- Produces: new report action `"served"` (agent-level row with
  `"skill": "*"`, same shape as the `"standard"` row) — Task 3's e2e
  greps for it.

- [ ] **Step 1: Write the failing regression tests**

Append to `cli/tests/test_setup_agents.py`:

```python
def test_fan_out_survives_skills_dir_symlinked_to_canonical(home, canonical):
    # the topology that destroyed skills in v1.1.0-v1.2.0: the agent's
    # whole skills dir is a symlink AT the canonical directory
    (home / ".claude").mkdir()
    (home / ".claude" / "skills").symlink_to(
        canonical, target_is_directory=True)
    results = setup.fan_out(canonical, setup.detect_agents(home),
                            force=False)
    claude = [r for r in results if r["agent"] == "Claude Code"]
    assert len(claude) == 1 and claude[0]["action"] == "served"
    # the canonical skills are alive, real, and readable
    assert (canonical / "fusion-intake" / "SKILL.md").is_file()
    assert not (canonical / "fusion-intake").is_symlink()


def test_remove_all_survives_skills_dir_symlinked_to_canonical(
        home, canonical):
    (home / ".claude").mkdir()
    (home / ".claude" / "skills").symlink_to(
        canonical, target_is_directory=True)
    setup.remove_all(canonical, home)
    # the canonical phase removed the skills exactly once; the user's
    # own dir-level symlink is not ours and stays
    assert not (canonical / "fusion-intake").exists()
    assert (home / ".claude" / "skills").is_symlink()
```

- [ ] **Step 2: Run to verify the first test reproduces the destruction**

Run: `cd cli && uv run pytest tests/test_setup_agents.py -v`
Expected: both new tests FAIL — the first with `"linked"` actions and a
destroyed/symlinked canonical (this is the live bug reproducing under
pytest), the second likely erroring or leaving the canonical
half-removed.

- [ ] **Step 3: Implement the guards**

In `cli/src/fusion/setup.py`, `fan_out()` — immediately after the
`if agent["mode"] == "standard": ... continue` block, before
`agent["skills_dir"].mkdir(...)`:

```python
        if _points_into(agent["skills_dir"], canonical):
            results.append({
                "agent": agent["name"], "skill": "*", "action": "served",
                "detail": f"{agent['skills_dir']} resolves into "
                          f"{canonical} — the canonical install already "
                          f"serves this agent; nothing to link"})
            continue
```

Defense-in-depth backstop in the same function's `elif target.is_dir():`
branch, as its first check (before the digest comparison):

```python
            elif target.is_dir():
                if target.resolve() == skill.resolve():
                    results.append({**row, "action": "served",
                                    "detail": f"{target} already resolves "
                                              f"to the canonical skill"})
                    continue
                if tree_digest(target) == tree_digest(skill):
```

(No filesystem lets a plain dir alias another today except through
symlinked parents — which the dir-level guard catches — but a rmtree
that could eat the canonical deserves two locks.)

In `remove_all()` — after the `if agent["mode"] == "standard": continue`
line:

```python
        if _points_into(agent["skills_dir"], canonical):
            continue  # entries here ARE the canonical skills; the
                      # canonical phase below removes them exactly once
```

- [ ] **Step 4: Run the file, then the full suite**

Run: `cd cli && uv run pytest tests/test_setup_agents.py -v` — ALL PASS.
Run: `cd cli && uv run pytest -q` — green.

- [ ] **Step 5: Commit**

```bash
git add cli/src/fusion/setup.py cli/tests/test_setup_agents.py
git commit -m "fix: setup can never destroy the canonical through a symlinked agent dir"
```

---

### Task 2: Registry truth — Pi and Codex read the standard dir; sweep our old links

**Files:**
- Modify: `cli/src/fusion/setup.py` (AGENTS, detect_agents, fan_out,
  remove_all, new `_sweep_legacy`)
- Modify: `cli/src/fusion/cli.py` (setup parser description)
- Modify: `cli/tests/test_setup_agents.py`

**Interfaces:**
- Consumes: Task 1's guards (already in the file).
- Produces: registry rows with optional `"legacy_subdir"`;
  `detect_agents` attaches `"legacy_dir"` when present; new report
  action `"unlinked"`; Pi/Codex rows are `mode: "standard"` with
  `skills_subdir: ".agents/skills"` — Task 3's e2e asserts no
  `.pi/agent/skills/fusion-*` are created.

- [ ] **Step 1: Update the registry and detection**

In `cli/src/fusion/setup.py`, replace the comment above `AGENTS` and the
Codex/Pi rows (Claude Code, Cursor, Gemini CLI, opencode, Goose rows
stay byte-identical):

```python
# One row per agent. mode "link": the agent does not read the standard
# ~/.agents/skills dir, so each fusion-* skill gets a symlink (or copy)
# in its own skills dir. mode "standard": the agent reads the standard
# dir — creating links there too would load every skill twice.
# legacy_subdir: a dir an earlier fusion-cli release linked into before
# the agent's native standard-dir support was verified; setup sweeps
# OUR leftovers out of it (attribution-checked, like everything else).
AGENTS = [
    {"name": "Claude Code", "marker": ".claude",
     "skills_subdir": ".claude/skills", "mode": "link",
     "docs_url": "https://code.claude.com/docs/en/skills"},
    {"name": "Codex", "marker": ".codex",
     "skills_subdir": ".agents/skills", "mode": "standard",
     "legacy_subdir": ".codex/skills",
     "docs_url": "https://developers.openai.com/codex/skills"},
    {"name": "Pi", "marker": ".pi",
     "skills_subdir": ".agents/skills", "mode": "standard",
     "legacy_subdir": ".pi/agent/skills",
     "docs_url": "https://pi.dev/docs/latest/skills"},
    {"name": "Cursor", "marker": ".cursor",
     "skills_subdir": ".agents/skills", "mode": "standard",
     "docs_url": "https://cursor.com/docs/skills"},
    {"name": "Gemini CLI", "marker": ".gemini",
     "skills_subdir": ".agents/skills", "mode": "standard",
     "docs_url": "https://geminicli.com/docs/cli/skills"},
    {"name": "opencode", "marker": ".config/opencode",
     "skills_subdir": ".agents/skills", "mode": "standard",
     "docs_url": "https://opencode.ai/docs/skills"},
    {"name": "Goose", "marker": ".config/goose",
     "skills_subdir": ".agents/skills", "mode": "standard",
     "docs_url": "https://block.github.io/goose/docs/mcp/skills-mcp"},
]
```

`detect_agents` attaches the legacy dir:

```python
def detect_agents(home: Path) -> list[dict]:
    found = []
    for row in AGENTS:
        if (home / row["marker"]).is_dir():
            entry = {**row, "skills_dir": home / row["skills_subdir"]}
            if "legacy_subdir" in row:
                entry["legacy_dir"] = home / row["legacy_subdir"]
            found.append(entry)
    return found
```

- [ ] **Step 2: Implement `_sweep_legacy` and wire it into both paths**

Add after `_points_into`:

```python
def _sweep_legacy(agent: dict, canonical: Path) -> list[dict]:
    """Remove OUR leftovers from a dir an earlier release linked into.

    fusion-cli <= 1.2.0 symlinked (or copy-fell-back) into Pi's and
    Codex's own dirs; both agents read the canonical dir natively, so
    those entries double-loaded every skill. Attribution-checked:
    symlinks into the canonical and sentinel-marked copies are ours;
    anything else is left with a report row.
    """
    legacy = agent.get("legacy_dir")
    if legacy is None or not legacy.is_dir():
        return []
    results = []
    for entry in sorted(legacy.glob("fusion-*")):
        row = {"agent": agent["name"], "skill": entry.name}
        if entry.is_symlink() and _points_into(entry, canonical):
            entry.unlink()
            results.append({**row, "action": "unlinked",
                            "detail": f"{entry} — this agent reads the "
                                      f"standard dir; the extra link "
                                      f"double-loaded every skill"})
        elif (entry.is_dir() and not entry.is_symlink()
              and (entry / ".fusion-setup").is_file()):
            shutil.rmtree(entry)
            results.append({**row, "action": "unlinked",
                            "detail": f"{entry} — copy from an earlier "
                                      f"fusion-cli; this agent reads the "
                                      f"standard dir"})
        else:
            results.append({**row, "action": "left",
                            "detail": f"{entry} is not attributable to "
                                      f"setup — left in place"})
    return results
```

In `fan_out()`, the standard branch becomes:

```python
        if agent["mode"] == "standard":
            results.extend(_sweep_legacy(agent, canonical))
            if canonical.resolve() != agent["skills_dir"].resolve():
                detail = (f"reads ~/.agents/skills — but your skills are "
                          f"at {canonical}, which this agent does not read")
            else:
                detail = "reads ~/.agents/skills — nothing to do"
            results.append({"agent": agent["name"], "skill": "*",
                            "action": "standard", "detail": detail})
            continue
```

In `remove_all()`, the standard branch becomes:

```python
        if agent["mode"] == "standard":
            results.extend(_sweep_legacy(agent, canonical))
            continue
```

- [ ] **Step 3: Update the setup parser description**

In `cli/src/fusion/cli.py`, the `setup` subparser description currently
says the skills are linked "into every detected agent". Replace that
description string with:

```
Install the bundled skills to the canonical skills directory
(~/.agents/skills) and make them available to every detected agent —
most read that directory natively; agents that do not (Claude Code)
get symlinks. --remove undoes exactly what setup can prove it created.
```

(Keep it a single Python string in the existing style; match the
surrounding quoting/concatenation.)

- [ ] **Step 4: Update and extend the tests**

In `cli/tests/test_setup_agents.py`:

**(a)** `test_registry_shape` — extend the mode assertions:

```python
    assert modes["Claude Code"] == "link"
    assert modes["Pi"] == "standard"
    assert modes["Codex"] == "standard"
    assert modes["Cursor"] == "standard"
    legacy = {a["name"]: a.get("legacy_subdir") for a in setup.AGENTS}
    assert legacy["Pi"] == ".pi/agent/skills"
    assert legacy["Codex"] == ".codex/skills"
```

**(b)** `test_fan_out_copies_when_symlink_unavailable` — Pi is no longer
a link agent; retarget to Claude Code: `(home / ".pi").mkdir()` →
`(home / ".claude").mkdir()`; every `"Pi"` → `"Claude Code"`; the path
`home / ".pi" / "agent" / "skills" / "fusion-intake"` →
`home / ".claude" / "skills" / "fusion-intake"`. Assertions otherwise
unchanged.

**(c)** `test_remove_all_removes_sentinel_copies_and_leaves_foreign` —
rewrite for the single remaining link agent:

```python
def test_remove_all_removes_sentinel_copies_and_leaves_foreign(
        home, canonical, monkeypatch):
    (home / ".claude").mkdir()
    # a foreign dir sharing a canonical skill's name — same shape, no
    # sentinel, different content — must survive removal untouched
    foreign = home / ".claude" / "skills" / "fusion-planner"
    foreign.mkdir(parents=True)
    (foreign / "SKILL.md").write_text("---\nname: my-own-tool\n---\n")
    (foreign / "data.txt").write_text("do not touch\n")

    def no_symlink(*a, **k):
        raise OSError("symlinks disabled")
    monkeypatch.setattr(setup.os, "symlink", no_symlink)
    setup.fan_out(canonical, setup.detect_agents(home), force=False)
    ours = home / ".claude" / "skills" / "fusion-intake"
    assert (ours / ".fusion-setup").is_file()   # our sentinel-marked copy

    results = setup.remove_all(canonical, home)

    assert not ours.exists()                     # our copy: removed
    intake = [r for r in results if r["agent"] == "Claude Code"
              and r["skill"] == "fusion-intake"][0]
    assert intake["action"] == "removed"
    assert foreign.is_dir()                      # foreign: left in place
    assert (foreign / "data.txt").read_text() == "do not touch\n"
    planner = [r for r in results if r["agent"] == "Claude Code"
               and r["skill"] == "fusion-planner"][0]
    assert planner["action"] == "left"
```

**(d)** New sweep tests:

```python
def test_fan_out_standard_sweeps_our_legacy_links(home, canonical):
    (home / ".pi").mkdir()
    legacy = home / ".pi" / "agent" / "skills"
    legacy.mkdir(parents=True)
    (legacy / "fusion-intake").symlink_to(
        canonical / "fusion-intake", target_is_directory=True)
    stale_copy = legacy / "fusion-planner"     # 1.2.0 copy-fallback relic
    stale_copy.mkdir()
    (stale_copy / "SKILL.md").write_text("old payload")
    (stale_copy / ".fusion-setup").write_text("1.0\nabc\n")
    mine = legacy / "fusion-mine"              # the user's own, not ours
    mine.mkdir()
    results = setup.fan_out(canonical, setup.detect_agents(home),
                            force=False)
    pi = {r["skill"]: r for r in results if r["agent"] == "Pi"}
    assert pi["fusion-intake"]["action"] == "unlinked"
    assert not (legacy / "fusion-intake").exists()
    assert pi["fusion-planner"]["action"] == "unlinked"
    assert not stale_copy.exists()
    assert pi["fusion-mine"]["action"] == "left"
    assert mine.is_dir()
    assert pi["*"]["action"] == "standard"     # and Pi reads the std dir
    # no new links were created in the legacy dir
    assert not (legacy / "fusion-analyst").exists()


def test_remove_all_sweeps_legacy_dirs(home, canonical):
    (home / ".codex").mkdir()
    legacy = home / ".codex" / "skills"
    legacy.mkdir(parents=True)
    (legacy / "fusion-intake").symlink_to(
        canonical / "fusion-intake", target_is_directory=True)
    results = setup.remove_all(canonical, home)
    assert not (legacy / "fusion-intake").exists()
    assert any(r["agent"] == "Codex" and r["action"] == "unlinked"
               for r in results)
    assert not (canonical / "fusion-intake").exists()
```

- [ ] **Step 5: Hunt down every other test pinning the old registry**

Run: `cd cli && grep -rn '"Pi"\|Codex\|\.pi\b\|\.codex' tests/` and
`uv run pytest -q`. Any test asserting Pi/Codex link behavior (check
`test_cli_setup.py` and `test_setup_core.py` especially) must be
updated to the new truth — Pi/Codex are standard-mode readers of the
canonical dir. Do not weaken assertions; retarget them.

- [ ] **Step 6: Full suite green, commit**

Run: `cd cli && uv run pytest -q` — green.

```bash
git add cli/src/fusion/setup.py cli/src/fusion/cli.py cli/tests/
git commit -m "fix: Pi and Codex read ~/.agents/skills natively — standard mode + legacy link sweep"
```

---

### Task 3: The e2e regression — the destruction topology runs in CI forever

**Files:**
- Modify: `.github/workflows/ci.yml` (installer-e2e POSIX step)

**Interfaces:**
- Consumes: `"served"` action (Task 1), Pi standard mode (Task 2),
  `$BIN/fusion` and `$SANDBOX` from the existing step.

- [ ] **Step 1: Extend the POSIX e2e step**

In `.github/workflows/ci.yml`, append to the
"Run install.sh against the local wheel (sandbox HOME)" step's script,
after the final `test ! -e "$SANDBOX/.claude/skills/fusion-intake"`:

```bash
          # regression: agent skills dir symlinked AT the canonical dir
          # (v1.1.0-v1.2.0 destroyed every canonical skill here)
          SANDBOX2="$(mktemp -d)"
          mkdir -p "$SANDBOX2/.agents/skills" "$SANDBOX2/.claude" "$SANDBOX2/.pi"
          ln -s "$SANDBOX2/.agents/skills" "$SANDBOX2/.claude/skills"
          HOME="$SANDBOX2" "$BIN/fusion" setup | tee setup2.out
          grep -q "served" setup2.out
          test -f "$SANDBOX2/.agents/skills/fusion-intake/SKILL.md"
          test ! -L "$SANDBOX2/.agents/skills/fusion-intake"
          # Pi reads the standard dir natively — no links of our own
          test ! -e "$SANDBOX2/.pi/agent/skills/fusion-intake"
          HOME="$SANDBOX2" "$BIN/fusion" setup --remove
          test ! -e "$SANDBOX2/.agents/skills/fusion-intake"
          test -L "$SANDBOX2/.claude/skills"
```

Windows deliberately skips this block: creating directory symlinks
there needs Developer Mode or elevation the runner does not guarantee,
and the guard code is platform-independent Python already covered by
the unit tests on the Windows suites job.

- [ ] **Step 2: Validate the workflow locally as far as possible**

Run: `cd cli && uv run pytest -q` (unchanged, green) and lint the YAML:
`uv run python -c "import yaml; yaml.safe_load(open('../.github/workflows/ci.yml'))"`.
Then rehearse the new block manually against a sandbox (same commands,
local wheel via `uv tool install --force ../dist/...` or the repo
install) OR rely on the live CI run at push time — state which you did
in your report.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: installer e2e pins the symlinked-skills-dir topology and Pi standard mode"
```

---

## After the tasks (controller-run, already user-authorized)

1. Final whole-branch review (most capable model) with the full diff
   package; fix wave if findings; merge `setup-registry-fix` to `main`
   ff-only.
2. Release v1.2.1: bump `cli/pyproject.toml` + `uv lock`, add friction
   #10 to `docs/dogfood/frictions.md` (the registry/destruction find,
   severity blocker, fixed by this batch), full local gates, push,
   tag `v1.2.1`, watch the release run (full ci gate now includes the
   new e2e block), wait out PyPI propagation, live sandbox acceptance
   INCLUDING the symlinked topology against the published wheel.
3. Real-machine remediation (the reason this batch exists): run
   `fusion setup` on the user's machine — expected: canonical copies
   in `~/.agents/skills` update to the v1.2 payload, Claude Code row
   reports "served" (its skills dir IS the canonical via the user's
   symlink), Pi/Codex report standard with nothing to sweep. Then
   remind: restart agents so the changed skill descriptions reload.
