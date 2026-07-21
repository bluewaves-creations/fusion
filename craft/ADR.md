# Decisions — Fusion (Craftsman)

Read before re-litigating anything. Newest first.

## 2026-07-21 — Batch 1 finished: static gates live and blocking
Context: craft C1–C3 remediated and finished the same day as adoption.

Decisions:
- One root ruff.toml, not [tool.ruff] in cli/pyproject.toml — ruff's
  per-file upward config discovery is the only way one config governs
  cli/ AND skills/. Rejected: per-package configs (style drift).
- mypy `strict = true` (human: fix now, at finish) — 77 fallout errors
  annotated. Liberal-reader frontmatter accessors return `Any` on
  purpose: frontmatter values are untyped by design (SPEC §0); the
  strictness lives at the boundaries, not in pretend value types.
- ci.yml triggers on every push, no branch filter (human: Fusion is a
  personal system, no branch/PR ceremony). Static-checks step pins
  `shell: bash` — pwsh only propagates the last command's exit code.
- Skills suites' unpinned `--with` deps: human accepted as-is at
  finish; revisit only if a resolution ever bites.
- Batch 2 (extended review, accepted in full): canonical skill installs
  now carry the `.fusion-setup` sentinel, and setup/remove only destroy
  what the sentinel (or a payload-identical digest) can vouch for.
  Transition: canonical dirs installed by ≤ 1.4.1 have no sentinel — the
  first post-upgrade `fusion setup` reports them "left … --force
  replaces"; one `fusion setup --force` adopts them. Accepted over
  silently overwriting possibly-user-modified content.

## 2026-07-21 — State of the system at Craftsman adoption
Context: `init craftsman` on the existing v1.4.1 tree (clean main, released
to PyPI, phase 4 dogfood in progress).

Verified (ran on this machine, 2026-07-21):
- CLI suite 198 passed (`cd cli && uv run --group dev pytest -q`).
- `fusion check examples/crazy-ones` — 0 errors, 0 warnings.
- Intake skill suite 87 passed; librarian suite 22 passed.
- `shellcheck install.sh` clean; `uv build --wheel` builds 1.4.1.
- ruff: 8 errors + 31/34 files unformatted. mypy: 4 errors (2 real).

Decisions:
- Craftsman ledgers live in `craft/` — root SPEC.md is the Fusion
  Convention, the product itself; it can never double as a work ledger.
  Rejected: renaming the product spec (linked everywhere: README,
  CONTRIBUTING, installer docs, external consumers).
- Lint/type gap: remediate (ruff + mypy, PLAN Batch 1), not accept.
  Human's call. Gate is advisory until Batch 1 lands, then blocking.
- Toolchain (standing, human-attested): always uv for Python, always bun
  for JS/TS. Never pip/pipx/poetry/npm/yarn/pnpm.

Inferred (not in AGENTS.md, verify before relying on):
- Prior workflow artifacts (`docs/plans/`, `docs/specs/`, `docs/acceptance/`,
  `.superpowers/sdd/`) are history from the pre-Craftsman flow; new work
  routes through craft/ ledgers. Dogfood protocol (docs/dogfood/) continues
  unchanged alongside.
- Skills tests' `--with` deps mirror ci.yml exactly; drift there would
  break the local/CI equivalence silently.
