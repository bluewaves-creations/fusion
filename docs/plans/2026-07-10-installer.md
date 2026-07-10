# Fusion One-Line Installer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One line installs Fusion — uv (which brings Python), the CLI from PyPI, the four skills into every detected agent — on macOS, Linux, and Windows, exactly as specified in `docs/specs/2026-07-10-installer-design.md`.

**Architecture:** Thin bootstraps (`install.sh`, `install.ps1`) ensure uv and `uv tool install fusion-cli`, then hand off to a new `fusion setup` command where all real logic lives in Python: skills bundled into the wheel by a hatchling build hook, canonical install to `~/.agents/skills`, symlink fan-out to agents that don't read the standard dir, environment advice, `--remove`. CI matrix + PyPI trusted publishing complete the pipeline.

**Tech Stack:** Python ≥3.11 (stdlib only — no new runtime deps), hatchling build hook, POSIX sh + PowerShell ≥5, GitHub Actions, pytest.

## Global Constraints

1. Work on `main`, one commit per task, never push.
2. The spec (`docs/specs/2026-07-10-installer-design.md`) is binding; its "Decisions already made" table and §Non-goals are settled — do not relitigate.
3. No sudo anywhere; writes only under `$HOME` (and the repo).
4. CLI gains NO new runtime dependencies (`dependencies = ["pyyaml>=6.0"]` stays as-is).
5. Suites stay green: CLI 135 + new tests, intake 77, librarian 22, `fusion check examples/crazy-ones` → 0 errors 0 warnings, conventions card ×4 byte-identical (`cli/tests/test_skill_family.py`).
6. Env vars and flags exactly as specced: `FUSION_VERSION`, `FUSION_PACKAGE_SPEC`, `FUSION_SKILLS_DIR`, `FUSION_NO_AGENTS`, `FUSION_NO_MODIFY_PATH`; `fusion setup [--json] [--force] [--remove] [--skills-dir PATH] [--no-agents]` (flags win over env).
7. Setup never destroys content it didn't create: foreign real dirs / foreign symlinks are warned and left; `--force` overrides; `--remove` is attribution-checked (symlink must point into the canonical dir; a copy must hash-match the bundled payload).
8. All new user-facing text: declarative, warm-but-terse, no exclamation marks, ~76-char wrapping in prose files.
9. Tests must not touch the real `$HOME` — every setup test runs against a `tmp_path` home.
10. `python` in test code means the CLI's environment (`cd cli && uv run --group dev pytest`).

---

### Task 1: The build hook — skills ride inside the wheel

**Files:**
- Create: `cli/hatch_build.py`
- Modify: `cli/pyproject.toml` (register hook)
- Modify: `cli/.gitignore` (create if absent: ignore `src/fusion/_skills/`)
- Test: `cli/tests/test_build_payload.py`

**Interfaces:**
- Produces: wheel (and sdist) containing `fusion/_skills/fusion-<name>/**` for the four skills, minus `tests/`, `__pycache__/`, `.pytest_cache/`. Task 2's `payload_root()` reads `fusion/_skills` via `importlib.resources`.

- [ ] **Step 1: Write the failing test**

```python
# cli/tests/test_build_payload.py
"""The wheel carries the four skills, byte-identical to the repo's."""
import subprocess
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
CLI = REPO / "cli"
SKILLS = REPO / "skills"
EXCLUDED_PARTS = {"tests", "__pycache__", ".pytest_cache"}


@pytest.fixture(scope="module")
def wheel(tmp_path_factory) -> zipfile.ZipFile:
    out = tmp_path_factory.mktemp("dist")
    subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(out)],
        cwd=CLI, check=True, capture_output=True,
    )
    whl = next(out.glob("fusion_cli-*.whl"))
    return zipfile.ZipFile(whl)


def _repo_skill_files() -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for skill in sorted(SKILLS.glob("fusion-*")):
        for f in sorted(skill.rglob("*")):
            if f.is_dir():
                continue
            rel = f.relative_to(SKILLS)
            if EXCLUDED_PARTS & set(rel.parts):
                continue
            files[f"fusion/_skills/{rel.as_posix()}"] = f.read_bytes()
    return files


def test_wheel_bundles_all_four_skills(wheel):
    names = {n for n in wheel.namelist() if n.startswith("fusion/_skills/")}
    tops = {n.split("/")[2] for n in names}
    assert tops == {"fusion-intake", "fusion-librarian",
                    "fusion-planner", "fusion-analyst"}


def test_bundled_tree_is_byte_identical(wheel):
    expected = _repo_skill_files()
    assert expected, "repo skills must exist"
    bundled = {n: wheel.read(n) for n in wheel.namelist()
               if n.startswith("fusion/_skills/")}
    assert bundled == expected


def test_no_test_dirs_in_wheel(wheel):
    assert not [n for n in wheel.namelist()
                if n.startswith("fusion/_skills/")
                and EXCLUDED_PARTS & set(n.split("/"))]


def test_conventions_card_x4_inside_wheel(wheel):
    cards = [wheel.read(f"fusion/_skills/fusion-{s}/references/fusion-conventions.md")
             for s in ("intake", "librarian", "planner", "analyst")]
    assert len({c for c in cards}) == 1
```

- [ ] **Step 2: Run it to make sure it fails**

Run: `cd cli && uv run --group dev pytest tests/test_build_payload.py -x -q`
Expected: FAIL in the fixture or first test — the wheel contains no `fusion/_skills/`.

- [ ] **Step 3: Write the hook**

```python
# cli/hatch_build.py
"""Build hook: bundle the repo's skills/fusion-* into the wheel as
fusion/_skills/. The repo's skills/ directory is the single source of
truth; this hook re-stages it at every build, so the wheel cannot drift.

Source resolution order:
  1. <cli>/../skills   — normal repo build
  2. <cli>/skills      — building from an sdist (the sdist hook below
                         copies skills/ inside so wheel-from-sdist works)
"""
import shutil
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

EXCLUDE = ("tests", "__pycache__", ".pytest_cache")


def _skills_source(root: Path) -> Path:
    for candidate in (root.parent / "skills", root / "skills"):
        if sorted(candidate.glob("fusion-*")):
            return candidate
    raise RuntimeError(
        f"no fusion-* skills found beside {root} — cannot build fusion-cli"
    )


class SkillsBundleHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version, build_data):
        root = Path(self.root)
        src = _skills_source(root)
        if self.target_name == "sdist":
            # ship skills/ inside the sdist so a wheel built from it
            # finds them via resolution order #2
            build_data.setdefault("force_include", {})
            for skill in sorted(src.glob("fusion-*")):
                build_data["force_include"][str(skill)] = f"skills/{skill.name}"
            return
        staged = root / "src" / "fusion" / "_skills"
        if staged.exists():
            shutil.rmtree(staged)
        for skill in sorted(src.glob("fusion-*")):
            shutil.copytree(skill, staged / skill.name,
                            ignore=shutil.ignore_patterns(*EXCLUDE))

    def finalize(self, version, build_data, artifact_path):
        staged = Path(self.root) / "src" / "fusion" / "_skills"
        if staged.exists():
            shutil.rmtree(staged)
```

Register in `cli/pyproject.toml` (add after the `[tool.hatch.build.targets.wheel]` table):

```toml
[tool.hatch.build.targets.wheel.hooks.custom]
path = "hatch_build.py"

[tool.hatch.build.targets.sdist.hooks.custom]
path = "hatch_build.py"

[tool.hatch.build.targets.wheel.force-include]
```

(The empty `force-include` table is NOT needed — omit it. Only the two hook registrations.) Also ensure the staged dir ships in the wheel: because `_skills` is staged inside `src/fusion/` before the wheel assembles, `packages = ["src/fusion"]` picks it up automatically — but hatchling excludes it if `.gitignore` patterns apply to wheel contents; hatchling honors VCS ignores for sdists only, wheels build from `packages`, so staging works. Verify empirically in Step 4.

Create `cli/.gitignore`:

```
src/fusion/_skills/
```

- [ ] **Step 4: Run the tests**

Run: `cd cli && uv run --group dev pytest tests/test_build_payload.py -q`
Expected: 4 passed. If `_skills` is missing from the wheel, hatchling pruned the staged dir — fall back to explicit inclusion by adding to pyproject:

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/fusion"]
artifacts = ["src/fusion/_skills"]
```

and re-run.

- [ ] **Step 5: Full CLI suite + fixture; verify a repo build cleans up**

Run: `cd cli && uv run --group dev pytest -q` → 139 passed (135 + 4).
Run: `git status --porcelain` → no `src/fusion/_skills` residue (finalize removed it).
Run: `cd cli && uv run fusion check ../examples/crazy-ones` → 0/0.

- [ ] **Step 6: Commit**

```bash
git add cli/hatch_build.py cli/pyproject.toml cli/.gitignore cli/tests/test_build_payload.py
git commit -m "cli: the wheel carries the skills — build hook bundles fusion-* with drift-proof tests"
```

### Task 2: setup module core — payload, canonical install, digest

**Files:**
- Create: `cli/src/fusion/setup.py`
- Test: `cli/tests/test_setup_core.py`

**Interfaces:**
- Consumes: `fusion/_skills` payload (Task 1); repo `skills/` as dev fallback.
- Produces (used by Tasks 3–4):
  - `class SetupError(Exception)`
  - `payload_root() -> Path` — bundled `_skills` dir, else repo `skills/`, else raises `SetupError`
  - `payload_version() -> str` — `importlib.metadata.version("fusion-cli")`, `"dev"` on PackageNotFoundError
  - `tree_digest(path: Path) -> str` — order-independent sha256 over (relpath, bytes) of all files
  - `install_canonical(payload: Path, skills_dir: Path, force: bool) -> list[dict]` — one `{"skill", "action", "detail"}` per `fusion-*`; actions: `installed`, `updated`, `up-to-date`, `left` (foreign symlink, no force), `replaced` (with force)

- [ ] **Step 1: Write the failing tests**

```python
# cli/tests/test_setup_core.py
"""setup core: payload resolution, canonical install, digests."""
from pathlib import Path

import pytest

from fusion import setup


def make_payload(root: Path, names=("fusion-intake", "fusion-librarian")) -> Path:
    for name in names:
        d = root / name
        (d / "references").mkdir(parents=True)
        (d / "SKILL.md").write_text(f"---\nname: {name}\n---\nbody\n")
        (d / "references" / "guide.md").write_text("guide\n")
    return root


def test_payload_root_prefers_bundled_then_repo():
    # in the dev checkout there is no _skills package dir, so the repo
    # skills/ fallback resolves — and it contains the four real skills
    root = setup.payload_root()
    assert sorted(p.name for p in root.glob("fusion-*")) == [
        "fusion-analyst", "fusion-intake", "fusion-librarian", "fusion-planner"]


def test_tree_digest_stable_and_content_sensitive(tmp_path):
    a = make_payload(tmp_path / "a")
    b = make_payload(tmp_path / "b")
    d1 = setup.tree_digest(a / "fusion-intake")
    assert d1 == setup.tree_digest(b / "fusion-intake")
    (b / "fusion-intake" / "SKILL.md").write_text("changed")
    assert d1 != setup.tree_digest(b / "fusion-intake")


def test_install_canonical_fresh(tmp_path):
    payload = make_payload(tmp_path / "payload")
    dest = tmp_path / "agents-skills"
    results = setup.install_canonical(payload, dest, force=False)
    assert {r["skill"]: r["action"] for r in results} == {
        "fusion-intake": "installed", "fusion-librarian": "installed"}
    assert (dest / "fusion-intake" / "references" / "guide.md").read_text() == "guide\n"


def test_install_canonical_refreshes_and_reports_upgrade(tmp_path):
    payload = make_payload(tmp_path / "payload")
    dest = tmp_path / "agents-skills"
    setup.install_canonical(payload, dest, force=False)
    (dest / "fusion-intake" / "SKILL.md").write_text("stale")
    results = setup.install_canonical(payload, dest, force=False)
    by = {r["skill"]: r["action"] for r in results}
    assert by["fusion-intake"] == "updated"
    assert by["fusion-librarian"] == "up-to-date"
    assert (dest / "fusion-intake" / "SKILL.md").read_text().startswith("---")


def test_install_canonical_leaves_foreign_symlink(tmp_path):
    payload = make_payload(tmp_path / "payload")
    dest = tmp_path / "agents-skills"
    dest.mkdir()
    theirs = tmp_path / "their-clone" / "fusion-intake"
    theirs.mkdir(parents=True)
    (dest / "fusion-intake").symlink_to(theirs)
    results = setup.install_canonical(payload, dest, force=False)
    by = {r["skill"]: r["action"] for r in results}
    assert by["fusion-intake"] == "left"
    assert (dest / "fusion-intake").is_symlink()
    # --force replaces it with a real dir
    results = setup.install_canonical(payload, dest, force=True)
    by = {r["skill"]: r["action"] for r in results}
    assert by["fusion-intake"] == "replaced"
    assert not (dest / "fusion-intake").is_symlink()
```

- [ ] **Step 2: Run to verify failure**

Run: `cd cli && uv run --group dev pytest tests/test_setup_core.py -x -q`
Expected: FAIL — `cannot import name 'setup'`.

- [ ] **Step 3: Implement**

```python
# cli/src/fusion/setup.py
"""fusion setup — the installer brain. Bootstraps hand off here; every
mechanical decision about skills placement lives in this module so it is
written once, runs identically on macOS/Linux/Windows, and is tested.

Never destroys content it did not create: foreign entries are warned and
left unless --force. Writes only under the given directories.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.resources
import shutil
from pathlib import Path


class SetupError(Exception):
    """A setup step that cannot proceed."""


def payload_root() -> Path:
    bundled = importlib.resources.files("fusion") / "_skills"
    p = Path(str(bundled))
    if p.is_dir() and sorted(p.glob("fusion-*")):
        return p
    repo = Path(__file__).resolve().parents[3] / "skills"
    if repo.is_dir() and sorted(repo.glob("fusion-*")):
        return repo
    raise SetupError(
        "no skills payload: neither bundled fusion/_skills nor a repo "
        "skills/ directory — reinstall fusion-cli"
    )


def payload_version() -> str:
    try:
        return importlib.metadata.version("fusion-cli")
    except importlib.metadata.PackageNotFoundError:
        return "dev"


def tree_digest(path: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(p for p in path.rglob("*") if p.is_file()):
        h.update(f.relative_to(path).as_posix().encode())
        h.update(b"\0")
        h.update(f.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def install_canonical(payload: Path, skills_dir: Path,
                      force: bool) -> list[dict]:
    skills_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for skill in sorted(payload.glob("fusion-*")):
        dest = skills_dir / skill.name
        if dest.is_symlink():
            if not force:
                results.append({
                    "skill": skill.name, "action": "left",
                    "detail": f"{dest} is a symlink you manage — "
                              f"--force replaces it"})
                continue
            dest.unlink()
            shutil.copytree(skill, dest)
            results.append({"skill": skill.name, "action": "replaced",
                            "detail": str(dest)})
            continue
        if dest.is_dir():
            if tree_digest(dest) == tree_digest(skill):
                results.append({"skill": skill.name, "action": "up-to-date",
                                "detail": str(dest)})
                continue
            shutil.rmtree(dest)
            shutil.copytree(skill, dest)
            results.append({"skill": skill.name, "action": "updated",
                            "detail": str(dest)})
            continue
        shutil.copytree(skill, dest)
        results.append({"skill": skill.name, "action": "installed",
                        "detail": str(dest)})
    return results
```

- [ ] **Step 4: Run the tests**

Run: `cd cli && uv run --group dev pytest tests/test_setup_core.py -q`
Expected: 5 passed.

- [ ] **Step 5: Full suite + commit**

Run: `cd cli && uv run --group dev pytest -q` → 144 passed.

```bash
git add cli/src/fusion/setup.py cli/tests/test_setup_core.py
git commit -m "cli: setup core — payload resolution, canonical install, drift-honest digests"
```

### Task 3: Agent registry, fan-out, remove

**Files:**
- Modify: `cli/src/fusion/setup.py` (append)
- Test: `cli/tests/test_setup_agents.py`

**Interfaces:**
- Consumes: `tree_digest`, canonical dir layout from Task 2.
- Produces (used by Task 4):
  - `AGENTS: list[dict]` — rows `{"name", "marker", "skills_subdir", "mode"}` with `mode` in `{"link", "standard"}`; `marker`/`skills_subdir` are home-relative POSIX strings
  - `detect_agents(home: Path) -> list[dict]` — registry rows whose marker dir exists, each augmented with `"skills_dir": Path`
  - `fan_out(canonical: Path, agents: list[dict], force: bool) -> list[dict]` — per (agent, skill): actions `linked`, `copied` (symlink unavailable), `up-to-date`, `left`, `replaced`, or per agent a single `standard` row
  - `remove_all(canonical: Path, home: Path) -> list[dict]` — attribution-checked removal; actions `removed`, `left`

- [ ] **Step 1: Write the failing tests**

```python
# cli/tests/test_setup_agents.py
"""Agent detection, fan-out, and the attribution-checked remove."""
from pathlib import Path

import pytest

from fusion import setup
from tests.test_setup_core import make_payload


@pytest.fixture
def home(tmp_path) -> Path:
    return tmp_path


@pytest.fixture
def canonical(home) -> Path:
    payload = make_payload(home / "_payload")
    dest = home / ".agents" / "skills"
    setup.install_canonical(payload, dest, force=False)
    return dest


def test_registry_shape():
    names = {a["name"] for a in setup.AGENTS}
    assert {"Claude Code", "Codex", "Pi", "Cursor", "Gemini CLI",
            "opencode", "Goose"} == names
    modes = {a["name"]: a["mode"] for a in setup.AGENTS}
    assert modes["Claude Code"] == "link"
    assert modes["Cursor"] == "standard"


def test_detect_agents_only_present(home):
    (home / ".claude").mkdir()
    (home / ".config" / "goose").mkdir(parents=True)
    found = {a["name"] for a in setup.detect_agents(home)}
    assert found == {"Claude Code", "Goose"}


def test_fan_out_links_link_agents_and_reports_standard(home, canonical):
    (home / ".claude").mkdir()
    (home / ".cursor").mkdir()
    results = setup.fan_out(canonical, setup.detect_agents(home), force=False)
    claude = [r for r in results if r["agent"] == "Claude Code"]
    assert {r["action"] for r in claude} == {"linked"}
    link = home / ".claude" / "skills" / "fusion-intake"
    assert link.is_symlink() and link.resolve() == (canonical / "fusion-intake").resolve()
    cursor = [r for r in results if r["agent"] == "Cursor"]
    assert len(cursor) == 1 and cursor[0]["action"] == "standard"
    # idempotent re-run
    again = setup.fan_out(canonical, setup.detect_agents(home), force=False)
    assert {r["action"] for r in again if r["agent"] == "Claude Code"} == {"up-to-date"}


def test_fan_out_leaves_foreign_dir_unless_forced(home, canonical):
    (home / ".claude" / "skills" / "fusion-intake").mkdir(parents=True)
    results = setup.fan_out(canonical, setup.detect_agents(home), force=False)
    intake = [r for r in results if r["skill"] == "fusion-intake"][0]
    assert intake["action"] == "left"
    results = setup.fan_out(canonical, setup.detect_agents(home), force=True)
    intake = [r for r in results if r["skill"] == "fusion-intake"][0]
    assert intake["action"] == "replaced"
    assert (home / ".claude" / "skills" / "fusion-intake").is_symlink()


def test_fan_out_copies_when_symlink_unavailable(home, canonical, monkeypatch):
    (home / ".pi").mkdir()

    def no_symlink(*a, **k):
        raise OSError("symlinks disabled")
    monkeypatch.setattr(setup.os, "symlink", no_symlink)
    results = setup.fan_out(canonical, setup.detect_agents(home), force=False)
    pi = [r for r in results if r["agent"] == "Pi"]
    assert {r["action"] for r in pi} == {"copied"}
    copied = home / ".pi" / "agent" / "skills" / "fusion-intake"
    assert copied.is_dir() and not copied.is_symlink()
    # a stale copy refreshes on re-run
    (copied / "SKILL.md").write_text("stale")
    again = setup.fan_out(canonical, setup.detect_agents(home), force=False)
    pi_intake = [r for r in again if r["skill"] == "fusion-intake"][0]
    assert pi_intake["action"] == "copied"


def test_remove_all_is_attribution_checked(home, canonical):
    (home / ".claude").mkdir()
    setup.fan_out(canonical, setup.detect_agents(home), force=False)
    foreign = home / ".claude" / "skills" / "fusion-mine"
    foreign.mkdir()
    results = setup.remove_all(canonical, home)
    assert foreign.is_dir()                      # not ours — untouched
    assert not (home / ".claude" / "skills" / "fusion-intake").exists()
    assert not (canonical / "fusion-intake").exists()
    assert any(r["action"] == "removed" for r in results)
```

- [ ] **Step 2: Verify failure**

Run: `cd cli && uv run --group dev pytest tests/test_setup_agents.py -x -q`
Expected: FAIL — `AGENTS` not defined.

- [ ] **Step 3: Implement (append to setup.py)**

```python
import os  # add to the imports at top of setup.py

# One row per agent. mode "link": the agent does not read the standard
# ~/.agents/skills dir, so each fusion-* skill gets a symlink (or copy)
# in its own skills dir. mode "standard": the agent reads the standard
# dir — creating links there too would load every skill twice.
AGENTS = [
    {"name": "Claude Code", "marker": ".claude",
     "skills_subdir": ".claude/skills", "mode": "link",
     "docs_url": "https://code.claude.com/docs/en/skills"},
    {"name": "Codex", "marker": ".codex",
     "skills_subdir": ".codex/skills", "mode": "link",
     "docs_url": "https://developers.openai.com/codex/skills"},
    {"name": "Pi", "marker": ".pi",
     "skills_subdir": ".pi/agent/skills", "mode": "link",
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


def detect_agents(home: Path) -> list[dict]:
    found = []
    for row in AGENTS:
        if (home / row["marker"]).is_dir():
            found.append({**row, "skills_dir": home / row["skills_subdir"]})
    return found


def _points_into(link: Path, canonical: Path) -> bool:
    try:
        return link.resolve().is_relative_to(canonical.resolve())
    except OSError:
        return False


def fan_out(canonical: Path, agents: list[dict], force: bool) -> list[dict]:
    results = []
    skills = sorted(canonical.glob("fusion-*"))
    for agent in agents:
        if agent["mode"] == "standard":
            results.append({"agent": agent["name"], "skill": "*",
                            "action": "standard",
                            "detail": "reads ~/.agents/skills — nothing to do"})
            continue
        agent["skills_dir"].mkdir(parents=True, exist_ok=True)
        for skill in skills:
            target = agent["skills_dir"] / skill.name
            row = {"agent": agent["name"], "skill": skill.name}
            if target.is_symlink():
                if _points_into(target, canonical):
                    results.append({**row, "action": "up-to-date",
                                    "detail": str(target)})
                    continue
                if not force:
                    results.append({**row, "action": "left",
                                    "detail": f"{target} links elsewhere — "
                                              f"--force replaces"})
                    continue
                target.unlink()
            elif target.is_dir():
                if tree_digest(target) == tree_digest(skill):
                    pass          # our copy, refresh below keeps it current
                elif not force and not _is_our_stale_copy(target, skill):
                    results.append({**row, "action": "left",
                                    "detail": f"{target} exists and is not "
                                              f"ours — --force replaces"})
                    continue
                shutil.rmtree(target)
            try:
                os.symlink(skill, target, target_is_directory=True)
                results.append({**row, "action": "linked",
                                "detail": str(target)})
            except OSError:
                shutil.copytree(skill, target)
                results.append({**row, "action": "copied",
                                "detail": f"{target} (symlinks unavailable — "
                                          f"re-run setup after upgrades)"})
    return results


def _is_our_stale_copy(target: Path, skill: Path) -> bool:
    # a copy is "ours" if it looks like the same skill (SKILL.md exists
    # with the same name line) — content may be a stale prior version
    ours, theirs = target / "SKILL.md", skill / "SKILL.md"
    if not (ours.is_file() and theirs.is_file()):
        return False
    def name_line(p: Path) -> str:
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.startswith("name:"):
                return line
        return ""
    return name_line(ours) == name_line(theirs)


def remove_all(canonical: Path, home: Path) -> list[dict]:
    results = []
    for agent in detect_agents(home):
        if agent["mode"] == "standard":
            continue
        entries = (sorted(agent["skills_dir"].glob("fusion-*"))
                   if agent["skills_dir"].is_dir() else [])
        for entry in entries:
            row = {"agent": agent["name"], "skill": entry.name}
            if entry.is_symlink() and _points_into(entry, canonical):
                entry.unlink()
                results.append({**row, "action": "removed",
                                "detail": str(entry)})
            elif entry.is_dir() and not entry.is_symlink() \
                    and (canonical / entry.name).is_dir() \
                    and tree_digest(entry) == tree_digest(canonical / entry.name):
                shutil.rmtree(entry)
                results.append({**row, "action": "removed",
                                "detail": str(entry)})
            else:
                results.append({**row, "action": "left",
                                "detail": f"{entry} is not attributable to "
                                          f"setup — left in place"})
    for skill in sorted(canonical.glob("fusion-*")):
        row = {"agent": "canonical", "skill": skill.name}
        if skill.is_symlink():
            results.append({**row, "action": "left",
                            "detail": f"{skill} is a symlink you manage"})
            continue
        shutil.rmtree(skill)
        results.append({**row, "action": "removed", "detail": str(skill)})
    return results
```

Note the fix the tests force: in `fan_out`, a dir whose digest matches is
still replaced by a link/copy refresh (the `pass` branch falls through to
rmtree+relink) — this is what makes Windows copies refresh after upgrades
and `test_fan_out_copies_when_symlink_unavailable`'s stale-copy re-run
pass.

- [ ] **Step 4: Run the tests**

Run: `cd cli && uv run --group dev pytest tests/test_setup_agents.py -q`
Expected: 6 passed.

- [ ] **Step 5: Full suite + commit**

Run: `cd cli && uv run --group dev pytest -q` → 150 passed.

```bash
git add cli/src/fusion/setup.py cli/tests/test_setup_agents.py
git commit -m "cli: setup knows the agents — detect, fan out, remove with attribution"
```

### Task 4: `fusion setup` — the ninth command, wired and documented

**Files:**
- Modify: `cli/src/fusion/setup.py` (append `run_setup`, `environment_advice`)
- Modify: `cli/src/fusion/cli.py` (cmd_setup + parser)
- Modify: `cli/README.md` (command table + "nine commands")
- Modify: `skills/*/references/fusion-conventions.md` ×4 (CLI crib row; keep byte-identical)
- Modify: `skills/README.md` (install pointer)
- Test: `cli/tests/test_cli_setup.py`

**Interfaces:**
- Consumes: everything Tasks 2–3 produced.
- Produces: `fusion setup [--json] [--force] [--remove] [--skills-dir PATH] [--no-agents]`, exit 0/1, JSON envelope `{"ok": true, "cli": {"version"}, "skills": {"dir", "results"}, "agents": [...], "advice": [...]}`; `setup.run_setup(home, skills_dir, force, no_agents, remove) -> dict` (pure, testable, no printing).

- [ ] **Step 1: Write the failing tests**

```python
# cli/tests/test_cli_setup.py
"""fusion setup end to end through the CLI surface."""
import json
from pathlib import Path

import pytest

from fusion import setup
from fusion.cli import main
from tests.test_setup_core import make_payload


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))          # windows
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    payload = make_payload(tmp_path / "payload")
    monkeypatch.setattr(setup, "payload_root", lambda: payload)
    return home


def test_setup_json_reports_all_sections(sandbox, capsys):
    assert main(["setup", "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["skills"]["dir"].endswith(".agents/skills") or \
        out["skills"]["dir"].endswith(".agents\\skills")
    assert {r["action"] for r in out["skills"]["results"]} == {"installed"}
    assert any(a["agent"] == "Claude Code" and a["action"] == "linked"
               for a in out["agents"])
    assert isinstance(out["advice"], list)


def test_setup_skills_dir_and_no_agents(sandbox, capsys):
    custom = str(sandbox / "custom-skills")
    assert main(["setup", "--json", "--skills-dir", custom, "--no-agents"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["skills"]["dir"] == custom
    assert out["agents"] == []
    assert (Path(custom) / "fusion-intake").is_dir()


def test_setup_env_vars_apply_and_flags_win(sandbox, capsys, monkeypatch):
    monkeypatch.setenv("FUSION_SKILLS_DIR", str(sandbox / "from-env"))
    monkeypatch.setenv("FUSION_NO_AGENTS", "1")
    assert main(["setup", "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["skills"]["dir"] == str(sandbox / "from-env")
    assert out["agents"] == []


def test_setup_remove_round_trip(sandbox, capsys):
    assert main(["setup", "--json"]) == 0
    capsys.readouterr()
    assert main(["setup", "--remove", "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert not (sandbox / ".agents" / "skills" / "fusion-intake").exists()
    assert not (sandbox / ".claude" / "skills" / "fusion-intake").exists()
    assert "uv tool uninstall fusion-cli" in json.dumps(out)


def test_setup_human_report_names_agents(sandbox, capsys):
    assert main(["setup"]) == 0
    text = capsys.readouterr().out
    assert "Claude Code" in text and "fusion-intake" in text
    assert "next" in text.lower()
```

- [ ] **Step 2: Verify failure**

Run: `cd cli && uv run --group dev pytest tests/test_cli_setup.py -x -q`
Expected: FAIL — argparse: invalid choice 'setup'.

- [ ] **Step 3: Implement `run_setup` + advice (append to setup.py)**

```python
def environment_advice(home: Path) -> list[dict]:
    import os as _os
    import subprocess
    advice = []
    if shutil.which("fusion") is None:
        # spec §4d: fix PATH via uv's own mechanism when allowed
        if _os.environ.get("FUSION_NO_MODIFY_PATH") != "1" \
                and shutil.which("uv") is not None:
            done = subprocess.run(["uv", "tool", "update-shell"],
                                  capture_output=True).returncode == 0
            advice.append({
                "topic": "path",
                "text": "uv tool update-shell ran — restart your shell so "
                        "`fusion` resolves" if done else
                        "uv tool update-shell failed — add uv's tool bin "
                        "dir to PATH yourself (`uv tool dir --bin`)"})
        else:
            advice.append({
                "topic": "path",
                "text": "the uv tool bin dir is not on PATH — run: "
                        "uv tool update-shell (or manage PATH yourself)"})
    if shutil.which("git") is None:
        advice.append({
            "topic": "git",
            "text": "git not found — buckets are git repos; install git"})
    if shutil.which("soffice") is None:
        advice.append({
            "topic": "libreoffice",
            "text": "LibreOffice (soffice) not found — only docx/pptx/"
                    "legacy-office/html intake needs it "
                    "(brew install --cask libreoffice · apt install "
                    "libreoffice · winget install LibreOffice.LibreOffice)"})
    return advice


def run_setup(home: Path, skills_dir: Path, force: bool,
              no_agents: bool, remove: bool) -> dict:
    if remove:
        results = remove_all(skills_dir, home)
        return {"ok": True, "removed": results,
                "next": ["uv tool uninstall fusion-cli"]}
    payload = payload_root()
    skills = install_canonical(payload, skills_dir, force)
    agents = [] if no_agents else fan_out(
        skills_dir, detect_agents(home), force)
    return {
        "ok": True,
        "cli": {"version": payload_version()},
        "skills": {"dir": str(skills_dir), "results": skills},
        "agents": agents,
        "advice": environment_advice(home),
        "next": ["fusion new ~/buckets/personal --kind personal "
                 "--description \"Home base.\"",
                 "docs/GETTING-STARTED.md"],
    }
```

- [ ] **Step 4: Wire cmd_setup in cli.py**

Add handler beside the others (match house style — `_fail`, `_emit`):

```python
def cmd_setup(args) -> int:
    from fusion import setup as setup_mod
    import os as _os
    home = Path.home()
    skills_dir = Path(
        args.skills_dir
        or _os.environ.get("FUSION_SKILLS_DIR")
        or home / ".agents" / "skills")
    no_agents = args.no_agents or _os.environ.get("FUSION_NO_AGENTS") == "1"
    try:
        report = setup_mod.run_setup(home, skills_dir, args.force,
                                     no_agents, args.remove)
    except setup_mod.SetupError as exc:
        return _fail(str(exc), args.json)
    lines = _render_setup(report)
    _emit(report, args.json, "\n".join(lines))
    return 0


def _render_setup(report: dict) -> list[str]:
    lines = []
    if "removed" in report:
        for r in report["removed"]:
            lines.append(f"  {r['action']:>10}  {r['skill']}  ({r['agent']})")
        lines.append("done. final step: " + report["next"][0])
        return lines
    lines.append(f"fusion-cli {report['cli']['version']}")
    lines.append(f"skills → {report['skills']['dir']}")
    for r in report["skills"]["results"]:
        lines.append(f"  {r['action']:>10}  {r['skill']}")
    for a in report["agents"]:
        lines.append(f"  {a['agent']}: {a['action']} — {a['detail']}")
    for adv in report["advice"]:
        lines.append(f"  advice: {adv['text']}")
    lines.append("next: " + " · ".join(report["next"]))
    return lines
```

Parser wiring (after the `agenda` block in `main`'s parser builder):

```python
    p = sub.add_parser("setup", help="install skills into agents; --remove undoes it",
                       description="Install the bundled skills to the canonical "
                       "skills directory and link them into every detected agent. "
                       "Idempotent; never destroys what it did not create.")
    p.add_argument("--force", action="store_true",
                   help="replace foreign entries setup would otherwise leave")
    p.add_argument("--remove", action="store_true",
                   help="undo setup (attribution-checked), print the uninstall closer")
    p.add_argument("--skills-dir", help="canonical destination (default ~/.agents/skills; env FUSION_SKILLS_DIR)")
    p.add_argument("--no-agents", action="store_true",
                   help="skip agent fan-out (env FUSION_NO_AGENTS=1)")
    p.set_defaults(func=cmd_setup)
```

(If the shared `--json` flag is per-subparser in this codebase, add it the same way the other subparsers get it — follow the existing pattern.)

- [ ] **Step 5: Run the tests**

Run: `cd cli && uv run --group dev pytest tests/test_cli_setup.py -q`
Expected: 5 passed.

- [ ] **Step 6: Docs — the ninth command**

- `cli/README.md`: heading `## The eight commands (there is no ninth)` →
  `## The nine commands (there is no tenth)`; add table row
  `| \`fusion setup\` | Install the skills into every detected agent — the installer's brain. \`--remove\` undoes it |`
- Conventions card (edit `skills/fusion-intake/references/fusion-conventions.md`, add to the CLI crib table:
  `| \`fusion setup\` | install/refresh the skills into detected agents |`
  then `cp` over the other three copies as in the card's established flow).
- `skills/README.md` Install section: before the `cp -r` line add
  `The one-line installer does this for you — see the repository README. Manually:`
- [ ] **Step 7: Verify + commit**

Run: `cd cli && uv run --group dev pytest -q` → 155 passed (incl. test_skill_family ×4 identity).
Run: `cd cli && uv run fusion check ../examples/crazy-ones` → 0/0.
Run: `shasum skills/*/references/fusion-conventions.md` → one hash.

```bash
git add cli/src/fusion/setup.py cli/src/fusion/cli.py cli/tests/test_cli_setup.py cli/README.md skills/README.md skills/*/references/fusion-conventions.md
git commit -m "cli: fusion setup — the ninth command (there is no tenth)"
```

### Task 5: install.sh — the POSIX bootstrap

**Files:**
- Create: `install.sh` (repo root)

**Interfaces:**
- Consumes: `fusion setup` (Task 4), env vars from Global Constraint 6.
- Produces: the curl-able bootstrap; CI (Task 7) runs it end to end.

- [ ] **Step 1: Write it**

```sh
#!/bin/sh
# Fusion installer — https://github.com/bluewaves-creations/fusion
# Usage:  curl -fsSL https://raw.githubusercontent.com/bluewaves-creations/fusion/main/install.sh | sh
# Env:    FUSION_VERSION, FUSION_PACKAGE_SPEC, FUSION_SKILLS_DIR,
#         FUSION_NO_AGENTS, FUSION_NO_MODIFY_PATH
# It ensures uv (which brings Python), installs fusion-cli from PyPI, and
# hands off to `fusion setup` for the skills. No sudo. Idempotent.
set -u

say()  { printf '%s\n' "$*" >&2; }
err()  { say "fusion install: error: $*"; exit 1; }

command -v curl >/dev/null 2>&1 || command -v wget >/dev/null 2>&1 \
  || err "need curl or wget. install one, or install by hand:
  1) https://docs.astral.sh/uv/  2) uv tool install fusion-cli  3) fusion setup"

fetch() {  # fetch URL > stdout
  if command -v curl >/dev/null 2>&1; then curl -fsSL "$1"
  else wget -qO- "$1"; fi
}

# 1 — uv (brings its own Python; PyPI hashes verified by uv itself)
if command -v uv >/dev/null 2>&1; then
  UV=uv
else
  say "installing uv (Astral's official installer)…"
  if [ "${FUSION_NO_MODIFY_PATH:-}" = "1" ]; then
    fetch https://astral.sh/uv/install.sh | UV_NO_MODIFY_PATH=1 sh \
      || err "uv install failed — see https://docs.astral.sh/uv/"
  else
    fetch https://astral.sh/uv/install.sh | sh \
      || err "uv install failed — see https://docs.astral.sh/uv/"
  fi
  UV="$HOME/.local/bin/uv"
  [ -x "$UV" ] || UV="${XDG_BIN_HOME:-$HOME/.local/bin}/uv"
  [ -x "$UV" ] || err "uv installed but not found at $HOME/.local/bin/uv —
  restart your shell and re-run, or run: uv tool install fusion-cli && fusion setup"
fi

# 2 — the CLI
SPEC="${FUSION_PACKAGE_SPEC:-fusion-cli${FUSION_VERSION:+==$FUSION_VERSION}}"
say "installing $SPEC…"
"$UV" tool install --force "$SPEC" \
  || err "uv tool install failed. manual step: $UV tool install --force '$SPEC'"

# 3 — hand off to the brain
BIN="$("$UV" tool dir --bin)" || err "could not resolve uv's tool bin dir"
[ -x "$BIN/fusion" ] || err "fusion not found in $BIN after install"
exec "$BIN/fusion" setup
```

- [ ] **Step 2: shellcheck**

Run: `shellcheck install.sh` (install via `brew install shellcheck` if absent)
Expected: no findings. Fix any it reports.

- [ ] **Step 3: Local end-to-end sanity (sandboxed HOME)**

```bash
cd ~/Developer/fusion/cli && uv build --wheel --out-dir /tmp/fusion-dist
WHEEL=$(ls /tmp/fusion-dist/fusion_cli-*.whl)
SANDBOX=$(mktemp -d)
mkdir -p "$SANDBOX/.claude"
HOME="$SANDBOX" FUSION_PACKAGE_SPEC="fusion-cli@$WHEEL" sh ~/Developer/fusion/install.sh
```

Expected: uv bootstraps into the sandbox home, installs the wheel, `fusion setup` prints the report; verify `ls "$SANDBOX/.agents/skills"` shows the four skills and `ls -l "$SANDBOX/.claude/skills"` shows symlinks. If `uv tool install` rejects the `name@path` spec form, use `FUSION_PACKAGE_SPEC="$WHEEL"` (a bare wheel path is a valid spec) and note which form worked in the report — CI (Task 7) must use the same form. Then `rm -rf "$SANDBOX"`.

- [ ] **Step 4: Commit**

```bash
git add install.sh
git commit -m "installer: one line for macOS and Linux — ensure uv, install the CLI, hand off to the brain"
```

### Task 6: install.ps1 — the Windows bootstrap

**Files:**
- Create: `install.ps1` (repo root)

- [ ] **Step 1: Write it**

```powershell
# Fusion installer (Windows, preview) — https://github.com/bluewaves-creations/fusion
# Usage: powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/bluewaves-creations/fusion/main/install.ps1 | iex"
# Env:   FUSION_VERSION, FUSION_PACKAGE_SPEC, FUSION_SKILLS_DIR,
#        FUSION_NO_AGENTS, FUSION_NO_MODIFY_PATH
$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

function Say([string]$m) { Write-Host $m }
function Fail([string]$m) { Write-Error "fusion install: $m"; exit 1 }

# 1 — uv (registry-based PATH handling is uv's own; we never call setx)
$uv = Get-Command uv -ErrorAction SilentlyContinue
if ($uv) { $uvExe = $uv.Source }
else {
    Say "installing uv (Astral's official installer)..."
    if ($env:FUSION_NO_MODIFY_PATH -eq "1") { $env:UV_NO_MODIFY_PATH = "1" }
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    $uvExe = Join-Path $HOME ".local\bin\uv.exe"
    if (-not (Test-Path $uvExe)) { Fail "uv installed but not found at $uvExe - restart the terminal and re-run" }
}

# 2 — the CLI
$spec = if ($env:FUSION_PACKAGE_SPEC) { $env:FUSION_PACKAGE_SPEC }
        elseif ($env:FUSION_VERSION)  { "fusion-cli==$($env:FUSION_VERSION)" }
        else                          { "fusion-cli" }
Say "installing $spec..."
& $uvExe tool install --force $spec
if ($LASTEXITCODE -ne 0) { Fail "uv tool install failed. manual step: uv tool install --force $spec" }

# 3 — hand off to the brain
$bin = (& $uvExe tool dir --bin).Trim()
$fusion = Join-Path $bin "fusion.exe"
if (-not (Test-Path $fusion)) { Fail "fusion not found in $bin after install" }
& $fusion setup
exit $LASTEXITCODE
```

- [ ] **Step 2: Static sanity on macOS**

Run: `pwsh -NoProfile -Command "& { \$c = Get-Content -Raw install.ps1; [scriptblock]::Create(\$c) | Out-Null; 'parses' }"` if `pwsh` is installed (`brew install powershell` — optional); otherwise rely on CI (Task 7 runs the script for real on windows-latest). Note in the commit message which verification ran.

- [ ] **Step 3: Commit**

```bash
git add install.ps1
git commit -m "installer: the Windows line (preview) — same three steps, idiomatic PowerShell"
```

### Task 7: CI — matrix, shellcheck, installer e2e

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Write the workflow**

```yaml
name: ci
on:
  push: { branches: [main] }
  pull_request:

jobs:
  suites:
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - name: CLI suite (incl. build-payload + setup)
        working-directory: cli
        run: uv run --group dev pytest -q
      - name: Fixture conformance
        working-directory: cli
        run: uv run fusion check ../examples/crazy-ones
      - name: Skills suites (POSIX only — they shell out to POSIX tools)
        if: runner.os != 'Windows'
        run: |
          uv run --with pytest --with pyyaml --with openpyxl --with pymupdf pytest skills/fusion-intake/tests -q
          uv run --with pytest --with pyyaml pytest skills/fusion-librarian/tests -q

  shellcheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: sudo apt-get update && sudo apt-get install -y shellcheck
      - run: shellcheck install.sh

  installer-e2e:
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - name: Build the wheel
        working-directory: cli
        run: uv build --wheel --out-dir ../dist
      - name: Run install.sh against the local wheel (sandbox HOME)
        if: runner.os != 'Windows'
        shell: bash
        run: |
          SANDBOX="$(mktemp -d)"
          mkdir -p "$SANDBOX/.claude"
          WHEEL="$(ls dist/fusion_cli-*.whl)"
          HOME="$SANDBOX" FUSION_PACKAGE_SPEC="$WHEEL" sh install.sh
          BIN="$(HOME=$SANDBOX uv tool dir --bin)"
          HOME="$SANDBOX" "$BIN/fusion" --version
          test -d "$SANDBOX/.agents/skills/fusion-intake"
          test -L "$SANDBOX/.claude/skills/fusion-intake"
          # idempotent re-run
          HOME="$SANDBOX" FUSION_PACKAGE_SPEC="$WHEEL" sh install.sh
          # remove leaves no trace
          HOME="$SANDBOX" "$BIN/fusion" setup --remove
          test ! -e "$SANDBOX/.agents/skills/fusion-intake"
          test ! -e "$SANDBOX/.claude/skills/fusion-intake"
      - name: Run install.ps1 against the local wheel (sandbox profile)
        if: runner.os == 'Windows'
        shell: pwsh
        run: |
          $sandbox = Join-Path $env:RUNNER_TEMP "fusion-sandbox"
          New-Item -ItemType Directory -Force -Path (Join-Path $sandbox ".claude") | Out-Null
          $env:HOME = $sandbox
          $env:USERPROFILE = $sandbox
          $env:FUSION_PACKAGE_SPEC = (Get-ChildItem dist\fusion_cli-*.whl).FullName
          .\install.ps1
          $bin = (uv tool dir --bin).Trim()
          & (Join-Path $bin "fusion.exe") --version
          if (-not (Test-Path (Join-Path $sandbox ".agents\skills\fusion-intake"))) { exit 1 }
          & (Join-Path $bin "fusion.exe") setup --remove
          if (Test-Path (Join-Path $sandbox ".agents\skills\fusion-intake")) { exit 1 }
```

Implementation notes for the e2e job: uv may key its tool dirs off
`UV_TOOL_DIR`/`XDG_DATA_HOME` rather than `HOME` alone — if the sandbox
assertions fail on tool location, set `UV_TOOL_DIR="$SANDBOX/uvtools"` and
`UV_TOOL_BIN_DIR="$SANDBOX/bin"` alongside `HOME` in every step of that
job and assert against those instead. The job must end green on all three
OSes; adjust mechanics, never assertions.

- [ ] **Step 2: Push-less verification**

Workflows can't run without pushing (this repo pushes only on the human's
word). Verify statically instead: `uv run --with yamllint yamllint -d relaxed .github/workflows/ci.yml` and re-run the local sandbox e2e from Task 5 step 3 one more time from a clean tree. Record in the task report that CI's first live run happens on the next authorized push, and its result must be checked then.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: three OSes prove the suites, shellcheck proves the script, e2e proves the one-liner"
```

### Task 8: Release pipeline + version + docs

**Files:**
- Create: `.github/workflows/release.yml`
- Modify: `cli/pyproject.toml` (version 1.0.0 → 1.1.0)
- Modify: `README.md` (quickstart → one-liners)
- Modify: `docs/GETTING-STARTED.md` (one line; manual alternative; leaving cleanly)

- [ ] **Step 1: release.yml**

```yaml
name: release
# One-time human setup (before first tag): create the PyPI project
# "fusion-cli" and register this repo + this workflow as a trusted
# publisher (https://docs.pypi.org/trusted-publishers/). No tokens stored.
on:
  push:
    tags: ["v*"]

jobs:
  check:
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - working-directory: cli
        run: uv run --group dev pytest -q
      - working-directory: cli
        run: uv run fusion check ../examples/crazy-ones

  publish:
    needs: check
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - name: Tag must equal pyproject version
        run: |
          V="$(grep -m1 '^version' cli/pyproject.toml | cut -d'"' -f2)"
          [ "v$V" = "${GITHUB_REF_NAME}" ] || { echo "tag ${GITHUB_REF_NAME} != v$V"; exit 1; }
      - name: Build (hook bundles the skills)
        working-directory: cli
        run: uv build --out-dir ../dist
      - name: Publish to PyPI (trusted publishing)
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          packages-dir: dist
```

- [ ] **Step 2: Version bump**

`cli/pyproject.toml`: `version = "1.0.0"` → `version = "1.1.0"`.

- [ ] **Step 3: README quickstart**

Replace the `## Get started` code block (currently clone + uv tool install + cp + fusion new + fusion today) with:

````markdown
```bash
curl -fsSL https://raw.githubusercontent.com/bluewaves-creations/fusion/main/install.sh | sh
```

Windows (preview):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/bluewaves-creations/fusion/main/install.ps1 | iex"
```

One line installs uv (which brings Python), the `fusion` CLI, and the
four skills into every agent on your machine that reads them. Then:

```bash
fusion new ~/buckets/personal --kind personal \
  --description "Home base: admin, health, house, money."
fusion today
```

Ten minutes, no wizard. The walkthrough:
[docs/GETTING-STARTED.md](docs/GETTING-STARTED.md).
````

- [ ] **Step 4: GETTING-STARTED**

- Replace `## Move one — the CLI` and `## Move two — the skills` with a single `## One line` section carrying both one-liners (same text as README, Windows marked preview), followed by `## The manual way` preserving the existing clone + `uv tool install ./fusion/cli` + `cp -r fusion/skills/fusion-* ~/.agents/skills/` flow verbatim as the alternative ("no script between you and the steps it runs").
- Add before `## Where to go next`:

```markdown
## Leaving cleanly

`fusion setup --remove` takes the skills back out of every agent it
installed into (it only removes what it can prove it created), then:
`uv tool uninstall fusion-cli`. Buckets are yours — nothing touches them.
```

- Troubleshooting section: add one bullet — `- The installer failed partway — every step prints the manual command it was running; finish by hand from there. The three steps are: install uv, `uv tool install fusion-cli`, `fusion setup`.`
- [ ] **Step 5: Verify + commit**

Run: `cd cli && uv run --group dev pytest -q` → 155 passed; fixture 0/0; links in modified docs resolve; `uv run --with yamllint yamllint -d relaxed .github/workflows/release.yml`.

```bash
git add .github/workflows/release.yml cli/pyproject.toml README.md docs/GETTING-STARTED.md
git commit -m "release: tag-to-PyPI trusted publishing; the README earns its one line (v1.1.0)"
```

---

## Acceptance (after all eight)

- Suites: CLI 155 (135 + 20 new), intake 77, librarian 22, fixture 0/0, card ×4 one hash.
- `shellcheck install.sh` clean; both workflows yamllint-clean.
- Local sandbox e2e (Task 5 step 3) passes fresh: install → four skills canonical + Claude links → idempotent re-run → `--remove` leaves no trace.
- On the next authorized push: watch the first live `ci` run on all three OSes — treat any red as a same-day friction (docs/dogfood/frictions.md).
- Human one-time steps queued (spec §9): PyPI trusted-publisher setup before tagging v1.1.0; real-Windows validation later lifts the "preview" label.

## Non-goals (from the spec, restated so nobody "helpfully" adds them)

No sudo path, no brew/winget packaging, no LibreOffice auto-install, no self-updater, no install.cmd, no branded domain, no checksum theater in the bootstraps (uv and PyPI already verify).
