# Plan — Fusion

Adapts at every batch boundary. The spec never moves.
Goal: bring the reference implementation under full Craftsman gates.
Architecture: convention (root SPEC.md) + CLI (`cli/`, Python/uv, hatchling)
+ four skills (`skills/`). Constraints: pyyaml-only runtime dep; uv always;
`fusion check examples/crazy-ones` stays 0/0.

## State
2026-07-21 — adopted brownfield. All advertised gates green (198 CLI tests,
87 intake, 22 librarian, conformance 0/0, shellcheck, wheel). Lint/type gate
absent; human chose remediation (ruff + mypy) over acceptance.

## Batch 1 — static gate remediation
- [ ] 1.1 Wire ruff (lint + format) into `cli/pyproject.toml` dev group +
      config; fix the 8 lint errors; format the 31 unformatted files.
      Files: cli/pyproject.toml, cli/src/**, cli/tests/**, skills/**/tests.
      Done: `uv run ruff check` and `uv run ruff format --check` exit 0.
- [ ] 1.2 Wire mypy (+ types-PyYAML) into dev group; fix the 2 real type
      errors. Files: cli/pyproject.toml, cli/src/fusion/checker.py,
      cli/src/fusion/cli.py. Done: `uv run mypy src/fusion` exits 0.
- [ ] 1.3 Add both to `.github/workflows/ci.yml`; flip the AGENTS.md
      Lint/Types gate from advisory to blocking.
      Done: CI green on all 3 OSes with the new steps.

## Gaps
- Lint red at adoption: 8 ruff errors, 31 files unformatted (`uvx ruff
  check cli`, 2026-07-21).
- Types red at adoption: `checker.py:41` union-attr on possibly-None,
  `cli.py:95` bool assigned to `list[str]`; yaml stubs missing.
- Skills suites depend on ad-hoc `--with` deps (no lockfile for skill
  tests) — works, unpinned.
