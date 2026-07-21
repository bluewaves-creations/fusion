# Spec — Fusion (Craftsman work ledger)

Status: frozen 2026-07-21
Frozen at approval. The agent drafts and refines; every alteration needs
human validation. Verify ticks the boxes.

Not the product spec — that is the Fusion Convention at the repo root
(`../SPEC.md`). Recovered behavior enters here through specify, one area
at a time, as it is touched.

## Static gates — adoption remediation
Human disposition at adoption (2026-07-21): remediate the missing
lint/type gate with ruff + mypy, then make it blocking.

- [ ] C1 The CLI codebase is lint-clean and uniformly formatted: inside
      `cli/`, `uv run ruff check` and `uv run ruff format --check` both
      exit 0. Edge: skills test suites (`skills/*/tests`) are covered by
      the same check — one style across the repo.
- [ ] C2 The CLI source is type-clean: inside `cli/`, `uv run mypy
      src/fusion` exits 0 — no missing-stub errors, no real type errors.
- [ ] C3 The static checks are enforced, not advisory: CI runs lint,
      format, and type checks on every push and pull request, and the
      AGENTS.md Lint/Types gate reads blocking. Edge: a contributor
      without ruff or mypy installed gets the same result via uv-managed
      dev dependencies — no global installs.

## Deferred — open questions
(none)
