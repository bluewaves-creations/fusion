# Fusion Installer — Design Specification

**Date:** 2026-07-10
**Status:** Approved design — pre-implementation
**Applies to:** fusion-cli ≥ 1.1.0, the skill family, and the repository's release process

---

## What this is

One line installs Fusion — the CLI, the four skills, into every agent that
can read them — on macOS, Linux, and Windows. Production grade: idempotent,
no sudo, honest errors, tested in CI on all three platforms, uninstallable.

The architecture is the Claude Code shape: **thin shell bootstraps, brain
in the binary.** The shell scripts only ensure uv and install the CLI; a
new `fusion setup` command does everything that requires logic — written
once in Python, identical on three OSes, tested with pytest.

Grounded in a survey of the uv, Claude Code, Goose, Ollama, Pi, and herdr
installers (2026-07-10): two scripts, never a polyglot; no sudo; env-var
parameterization; registry-based PATH on Windows (never `setx`); Windows
shipped native but labeled preview until proven (herdr precedent).

## Decisions already made (binding)

| Decision | Choice |
|---|---|
| CLI distribution | PyPI (`fusion-cli`, name verified free), trusted publishing via GitHub Actions |
| One-liner hosting | `raw.githubusercontent.com/bluewaves-creations/fusion/main/` |
| Windows depth | Native `install.ps1` + Windows CI, labeled **preview** in docs |
| Skills layout | Canonical copies in `~/.agents/skills/`, symlink fan-out to agents that need it, copy fallback on Windows |
| Python handling | None of ours — uv downloads a managed CPython when none satisfies `>=3.11`; the installer only ensures uv |

## Non-goals

- No LibreOffice auto-install — `fusion setup` detects `soffice` and prints
  one line of per-OS advice (brew/apt/winget). Installing a 500 MB suite is
  the human's call.
- No system-wide install mode, no sudo path, no package-manager
  distributions (brew/winget) — later phases if ever.
- No self-updater daemon. Upgrade = re-run the one-liner (or
  `uv tool upgrade fusion-cli && fusion setup`).
- No `install.cmd` for plain CMD (Claude Code ships one; PowerShell is the
  Windows default everywhere now).
- No branded domain yet — the raw URL works today; a domain can 301 to it
  later without changing anything.

---

## 1. The surface

README and GETTING-STARTED advertise exactly two lines:

```bash
curl -fsSL https://raw.githubusercontent.com/bluewaves-creations/fusion/main/install.sh | sh
```

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/bluewaves-creations/fusion/main/install.ps1 | iex"
```

Behavior contract, both scripts:

- **Idempotent**: a re-run upgrades the CLI (`uv tool install` handles
  reinstall) and re-runs `fusion setup`, which refreshes skills in place.
- **No sudo**: user-owned locations only. The scripts never elevate.
- **Non-interactive**: no prompts; everything decidable is decided,
  everything else is a printed next step.
- **Honest failure**: every failure path prints the manual command that
  would have run, so the user can always finish by hand.

Environment variables (both scripts + `fusion setup`):

| Var | Effect |
|---|---|
| `FUSION_VERSION` | Pin the CLI version: `uv tool install fusion-cli==$FUSION_VERSION` |
| `FUSION_PACKAGE_SPEC` | Override the package spec entirely (CI installs the locally built wheel; power users install `git+https://…#subdirectory=cli`) |
| `FUSION_SKILLS_DIR` | Canonical skills destination (default `~/.agents/skills`) |
| `FUSION_NO_AGENTS` | `1` = skip agent fan-out; canonical install only |
| `FUSION_NO_MODIFY_PATH` | `1` = never touch shell config; print instructions instead |

## 2. install.sh

POSIX sh (`#!/bin/sh`, `set -u`, shellcheck-clean). Target ≤ ~80 lines of
logic. Helpers: `say`/`warn`/`err`, color only when stderr is a TTY.
Downloader: `curl` primary, `wget` fallback; neither → err with the two
manual steps.

Steps:

1. **Ensure uv.** `command -v uv` — if absent, run Astral's official
   installer (`curl -fsSL https://astral.sh/uv/install.sh | sh`), then
   locate uv at `$HOME/.local/bin/uv` (its default) for the rest of this
   run without requiring a shell restart. Pass through
   `FUSION_NO_MODIFY_PATH=1` as `UV_NO_MODIFY_PATH=1`.
2. **Install the CLI.** `"$UV" tool install --force fusion-cli` (with
   `==$FUSION_VERSION` when pinned, or `$FUSION_PACKAGE_SPEC` verbatim when
   set). `--force` makes re-runs upgrades. PyPI wheel hashes are verified
   by uv itself — the script adds no checksum theater of its own.
3. **Hand off.** Resolve the tool bin dir via `"$UV" tool dir --bin` and
   exec `"$BIN/fusion" setup` — never rely on the current shell's PATH
   containing a binary installed seconds ago. All remaining output is
   `fusion setup`'s.

## 3. install.ps1

PowerShell ≥5, TLS 1.2. Same three steps, idiomatic PowerShell: ensure uv
via `irm https://astral.sh/uv/install.ps1 | iex` (uv's own installer edits
HKCU PATH via the registry + `WM_SETTINGCHANGE`; we never call `setx`),
`uv tool install --force fusion-cli`, invoke `fusion.exe setup` by absolute
path from `uv tool dir --bin`. Honors the same `FUSION_*` variables
(`$env:FUSION_VERSION` …).

Windows is labeled **preview** wherever the one-liner appears, until a real
user validates it end-to-end (CI proves it mechanically first).

## 4. `fusion setup` — the ninth command

New subcommand in `cli/src/fusion/setup.py`, wired like the others
(`--json` supported; exit 0 success / 1 failure envelope like every
command). NOT a SPEC change — SPEC.md never enumerates CLI commands. Doc
updates: `cli/README.md` ("The nine commands (there is no tenth)"), the
conventions card CLI crib ×4, `skills/README.md`.

### 4a. Skills payload — bundled in the wheel

- A hatchling **build hook** (`cli/hatch_build.py`, registered in
  `pyproject.toml`) copies `../skills/fusion-*/` into the wheel as
  `fusion/_skills/fusion-*/` at build time. Excluded: `tests/`,
  `__pycache__/`, `.pytest_cache/` inside each skill.
- The repo's `skills/` directory stays the single source of truth; the
  hook runs at every build, so the wheel can never drift.
- A CLI test builds the wheel (or inspects the hook's output) and asserts
  the bundled tree is byte-identical to `skills/fusion-*` minus exclusions
  — including the ×4 conventions-card identity.
- `fusion setup` locates the payload with
  `importlib.resources.files("fusion") / "_skills"`. Editable/dev installs
  without `_skills` fall back to the repo-relative `skills/` when present
  (dev convenience), else fail with a clear message.

### 4b. Canonical install

Copy each bundled `fusion-*` skill to `$FUSION_SKILLS_DIR/fusion-<name>/`
(default `~/.agents/skills/`), replacing existing `fusion-*` real
directories there (they are ours by name; delete-then-copy, no merge).
Exception: an existing `fusion-*` entry that is a **symlink** (someone
manages skills their own way, e.g. a link into their repo clone) is left
untouched with a warning; `--force` replaces it. Report the installed
version (from package metadata).

### 4c. Agent detection and fan-out

Data-driven registry in code — one row per agent:

| Agent | Detected by | Skills dir | Action |
|---|---|---|---|
| Claude Code | `~/.claude/` exists | `~/.claude/skills/` | link |
| Codex | `~/.codex/` exists | `~/.codex/skills/` | link |
| Pi | `~/.pi/` exists | `~/.pi/agent/skills/` | link |
| Cursor | `~/.cursor/` exists | reads `~/.agents/skills` | report only |
| Gemini CLI | `~/.gemini/` exists | reads `~/.agents/skills` | report only |
| opencode | `~/.config/opencode/` exists | reads `~/.agents/skills` | report only |
| Goose | `~/.config/goose/` exists | reads `~/.agents/skills` | report only |

- **link**: create `agent_dir/fusion-<name>` → symlink to the canonical
  copy, one per skill (never link the whole skills dir). Creating the
  agent's skills dir is fine when the agent dir itself exists.
- **report only**: agents documented to read the standard dir get NO link
  — linking would double-load the skill. They appear in the report as
  "reads ~/.agents/skills — nothing to do".
- Registry rows carry a `docs_url` so the report can cite why.

Collision policy at a link target:
- Already the right symlink → "up to date".
- A symlink elsewhere or a real directory → **left untouched**, warned,
  with the exact command to resolve; `--force` replaces it. The installer
  never destroys content it didn't create.
- On Windows (or wherever `os.symlink` raises): fall back to **copying**;
  the report says "copy (symlinks unavailable) — re-run setup after
  upgrades", and re-runs refresh copies whose source version differs.

### 4d. Environment checks (advice, not action)

- PATH: is the uv tool bin dir on PATH? If not and
  `FUSION_NO_MODIFY_PATH` unset, run `uv tool update-shell`; else print
  the export line.
- `git`: absent → one line ("buckets are git repos; install git").
- LibreOffice (`soffice`): absent → one line with the per-OS install hint
  (brew/apt/winget), noting only docx/pptx/legacy-office/html intake
  needs it.

### 4e. The report

Human mode: a short table — CLI version + location; canonical skills dir
+ version; per-agent row (linked / copied / reads-standard-dir / skipped
with reason); environment advice; then next steps (`fusion new …`, the
GETTING-STARTED URL). `--json`: the same as one object
(`{"ok": true, "cli": {...}, "skills": {...}, "agents": [...],
"advice": [...]}`).

### 4f. `fusion setup --remove`

Removes what setup created, attribution-checked: in agent dirs, a
`fusion-*` symlink is removed only if it points into the canonical dir; a
`fusion-*` real directory (Windows copy fallback) is removed only if its
content hash matches the bundled payload — anything modified or foreign
is warned about and left. Then the canonical `fusion-*` dirs are removed
under the same symlink exception as 4b. Prints the one manual closer:
`uv tool uninstall fusion-cli`. Documented in GETTING-STARTED under
"Leaving cleanly".

### Flags

`fusion setup [--json] [--force] [--remove] [--skills-dir PATH]
[--no-agents]` — env vars are the equivalent long-term settings; flags
win over env.

## 5. Packaging and release pipeline

Greenfield `.github/workflows/`:

- **ci.yml** — push/PR: matrix {ubuntu-latest, macos-latest,
  windows-latest} × (CLI suite incl. new setup/build-hook tests; intake +
  librarian suites on ubuntu/macos — they shell out to POSIX tools;
  fixture check 0/0). Plus: shellcheck on `install.sh`, and an
  **installer e2e job** per OS: build the wheel, run the real
  `install.sh`/`install.ps1` with `FUSION_PACKAGE_SPEC=<built wheel>`,
  assert `fusion --version` works from the tool bin dir, canonical skills
  present, a fake agent dir (`$HOME/.claude/`) got its links, re-run is
  idempotent, `--remove` leaves no trace.
- **release.yml** — on tag `v*`: full ci matrix must pass → build sdist +
  wheel (hook bundles skills) → publish to PyPI with
  `pypa/gh-action-pypi-publish` via **trusted publishing** (no stored
  token). One-time human step, documented in the workflow header comment:
  create the PyPI project `fusion-cli` and register the repo +
  `release.yml` as trusted publisher.
- Version bumps live in `cli/pyproject.toml`; tag `vX.Y.Z` must equal the
  pyproject version (release job asserts it). First release: **v1.1.0**
  (1.0.0 was never published).

## 6. Documentation changes

- `README.md` quickstart: the two one-liners replace the clone+cp block
  (clone flow moves to GETTING-STARTED as "the manual way"); Windows line
  carries "(preview)".
- `docs/GETTING-STARTED.md`: "two moves" become "one line"; manual
  install preserved as an alternative section; new "Leaving cleanly"
  (uninstall) block; troubleshooting gains "the installer failed at step
  N" guidance (each failure already prints its manual command).
- `cli/README.md`: Install section shows the one-liner + PyPI now-true
  `uv tool install fusion-cli`; command table gains `setup`; the "eight
  commands (there is no ninth)" joke becomes "nine commands (there is no
  tenth)".
- Conventions card ×4: CLI crib gains the `fusion setup` row
  (byte-identity preserved).
- `skills/README.md`: install section points at the one-liner first,
  `cp -r` second.
- `docs/README.md` table row for the installer isn't needed (install.sh
  lives at repo root, covered by README).

## 7. Testing strategy

- **Unit (pytest, runs on all three OSes)**: agent registry detection
  against a fake `$HOME`; canonical install (fresh/upgrade/refresh);
  symlink creation, collision policies, `--force`; Windows copy fallback
  (monkeypatched `os.symlink` raising); `--remove` inverse; `--json`
  envelope; PATH/tool-advice branches; payload resolution
  (importlib.resources + dev fallback).
- **Build hook test**: bundled tree byte-identical to `skills/fusion-*`
  minus exclusions; conventions card ×4 identity inside the wheel.
- **Shell**: `shellcheck` gate on install.sh; the e2e CI job (above) is
  the real test for both scripts — no bats/Pester layer.
- **Suites stay green at their counts** (CLI 135 + new, intake 77,
  librarian 22, fixture 0/0).

## 8. Security posture

- No sudo, no privileged writes, no PATH edits beyond uv's own guarded
  mechanisms + `uv tool update-shell`.
- Payload integrity is delegated to the channels that already verify:
  uv's installer (Astral's signed hosting), PyPI wheel hashes (uv
  verifies). The bootstrap scripts download nothing else.
- `fusion setup` writes only under `$HOME` (skills dirs + agent dirs),
  never follows a symlinked target outside them blindly on `--remove`
  (it removes only entries it can attribute to itself: symlinks pointing
  into the canonical dir, or copies matching the bundled version
  manifest).
- The scripts are committed at repo root — auditable at the same URL
  users curl.

## 9. Open items for the human (one-time)

1. Create the PyPI project + configure trusted publishing for
   `bluewaves-creations/fusion` / `release.yml`.
2. Validate the Windows one-liner on a real Windows machine once CI is
   green (lifts the "preview" label — a later doc change).
