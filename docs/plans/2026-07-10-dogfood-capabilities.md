# Dogfood Capabilities Implementation Plan — frictions 5–7

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn what the 2026-07-10 delivery taught us into Fusion capabilities: a gate that stays fast on large binary batches, containers that unpack where they live, manifest-driven batch intake, and a librarian link-repair sweep — each exactly as proven live, now with tests.

**Architecture:** All changes live in the self-contained skills (`skills/fusion-intake`, `skills/fusion-librarian`). No CLI changes, no SPEC changes. The intake scripts gain performance guards and a `batch` subcommand; the librarian gains its first script (`link-repair.py`) implementing the propose→approve→apply sweep run by hand today.

**Tech Stack:** Python ≥3.11, PEP 723, stdlib-first (gate.py stays stdlib-only), pytest.

## Global Constraints

1. Work on `main`, one commit per task, never push, never touch `examples/crazy-ones` or `references/fusion-conventions.md` (byte-identity ×4 enforced).
2. Suites before → after: intake 57 → grows; CLI 125 stays; `fusion check examples/crazy-ones` 0/0 after every task.
3. Single-writer contracts hold: scripts never write LEDGER/INDEX; MANIFEST only via convert.py's existing writers.
4. Locked constants stay locked (0.85 / 0.30 / 3 / 100 / 150). New constants get the same literal-pinning treatment in tests.
5. Behavior proven live today is the spec: the a-mua/engagements repairs and the .athena batch are the acceptance shapes.
6. TDD per task; every new behavior mutation-testable (a reverted hunk must fail a test).

---

### Task 1: The gate stays fast — similarity reads capped, binaries skip the scan

**Files:** `skills/fusion-intake/scripts/gate.py` · `skills/fusion-intake/tests/test_gate.py`

Friction 5: `classify_intake` decoded every byte of every file (144MB batch → >2min). Two guards, both semantic no-ops for real matching:

- [ ] New constant beside the locked ones (documented as a guard, not a lineage threshold): `SIMILARITY_READ_CAP = 512 * 1024  # bytes of text considered for similarity — enough to catch any real re-export/update`.
- [ ] `extract_text(path)` reads at most `SIMILARITY_READ_CAP` bytes (`path.open("rb").read(SIMILARITY_READ_CAP)` then decode as today).
- [ ] In `classify_intake`, compute the incoming file's shingles ONCE; if the set is empty (binary/no-words), skip `_best_match` entirely — hash matching already ran, and empty shingles can never score above 0.0. Pass precomputed shingles into the best-match path so each source is shingled at most once per run (cache `idx` shingles on first use in a dict).
- [ ] Tests: (a) literal pin `gate.SIMILARITY_READ_CAP == 524288`; (b) a >cap text file still classifies as near-dup of its own re-export (first-cap-bytes identical); (c) a binary incoming with 200 sources present classifies clean_new and `_best_match` is not called (monkeypatch a counter on `gate.similarity`); (d) existing 0.444/0.93 similarity-band tests still pass untouched.

Commit: `fusion-intake: the gate reads enough, not everything — capped similarity, binaries skip the scan (friction 5)`

### Task 2: Containers unpack beside their parent

**Files:** `skills/fusion-intake/scripts/convert.py` (`unpack`) · `skills/fusion-intake/tests/test_convert.py` · `skills/fusion-intake/references/gate.md` (one line)

Friction 6: dest was always `inbox/<stem>`; a nested container lost its folder context.

- [ ] Dest becomes sibling: `dest = src.parent / src.stem` (still inside inbox/ by construction since src is validated under inbox/). Existing refusals (dest exists, zip-slip) unchanged.
- [ ] Tests: nested container at `inbox/delivery/assets/inner.zip` unpacks to `inbox/delivery/assets/inner/`; top-level behavior unchanged (`inbox/x.zip` → `inbox/x/`). Update any test pinning the old root dest.
- [ ] gate.md: the containers paragraph notes members land beside the container.

Commit: `fusion-intake: containers unpack where they live — nested vehicles keep their context (friction 6)`

### Task 3: Manifest-driven batch intake — `convert.py batch`

**Files:** `skills/fusion-intake/scripts/convert.py` · new `skills/fusion-intake/references/delivery.md` · `skills/fusion-intake/tests/test_convert.py` · `skills/fusion-intake/SKILL.md` (pipeline note)

Friction 7a: 122 sequential subprocess calls. One `batch` subcommand executes a JSON op-list in a single process, validating everything before touching anything (the gate's validation-before-damage rule, batch-scale).

- [ ] CLI: `batch --bucket <root> --ops <ops.json> [--actor claude]`. Schema (documented in delivery.md):

```json
{"admits": [{"file": "<inbox-rel>", "category": "<cat>"}],
 "links":  [{"source": "<sources-rel>", "doc": "<zone-rel-doc>"}]}
```

- [ ] Two phases. VALIDATE: every admit file exists in inbox with a supported ext, every (category,basename) unique among admits AND against existing sources rows, every link doc path is zone-relative to an existing file OR one of this batch's declared docs, actor token valid — any failure aborts with IntakeError before ANY move. EXECUTE: run admits (reusing `admit()`), then links (reusing `link` internals). Output JSON `{"admitted": n, "linked": m}`.
- [ ] Conversion stays the operator's judgment (Stage 2) — batch handles the mechanical halves only. delivery.md documents the full proven protocol: unpack → dedupe (hash sweep) → per-folder categories on basename collision → notes convert with lifted summaries → batch links from the package manifest → close (ledger `converted` per document) → archive pass when the delivery's intent says so.
- [ ] Tests: happy path (2 admits + 2 links in one call, MANIFEST rows + library columns correct); validation-before-damage (one bad admit in a 3-op batch → nothing moved, nothing appended); link to a doc declared in the same batch's admits-then-converted flow (pre-created file) works.

Commit: `fusion-intake: deliveries are one batch, not a hundred calls — validate everything, then move (friction 7)`

### Task 4: The librarian learns link repair — propose, approve, apply

**Files:** new `skills/fusion-librarian/scripts/link-repair.py` · new `skills/fusion-librarian/tests/` (conftest + test_link_repair.py, self-contained like intake's) · `skills/fusion-librarian/references/cross-reference.md` (repair-sweep section)

Friction 7b: today's 67 rewrites ran as a hand script. Productize the exact pattern — with the human gate in the middle.

- [ ] `link-repair.py scan --bucket <root>` (stdlib + PyYAML via PEP 723): walk documents in `library/` and `activities/` (skip dot-dirs), extract relative links (`\]\(([^)#][^)]*)\)`, skip http/https/mailto/#), test existence from the doc's dir; for each broken link, propose candidates: exact basename match anywhere under `sources/` or the doc zones (unique match → `confidence: exact`; unique match after lowercase/hyphen-insensitive normalization → `confidence: fuzzy`; else `unrepairable`). Emit JSON to stdout: `{"proposals": [{"doc", "link", "target", "confidence"} …], "unrepairable": […]}` — and a human-readable table on stderr.
- [ ] `link-repair.py apply --bucket <root> --proposals <file.json>`: rewrite ONLY the pairs in the file (relative path computed from each doc's dir via `os.path.relpath`), bump `updated:` (add or replace, today's date) on changed docs, print count. The script writes NO ledger entry — the gear's protocol has the operator sign one `noted` for the pass and re-run `fusion index`/`check`.
- [ ] cross-reference.md gains the sweep protocol: scan → show the human the table (exact vs fuzzy separated; fuzzy requires explicit yes per group) → apply approved subset → `noted` → index → check.
- [ ] Tests (self-contained scratch bucket, no CLI dependency, mirror intake's conftest pattern): scan finds a broken `assets/x.pdf` with the real file under `sources/cat/x.pdf` and proposes the correct `../../sources/cat/x.pdf` (exact); a normalized match (`amua-map.png` vs `a-mua-map.png`) is `fuzzy`, never auto-exact; apply rewrites only listed pairs, bumps `updated:`, leaves other links untouched; a link whose basename matches TWO files is unrepairable (never guess); http/anchor links ignored.
- [ ] `cd cli && uv run --group dev pytest tests/test_skill_family.py -q` still green (librarian gains scripts/tests dirs — confirm the structure gate accepts them as intake's equivalents are accepted).

Commit: `fusion-librarian: broken links get a sweep — scan proposes, the human approves, apply signs off (friction 7)`

---

## Acceptance (after all four)

- Intake suite green (expect ~70), CLI 125, fixture 0/0.
- Live re-proof on real buckets, read-only or reversible only: `gate.py --bucket ~/buckets/bluewaves` completes in seconds (146MB of sources present); `link-repair.py scan --bucket ~/buckets/bluewaves` proposes nothing for the 54+13 already-repaired links and lists exactly the 7 known unrepairables.
- Frictions 5–7 dispositions updated with commit hashes.
