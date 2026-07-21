# Plan — Fusion

Adapts at every batch boundary. The spec never moves.
Goal: bring the reference implementation under full Craftsman gates.
Architecture: convention (root SPEC.md) + CLI (`cli/`, Python/uv, hatchling)
+ four skills (`skills/`). Constraints: pyyaml-only runtime dep; uv always;
`fusion check examples/crazy-ones` stays 0/0; CI 3-OS matrix stays green.

Files (Batch 1):
- ruff.toml (repo root) — the one lint/format config; ruff's per-file
  upward discovery is the only way one config governs cli/ AND skills/
- cli/pyproject.toml — dev group (ruff, mypy, types-PyYAML) + [tool.mypy]
- cli/src/fusion/{checker.py,cli.py} — the 2 real type fixes
- cli/src/**, cli/tests/**, skills/*/tests/** — mechanical lint/format sweep
- .github/workflows/ci.yml — new static-checks step
- AGENTS.md — gate line flips advisory → blocking

## State
Batch 1 closed 2026-07-21 (adopted brownfield + spec C1–C3 same day).
All C-ids ticked; CI run 29873877632 green on all 7 jobs. Next: finish,
or new work via specify.
- Decided: one root ruff.toml, not [tool.ruff] in cli/pyproject.toml —
  ruff's per-file upward discovery is the only way one config governs
  cli/ AND skills/ (docs.astral.sh/ruff/configuration).
- Decided: ci.yml static step pins `shell: bash` — pwsh only propagates
  the last command's exit code; red ruff would pass silently on Windows.
- Decided: [tool.mypy] files=["src/fusion"] kept although commands pass
  the path — it makes a bare `uv run mypy` work for contributors.
- Review (fresh-eyes subagent, 1d3d528..d7e4932): zero critical/important;
  sweep AST-verified semantics-preserving; minors seated in Gaps.

## Batch 1 — static gate remediation
- [x] 1.1 Lint-clean and formatted (C1). Doc: Ruff docs — "Configuring
      Ruff" (hierarchical discovery; pyproject without [tool.ruff] is
      ignored, so a root ruff.toml governs the repo) + rules E4/E7/F.
      Files: ruff.toml (create, repo root); cli/pyproject.toml (ruff into
      dev group via `uv add --group dev ruff`); fix 73 repo-wide errors —
      60×F811 fixture-import shadowing in skills/fusion-intake tests
      (drop `from conftest import` lines, pytest auto-discovers), 7×E702,
      3×E741, 1×E731, 1×E401, 1×F401; format the 43 drifted files.
      Done: from repo root, `uv run --project cli ruff check .` and
      `uv run --project cli ruff format --check .` exit 0 (covers cli/
      and skills/ — C1's letter, inside cli/, holds as a subset); full
      gate run stays green.
- [x] 1.2 Type-clean (C2). Doc: mypy docs — "The mypy configuration file"
      (pyproject `[tool.mypy]`). Files: cli/pyproject.toml (add mypy +
      types-PyYAML to dev group); cli/src/fusion/checker.py:41 (union-attr
      on possibly-None before .strip()); cli/src/fusion/cli.py:95 (bool
      assigned to `list[str]`).
      Done: inside `cli/`, `uv run mypy src/fusion` exits 0; full gate
      run stays green.
- [x] 1.3 Enforcement (C3). Doc: uv docs — "Using uv in GitHub Actions".
      Files: .github/workflows/ci.yml (static-checks step running the
      three commands from 1.1/1.2 via the dev group); AGENTS.md Lint/Types
      gate line rewritten to the `uv run` forms, advisory clause dropped.
      Done: `git push` then CI green on all 3 OSes with the new step;
      AGENTS.md gate line contains no "advisory".

## Gaps
Disposed at finish (2026-07-21): CI now triggers on every push (human:
personal main-first system, no branch/PR ceremony) · mypy strict = true,
77 fallout errors annotated (human: fix now). Remaining:
- Skills suites depend on ad-hoc `--with` deps (no lockfile for skill
  tests) — human accepted as-is at finish; risk recorded in ADR.md
  adoption entry. Raise if it bites.
