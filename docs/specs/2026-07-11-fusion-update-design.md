# fusion update — one command to bring the whole system current

2026-07-11 · target: v1.3.0

## Problem

Updating Fusion today is a two-step ritual the user must know by heart:
`uv tool upgrade fusion-cli`, then `fusion setup`. Forget the second step
and the installed skills go stale — silently, because most agents read
symlinks into `~/.agents/skills` but copy-fallback platforms (no
symlinks) keep old bytes forever. The system should update itself with
one verb.

## Command

    fusion update [--force] [--skills-dir DIR] [--no-agents]

1. **Find uv.** `shutil.which("uv")`, falling back to `~/.local/bin/uv`
   (where install.sh puts it). No uv → error with the manual path.
2. **Prove uv owns this install.** `uv tool list` must name
   `fusion-cli`. If it does not (pip/pipx/checkout install), error with
   guidance instead of guessing at someone else's package manager.
3. **Upgrade.** `uv tool upgrade fusion-cli`, stdio inherited — the
   user sees uv's own "Updated fusion-cli v1.2.1 -> v1.3.0" or
   "Nothing to upgrade". Non-zero exit → error; the message includes
   the Windows case (a running `fusion.exe` can hold a lock — exit
   this process, run `uv tool upgrade fusion-cli && fusion setup`).
4. **Re-exec setup from the NEW binary.** The running process still
   holds the old payload in memory, so setup must run in a child:
   `<uv tool dir --bin>/fusion setup`, forwarding `--force`,
   `--skills-dir`, `--no-agents`. `fusion update` returns that child's
   exit code. Setup already prints the new version and per-skill
   `up-to-date`/`updated` actions — no duplicate reporting.

`--json` is deliberately absent: the command is a composition of two
processes that own stdout in turn (uv's progress, then setup's report).
Agents that need machine output run the two steps themselves.

## Non-goals

- No self-update for non-uv installs (pip, pipx, a git checkout).
  The error message says exactly what to run instead.
- No version pinning/unpinning. A `fusion-cli==X` pin given at install
  time is respected by `uv tool upgrade`; upgrading past it is the
  user's decision, made with uv directly.
- No skills-only or CLI-only mode. `fusion setup` alone already covers
  skills-only.

## Module shape

`cli/src/fusion/update.py` — the brain, mirroring setup.py's contract:
every decision testable without a real subprocess.

    class UpdateError(Exception)
    find_uv(home) -> Path | None
    uv_owns_install(uv, run) -> bool          # parses `uv tool list`
    fusion_binary(uv, run) -> Path            # <tool bin dir>/fusion(.exe)
    run_update(home, setup_args, run) -> int  # orchestrates 1–4

`run` is an injectable `subprocess.run`-alike; tests pass a fake and
assert the exact command sequence. `cmd_update` in cli.py stays thin:
build `setup_args` from flags, call `run_update`, `_fail` on
`UpdateError`.

## Tests

`cli/tests/test_cli_update.py`, in the house style of
test_cli_setup.py (sandboxed home, no real subprocess ever):

- happy path: uv found → list shows fusion-cli → upgrade runs →
  child `fusion setup` invoked from the tool bin dir with forwarded
  flags → exit code is the child's
- no uv anywhere → exit 1, message names the manual steps
- uv present, fusion-cli not in `uv tool list` → exit 1, non-uv guidance
- `uv tool upgrade` fails → exit 1, message includes the retry ritual
- flags forwarded: `--force --skills-dir X --no-agents` all reach the
  child argv
- `fusion --help` lists update; `fusion update --help` describes it

## Release

Version 1.3.0 (new command = minor bump). Tag `v1.3.0` → the existing
release workflow publishes to PyPI via trusted publishing. Then this
machine upgrades for real: `uv tool upgrade fusion-cli && fusion setup`
once (the installed 1.2.1 has no `update` yet), and from then on
`fusion update` is the whole ritual.
