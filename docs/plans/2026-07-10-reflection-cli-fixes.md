# Reflection CLI Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix what the first reflection cycles surfaced in the CLI and the librarian scanner: link scanning must ignore code (fences and inline spans), unexpected CLI failures must honor `--json`, and one E7 message must stop lying about invisible files.

**Architecture:** Two tasks. Task 1 touches the CLI (`document._links`, `cli.main` dispatch, one checker message). Task 2 gives the librarian's link-repair scanner the same code-blindness. No SPEC changes — W4's definition ("broken relative links between documents") is unchanged; links inside code were never links.

**Tech Stack:** as the repo stands (Python ≥3.11, pytest; suites at CLI 125 / intake 77 / librarian 17).

## Global Constraints

Same as docs/plans/2026-07-10-dogfood-capabilities.md (main, one commit per task, never push, fixture byte-frozen at 0/0, golden INDEX identity holds, cards ×4 identical, single-writer intact, TDD, mutation-testable).

Live acceptance shape (the reflections' evidence): after Task 1, `fusion check ~/buckets/bluewaves` must report exactly **4** W4 warnings (the never-shipped dossier files) — the 3 template placeholders (`assets/x`, `assets/x.png`, `assets/x.pdf` inside fenced examples in decision-log/grooming-spec/grooming-worklist) disappear. READ-ONLY on real buckets.

---

### Task 1: The CLI stops reading code as prose

**Files:** `cli/src/fusion/document.py` (`_links`) · `cli/src/fusion/cli.py` (`main`) · `cli/src/fusion/checker.py` (E7 message) · tests: `cli/tests/test_document.py`, `cli/tests/test_cli.py`, `cli/tests/test_checker_errors.py`

- [ ] **_links skips code.** Before extracting links in `_links(body)`, blank out (a) fenced blocks — lines from a ` ``` `/`~~~` opener to its closer inclusive — and (b) inline code spans (`` `...` `` on one line, non-greedy). Replace them with equal-length whitespace or drop them; the remaining text feeds the existing `_LINK_RE`. Document.links semantics elsewhere unchanged.
- [ ] Tests: a body whose only `](broken.md)` sits inside a fenced block yields `links == []`; inline span `` `[x](gone.md)` `` ignored; a real link BETWEEN two fences is still found; an unterminated fence swallows to EOF (liberal: better silent than false-positive).
- [ ] **Unexpected exceptions honor --json.** In `main` (cli.py), wrap the dispatched `args.func(args)` call: on any unhandled `Exception` (not SystemExit), print the `_fail`-style envelope — `{"ok": false, "error": "unexpected: <ExcName>: <msg>"}` to stdout when `--json` was passed, else `fusion: unexpected: …` to stderr — and exit 1. argparse's own exit-2 behavior stays untouched.
- [ ] Test: monkeypatch a command handler to raise `RuntimeError("boom")`; `main([cmd, "--json"])` returns 1 with a parseable envelope; without `--json`, stderr text.
- [ ] **E7 message tells the truth.** The "manifest row's file is gone" finding becomes "manifest row's file is missing or invisible (dot-directories are not scanned): <rel>". Update its test's expected text.
- [ ] Suite green (128+); fixture 0/0; golden INDEX identity (the fixture has no code-fenced links — verify the golden tests still pass untouched).
- [ ] Commit: `cli: code is not prose — link scan skips fences and spans, surprises speak JSON, E7 says invisible`

### Task 2: The librarian scanner gets the same code-blindness

**Files:** `skills/fusion-librarian/scripts/link-repair.py` · `skills/fusion-librarian/tests/test_link_repair.py`

- [ ] Port the same fence/inline-span blanking to the scanner's link extraction (keep implementations independent — the skill stays self-contained — but semantically identical; note the CLI twin in a comment).
- [ ] Tests: fenced `](assets/x.pdf)` produces NO unrepairable entry and NO proposal even when a real `x.pdf` exists somewhere (the reviewer's named risk: a real file with a placeholder basename must no longer be proposable from code text); real broken link outside the fence still proposed.
- [ ] Librarian suite green (19+); intake 77; CLI unchanged from Task 1's count; fixture 0/0.
- [ ] Commit: `fusion-librarian: the scanner learns what the checker learned — code is not prose`

---

## Acceptance

- Live read-only: `fusion check ~/buckets/bluewaves` → exactly 4 W4 (the never-shipped files); `link-repair.py scan --bucket ~/buckets/bluewaves` → 4 unrepairables, 0 proposals.
- Record the outcome in docs/dogfood/frictions.md as row 8 (fixed-on-arrival) and in the progress ledger.
