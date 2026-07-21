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
2026-07-21 — adopted brownfield; spec seated C1–C3 (static gates) same day.
All advertised gates green (199 CLI tests, 87 intake, 22 librarian,
conformance 0/0, shellcheck, wheel). Red trials re-run at plan time:
ruff 0.15.22, mypy 2.3.0 — counts pinned in Gaps.

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
- [ ] 1.2 Type-clean (C2). Doc: mypy docs — "The mypy configuration file"
      (pyproject `[tool.mypy]`). Files: cli/pyproject.toml (add mypy +
      types-PyYAML to dev group); cli/src/fusion/checker.py:41 (union-attr
      on possibly-None before .strip()); cli/src/fusion/cli.py:95 (bool
      assigned to `list[str]`).
      Done: inside `cli/`, `uv run mypy src/fusion` exits 0; full gate
      run stays green.
- [ ] 1.3 Enforcement (C3). Doc: uv docs — "Using uv in GitHub Actions".
      Files: .github/workflows/ci.yml (static-checks step running the
      three commands from 1.1/1.2 via the dev group); AGENTS.md Lint/Types
      gate line rewritten to the `uv run` forms, advisory clause dropped.
      Done: `git push` then CI green on all 3 OSes with the new step;
      AGENTS.md gate line contains no "advisory".

## Gaps
- Lint red at adoption, re-confirmed at plan (2026-07-21): 8 ruff errors
  (3 E702, 1 E731, 3 E741, 1 F401), 32/35 files unformatted.
- Types red at adoption, re-confirmed: checker.py:41 union-attr,
  cli.py:95 bool→list[str], yaml stubs missing (document.py:8,
  scaffold.py:9).
- Skills suites depend on ad-hoc `--with` deps (no lockfile for skill
  tests) — works, unpinned. Not in Batch 1; raise at boundary if it bites.
