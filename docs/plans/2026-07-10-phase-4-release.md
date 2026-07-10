# Phase 4 — Dogfood + Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Fusion releasable and livable — fix the deferred defects that would bite real daily use, close the open-source gate item (install proven, README truthful, docs a newcomer can follow), settle the SPEC's open vocabulary with the human, and hand the system a written protocol for its dogfood week.

**Architecture:** Two parts. **Part A** (Tasks 1–9, SDD-executable now): a hardening wave over the CLI and fusion-intake driven by the Phase 2+3 deferred list, a `--help`/README/getting-started documentation wave, one human-gated SPEC vocabulary amendment, and an install-from-clean-machine acceptance transcript. **Part B** (after the final review, live with the human): bootstrap the two real buckets, live a real week, run one reflection cycle per bucket — the three calendar-bound gate boxes close on that evidence, not in this plan.

**Tech Stack:** Python ≥3.11 · `uv` (CLI under `cli/` with hatchling; intake scripts PEP 723) · pytest · LibreOffice for the docx route · the Phase-2/3 conventions unchanged.

## Global Constraints

1. Work on `main`, linear history, **one commit per task**, **never push** — pushing is the human's act.
2. **No personal filesystem paths** in any committed file (`/Users/…` never appears; test-enforced for `skills/`). The fictional actor name `bertrand` in SPEC §6 and the fixture ledger is a pending human decision (Task 6) — do not change it outside that task.
3. `examples/crazy-ones/` is **normative and byte-frozen**. No task may modify it except Task 6, and only for the option the human explicitly approves there.
4. Any live `fusion` invocation in tests or acceptance runs **sandboxes the hub**: `FUSION_HUB=/tmp/<scratch>/hub.md` (there is no `--no-register` flag; `fusion new` always registers). The real `~/.fusion/hub.md` is never touched by this plan.
5. CLI suite: `cd cli && uv run --group dev pytest -q` — **111 green before this plan**; the count only grows.
6. Intake suite: `uv run --with pytest --with pyyaml --with openpyxl --with pymupdf pytest skills/fusion-intake/tests -q` (from repo root) — **34 green before this plan**; the count only grows.
7. `uv run --project cli fusion check examples/crazy-ones` stays **0 errors / 0 warnings**, and the golden INDEX byte-identity tests keep passing, after every task.
8. `references/fusion-conventions.md` is **byte-identical across all four skills** (test-enforced). Any card edit is four identical edits in the same commit.
9. **SPEC.md changes only through Task 6**, each individually approved by the human via AskUserQuestion. Pre-release: amend in place, no version bump (Phase 3 precedent, commit e684749).
10. License MIT, copyright **Bluewaves Boutique** — never a personal name.
11. **Documentation excellence** (standing human directive): a task that ships behavior ships its documentation in the same commit; every doc claim must be verifiable against the tree (truthful links, current status tables); judge newcomer-facing text by a cold read.
12. Locked lineage constants stay locked: `NEAR_DUP_THRESHOLD = 0.85`, `UPDATE_SIM_FLOOR = 0.30`, `SHINGLE_K = 3`, `TEXT_COVERAGE_MIN_CHARS = 100`, `RENDER_DPI = 150`.
13. `gate.py` stays stdlib-only. `convert.py` may use its declared PEP 723 deps (PyYAML, openpyxl, pymupdf) plus stdlib; `html.parser` is stdlib.
14. Single-writer contracts hold: `LEDGER.md` ← `fusion log` only; `INDEX.md` ← `fusion index` only; `sources/MANIFEST.md` ← intake's `convert.py` only.

---

## Research facts (verified 2026-07-10 against HEAD f0f6e1a)

These were established by direct code reading and live probes before planning. Task steps cite them; implementers need not re-derive them.

- **CRLF is a non-issue** in all four CLI readers (`document`, `ledger`, `hub`, `manifest`): every reader uses `Path.read_text(encoding="utf-8")`, so Python's universal-newline translation converts `\r\n` before parsing. Verified by live round-trip. We lock this with a regression test but change no reader for CRLF.
- **UTF-8 BOM is a real bug in `document.py` only**: `read_document` decodes with `"utf-8"` (which keeps `﻿`), then `split_frontmatter`'s `text.startswith("---\n")` fails → the whole frontmatter is silently discarded (`fm_error = "no frontmatter block"`). `ledger`/`hub`/`manifest` tolerate BOM because their first line is a heading no regex anchors on.
- **Dot-directories are fully visible**: `bucket.iter_documents`, `indexer._zone_documents`, `checker._e7_manifest`, `checker._e8_filenames` all exempt only leaf names starting with `.`, never path components. Live probe: `library/.trash/Weird Name.md` produces E8; `sources/.trash/junk file.pdf` produces E7.
- **Blank-string aurora double-reports**: `aurora: ""` fires E3 (blank required field) *and* E4 (`"" is not None` passes the guard). YAML-null `aurora:` correctly fires E3 only.
- **`_fail` ignores `--json` at all 12 call sites** (cli.py lines 51, 68, 72, 77, 83, 99, 108, 114, 123, 138, 171): plain text to stderr even under `--json`. The single exception is `cmd_check`'s findings path, which never goes through `_fail`. Also `cmd_check`'s no-root message ("no bucket here and no path given") is wrong when a path *was* given but doesn't exist.
- **`today()`/`agenda()` exclude archive by path only** (`"archive" in rel.parts`); a document carrying `aurora: archive` outside an `archive/` path still composes into the morning.
- **gate.py `similarity()` returns 1.0 when both shingle sets are empty** — two binary files (zero `\w+` tokens after `errors="ignore"` decode) score a perfect match and land in `near_dups` at reported similarity 1.0. Exact duplicates are caught upstream by sha256, so the both-empty→1.0 branch only ever produces noise.
- **gate.py `git_history()`** catches only `FileNotFoundError`/`TimeoutExpired`; `check=` is not set so `CalledProcessError` can't happen, but a `PermissionError`/`NotADirectoryError` on `cwd` propagates and crashes the gate.
- **convert.py xlsx** never touches `ws.merged_cells.ranges`: openpyxl yields `None` for every non-anchor cell of a merge, so merged values survive only in the anchor cell and merge-spanned rows/columns can be pruned as "empty".
- **convert.py eml** strips html with `re.sub(r"<[^>]+>", " ", content)`: entities stay encoded (`&amp;` renders literally), `<script>`/`<style>` *content* survives, and attachment basenames can silently overwrite each other in the run dir on name collision.
- **The docx fixture cannot force >1 page**; the multi-page path (LibreOffice → PDF → all pages probed and rendered) is only asserted at `page_count >= 1`.
- **W5 is disabled below two reflections** — and SPEC §11 item 5 says so explicitly ("Buckets with fewer than two reflections never trigger this warning"), so changing it is a SPEC amendment (Task 6), not a code fix.
- **SPEC §4 has no `due` field** at all, while `views.agenda()` reads `fm.get("due") or fm.get("date")` and the commitments aurora is defined by "obligations, promises, deadlines". `resource` is defined as "URI of an external thing this document describes", while the amended conventions card and fusion-analyst's export gear point it at in-bucket artifacts too.
- **Install already works from a clean slate**: `uv pip install ./cli` into an isolated venv succeeds (hatchling, `fusion-cli==1.0.0`, sole dep pyyaml); `fusion --help` and `fusion check examples/crazy-ones` pass from that venv. **PyPI: `fusion` is taken by an unrelated project; `fusion-cli` is free** — matching `cli/pyproject.toml`.
- **README's "OKF" link is mislabeled**: it points at the real, active `GoogleCloudPlatform/knowledge-catalog` repo, which never calls itself OKF; the acronym exists only in our design spec.
- **`--help` is thin everywhere**: no subcommand has a `description`, no positional argument has help text, `fusion log`'s no-arg read mode is undocumented in the tool itself.
- **No getting-started path exists**: no quickstart/tutorial anywhere; `examples/crazy-ones` has no tour; the day-one sequence (install → new → hub → intake → today) is never stitched together.
- **Personal-path sweep is clean**: zero real filesystem paths anywhere; every `bertrand` hit is the fictional example actor (SPEC §6 line 230, fixture ledger, mirrored test data); every `/Users/` hit is a test assertion *looking for* the pattern.

## Deferred-item triage

| Deferred item (source) | Disposition |
|---|---|
| CRLF tolerance (P2 final) | **Non-issue, verified** — lock with regression test, Task 1 |
| UTF-8 BOM (found while verifying CRLF) | **Fix**, Task 1 |
| Dot-directory gaps E7/E8/iter_documents (P2 T4/T6) | **Fix**, Task 1 |
| Blank-aurora E3+E4 double-report (P2 T6) | **Fix**, Task 1 |
| No-JSON-on-failure convention (P2 final) | **Fix**, Task 2 |
| today/agenda archive-aurora leak (P2 T9 minor) | **Fix**, Task 2 |
| gate similarity empty-shingle ==1.0 (P3 T2) | **Fix**, Task 3 |
| gate git_history exception breadth (P3 T2) | **Fix**, Task 3 |
| Merged-cell xlsx (P3 T3) | **Fix**, Task 4 |
| html-only eml (P3 T3) | **Fix**, Task 4 |
| Multi-page docx untested (P3 T3) | **Fix (test)**, Task 4 |
| CLI `--help` thinness + `log` read mode undocumented (P3 T5 friction 1) | **Fix**, Task 5 |
| W5 two-reflection floor (P3 T7) | **Human decision**, Task 6 |
| SPEC `due:` vocabulary (P3 T8) | **Human decision**, Task 6 |
| SPEC `resource:` wording (P3 T9) | **Human decision**, Task 6 |
| `bertrand` example actor (P1 final, M3 "user taste") | **Human decision**, Task 6 |
| `_LINK_RE` image-syntax + `)` -in-target (P2 T2) | **Wontfix v1**: an unescaped `)` in a bare link target is invalid CommonMark anyway, and a broken image reference *is* a broken link — W4 flagging it is correct. Recorded here as the decision. |
| Hub display-name dedup in `today()` (P2 T9) | **Wontfix v1**: `hub add` already refuses duplicate registered names; colliding display names require hand-editing two BUCKET.md files into contradiction — liberal reader shows both, checker territory later if real use ever hits it. |
| MANIFEST header literal match (P2 T4) | **Wontfix v1**: single-writer zone — the only writer (`convert.py`) emits exactly the canonical header; the liberal reader skips what doesn't match. |
| `fusion log --bucket` vs positional path (P3 T5 friction) | **Wontfix structurally** (verb/object already occupy the positionals; changing shape breaks the skills' documented invocations); the friction is treated as a documentation defect — Task 5 makes `--help` and cli/README say it plainly. |
| Promote CLI backstop (P3 T7) | **Wontfix v1**: workbench is ruleless by design (SPEC §2); the librarian gear's STOP is the guard, and the checker takes over the moment the file lands in library/. |
| Mail-attachment default disposition (P3 T5 friction) | **Already documented** in gate.md's Stage-2 protocol (attachments surfaced to the agent's judgment); collision-safety fixed in Task 4. |

---

### Task 1: CLI readers and checks harden — BOM, dot-directories, one finding per defect

**Files:**
- Modify: `cli/src/fusion/document.py` (one line in `read_document`)
- Modify: `cli/src/fusion/bucket.py` (`iter_documents`)
- Modify: `cli/src/fusion/indexer.py` (`_zone_documents`)
- Modify: `cli/src/fusion/checker.py` (`_e7_manifest`, `_e8_filenames`, `_e3_e4_e5_documents`)
- Test: `cli/tests/test_document.py`, `cli/tests/test_checker_errors.py`, `cli/tests/test_hub_bucket.py`

**Interfaces:**
- Consumes: existing `read_document`, `iter_documents`, `check` — signatures unchanged.
- Produces: the rule every later task may rely on: **any path component starting with `.` makes a file invisible to Fusion** (documents, E7, E8, INDEX), matching the existing leaf-dotfile behavior; `read_document` tolerates a UTF-8 BOM.

- [ ] **Step 1: Write the failing tests**

In `cli/tests/test_document.py` (append; use the existing imports of that file — it already imports `read_document`):

```python
def test_read_document_strips_utf8_bom(tmp_path):
    body = ("---\ntitle: Bom Test\ntype: note\naurora: library\n---\n\n"
            "## Summary\n\nStill fine.\n\n---\n\nBody.\n")
    p = tmp_path / "doc.md"
    p.write_bytes(b"\xef\xbb\xbf" + body.encode("utf-8"))
    doc = read_document(p)
    assert doc.frontmatter is not None
    assert doc.title == "Bom Test"


def test_read_document_tolerates_crlf(tmp_path):
    body = ("---\ntitle: Crlf Test\ntype: note\naurora: library\n---\n\n"
            "## Summary\n\nStill fine.\n\n---\n\nBody.\n")
    p = tmp_path / "doc.md"
    p.write_bytes(body.replace("\n", "\r\n").encode("utf-8"))
    doc = read_document(p)
    assert doc.title == "Crlf Test"
    assert doc.summary_first
```

In `cli/tests/test_checker_errors.py` (append). The assertion bodies below are normative; build the bucket with the same factory idiom the file's existing tests use (see `test_e7_exemptions` around line 92 — it already writes dotFILE probes; this adds dot-DIRECTORY probes):

```python
def test_dot_directories_are_invisible(make_bucket):
    root = make_bucket()
    trash = root / "library" / ".trash"
    trash.mkdir()
    (trash / "Not A Slug.md").write_text("no frontmatter at all",
                                         encoding="utf-8")
    cache = root / "sources" / ".cache"
    cache.mkdir()
    (cache / "junk file.pdf").write_bytes(b"%PDF-1.4")
    codes = {f.code for f in check(root)}
    assert not {"E3", "E5", "E7", "E8"} & codes


def test_blank_aurora_reports_e3_only(make_bucket):
    root = make_bucket()
    (root / "library" / "blank.md").write_text(
        '---\ntitle: Blank\ntype: note\naurora: ""\n---\n\n'
        "## Summary\n\nBlank aurora.\n\n---\n\nBody.\n",
        encoding="utf-8")
    findings = [f for f in check(root) if f.path.endswith("blank.md")]
    codes = [f.code for f in findings]
    assert "E3" in codes
    assert "E4" not in codes
```

In `cli/tests/test_hub_bucket.py` (append; mirror `test_iter_documents_fixture`'s imports):

```python
def test_iter_documents_skips_dot_directories(tmp_path):
    lib = tmp_path / "library" / ".obsidian"
    lib.mkdir(parents=True)
    (lib / "workspace.md").write_text("junk", encoding="utf-8")
    (tmp_path / "library" / "real.md").write_text(
        "---\ntitle: Real\ntype: note\naurora: library\n---\n\n"
        "## Summary\n\nReal.\n\n---\n\nBody.\n", encoding="utf-8")
    rels = [rel.as_posix() for _, rel, _ in iter_documents(tmp_path)]
    assert rels == ["real.md"]
```

- [ ] **Step 2: Run them to verify they fail**

Run: `cd cli && uv run --group dev pytest tests/test_document.py tests/test_checker_errors.py tests/test_hub_bucket.py -q`
Expected: the five new tests FAIL (BOM test: title is None; dot-dir tests: E8/E7 present, `.obsidian` file yielded; blank-aurora: E4 present). CRLF test may already PASS — that is the point of locking it.

- [ ] **Step 3: Implement**

`cli/src/fusion/document.py` — in `read_document` (line ~96), change only the encoding (utf-8-sig decodes BOM-less files identically and strips a leading BOM when present):

```python
        text = path.read_text(encoding="utf-8-sig")
```

`cli/src/fusion/bucket.py` — replace the loop body of `iter_documents` (lines 72–75):

```python
        for path in sorted(zone_dir.rglob("*.md")):
            rel = path.relative_to(zone_dir)
            if path.name == "INDEX.md" or any(
                    part.startswith(".") for part in rel.parts):
                continue
            yield zone, rel, read_document(path)
```

`cli/src/fusion/indexer.py` — `_zone_documents` filter becomes:

```python
    return [
        p
        for p in sorted(zone_dir.rglob("*.md"))
        if p.name != "INDEX.md"
        and not any(part.startswith(".")
                    for part in p.relative_to(zone_dir).parts)
    ]
```

`cli/src/fusion/checker.py` — `_e7_manifest`'s `on_disk` comprehension:

```python
    on_disk = {
        p.relative_to(sources).as_posix()
        for p in sources.rglob("*")
        if p.is_file() and p.name != "MANIFEST.md"
        and not any(part.startswith(".")
                    for part in p.relative_to(sources).parts)
    }
```

`_e8_filenames`'s skip condition:

```python
        for p in sorted(zone_dir.rglob("*")):
            if (not p.is_file() or p.name == "INDEX.md"
                    or any(part.startswith(".")
                           for part in p.relative_to(zone_dir).parts)):
                continue
```

`_e3_e4_e5_documents`'s E4 guard (a blank string is E3's finding — missing — not E4's):

```python
        aurora = doc.frontmatter.get("aurora")
        blank = isinstance(aurora, str) and not aurora.strip()
        if aurora is not None and not blank and aurora not in AURORAS:
```

- [ ] **Step 4: Full suite + fixture green**

Run: `cd cli && uv run --group dev pytest -q` → all pass (≥116).
Run: `uv run --project cli fusion check examples/crazy-ones` → `0 errors · 0 warnings`.

- [ ] **Step 5: Commit**

```bash
git add cli/src/fusion/document.py cli/src/fusion/bucket.py cli/src/fusion/indexer.py cli/src/fusion/checker.py cli/tests/test_document.py cli/tests/test_checker_errors.py cli/tests/test_hub_bucket.py
git commit -m "cli: readers harden for real files — BOM-proof documents, dot-directories invisible, one finding per blank aurora"
```

---

### Task 2: Failures speak JSON — error envelopes, honest messages, both archive signals

**Files:**
- Modify: `cli/src/fusion/cli.py` (`_fail` + its 12 call sites at lines 51, 68, 72, 77, 83, 99, 108, 114, 123, 138, 171)
- Modify: `cli/src/fusion/views.py` (`today`, `agenda`)
- Test: `cli/tests/test_cli.py`, `cli/tests/test_views.py`

**Interfaces:**
- Consumes: Task 1's tree (no dependency on its changes).
- Produces: under `--json`, every failure prints `{"ok": false, "error": "<message>"}` to **stdout** and exits 1 (same channel as `cmd_check`'s findings envelope, which already does this); human mode keeps `fusion: <message>` on stderr. Skills and scripts may rely on this envelope from here on.

- [ ] **Step 1: Failing tests**

In `cli/tests/test_cli.py` (append; the file already imports `main` and `json` — check its head and reuse its helpers, e.g. `out_json(capsys)` if present):

```python
def test_failure_emits_json_envelope(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)          # nowhere near a bucket
    assert main(["log", "noted", "x", "--json"]) == 1
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["ok"] is False
    assert "bucket" in payload["error"]
    assert captured.err == ""


def test_failure_stays_human_without_json(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["log", "noted", "x"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("fusion: ")


def test_check_names_the_missing_path(capsys):
    assert main(["check", "/nonexistent/nowhere"]) == 1
    assert "/nonexistent/nowhere" in capsys.readouterr().err
```

In `cli/tests/test_views.py` (append; build the two-bucket hub exactly the way `test_today_composes_across_buckets` does, adding one document): a document under `activities/mislabeled/plan.md` with `status: active` **and** `aurora: archive` (path has no `archive/` component). Assert it appears in **neither** `today()["groups"]` (flatten all groups' items) **nor** `agenda()["active"]`.

```python
def test_views_exclude_archive_aurora_off_archive_paths(...):
    ...  # setup per the sibling test's idiom
    doc = ("---\ntitle: Mislabeled\ntype: plan\naurora: archive\n"
           "status: active\n---\n\n## Summary\n\nShould not compose.\n\n---\n\nBody.\n")
    ...
    everything = [i["path"] for items in today()["groups"].values() for i in items]
    assert not any("mislabeled" in p for p in everything)
    assert not any("mislabeled" in i["path"] for i in agenda()["active"])
```

- [ ] **Step 2: Run to verify failure**

Run: `cd cli && uv run --group dev pytest tests/test_cli.py tests/test_views.py -q`
Expected: FAIL — envelope test gets empty stdout; check-path test sees the generic message; views test finds the mislabeled doc composed.

- [ ] **Step 3: Implement**

`cli/src/fusion/cli.py` — `_fail` becomes:

```python
def _fail(message: str, as_json: bool = False) -> int:
    if as_json:
        print(json.dumps({"ok": False, "error": message}, ensure_ascii=False))
    else:
        print(f"fusion: {message}", file=sys.stderr)
    return 1
```

Every existing `_fail(...)` call gains `, args.json` as its last argument (all 12 sites; every parser including `hub add`/`hub remove` already defines `--json`).

Three sites also get honest messages. `cmd_log` (line ~99):

```python
    if root is None or not (root / "BUCKET.md").is_file():
        given = getattr(args, "bucket", None)
        return _fail(f"no bucket at: {given}" if given else
                     "not inside a bucket (no BUCKET.md found) — use --bucket",
                     args.json)
```

`cmd_check` (line ~138):

```python
    if root is None:
        given = getattr(args, "path", None)
        return _fail(f"no bucket at: {given}" if given else
                     "not inside a bucket and no path given", args.json)
```

`cmd_index` (line ~123) and `cmd_status` (line ~171) use the same two-branch shape with `getattr(args, "path", None)` and their existing no-path message text.

`cli/src/fusion/views.py` — in `today()` and in `agenda()`, the exclusion line becomes (archive is path truth *and* aurora signal — a composed morning trusts either):

```python
            if "archive" in rel.parts or doc.aurora == "archive":
                continue
```

- [ ] **Step 4: Full suite green**

Run: `cd cli && uv run --group dev pytest -q` → all pass.

- [ ] **Step 5: Commit**

```bash
git add cli/src/fusion/cli.py cli/src/fusion/views.py cli/tests/test_cli.py cli/tests/test_views.py
git commit -m "cli: failures speak JSON too — error envelopes under --json, missing paths named, views trust both archive signals"
```

---

### Task 3: The gate never mistakes silence for identity

**Files:**
- Modify: `skills/fusion-intake/scripts/gate.py` (`similarity`, `git_history`)
- Test: `skills/fusion-intake/tests/test_gate.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `similarity(a, b) == 0.0` whenever either side yields zero shingles (exact dups are sha256's job upstream); `git_history` returns `[]` on any OS/subprocess failure.

- [ ] **Step 1: Failing tests**

Append to `skills/fusion-intake/tests/test_gate.py` (reuse its existing imports/helpers — it has the `bucket` fixture and a gate-runner helper; mirror the invocation idiom of the neighboring classification tests):

```python
def test_similarity_no_evidence_is_zero():
    assert gate.similarity("", "") == 0.0
    assert gate.similarity("... !!! ---", "%%% ***") == 0.0


def test_binary_pair_is_clean_new_not_near_dup(bucket):
    noise_a = b"\x89PNG\r\n\x1a\n" + b"\x00\x01\x02\xff\xfe" * 24
    noise_b = b"\x89PNG\r\n\x1a\n" + b"\x03\x04\x05\xfd\xfc" * 24
    (bucket / "sources" / "img-a.png").write_bytes(noise_a)
    (bucket / "inbox" / "img-b.png").write_bytes(noise_b)
    result = <the file's gate-runner helper>(bucket)
    assert result["near_dups"] == []
    assert [f["incoming"] for f in result["clean_new"]] == ["img-b.png"]


def test_git_history_survives_missing_cwd(tmp_path):
    assert gate.git_history(Path("sources/x.pdf"), tmp_path / "absent") == []
```

(The two PNG payloads contain no `\w` bytes beyond the header, differ byte-wise — so sha256 does not catch them — and decode to zero shingles.) Replace `<the file's gate-runner helper>` with the helper the file actually defines (`run_gate` per Phase 3).

- [ ] **Step 2: Run to verify failure**

Run: `uv run --with pytest --with pyyaml --with openpyxl --with pymupdf pytest skills/fusion-intake/tests/test_gate.py -q`
Expected: FAIL — similarity returns 1.0 for both-empty; the binary pair lands in `near_dups` at 1.0; the missing-cwd call raises instead of returning `[]`.

- [ ] **Step 3: Implement**

`gate.py` `similarity` (lines 99–107) becomes:

```python
def similarity(a: str, b: str) -> float:
    """Jaccard over word k-shingles: 0.0 disjoint .. 1.0 identical.
    Zero shingles on either side is absence of evidence, never identity —
    exact duplicates are sha256's catch upstream, not this function's."""
    sa, sb = _shingles(a), _shingles(b)
    if not sa or not sb:
        return 0.0
    union = len(sa | sb)
    return len(sa & sb) / union if union else 0.0
```

`git_history`'s except clause (line 119) becomes (FileNotFoundError is an OSError; TimeoutExpired is a SubprocessError — this widens to every OS-level failure while `returncode != 0` keeps handling non-repo dirs):

```python
    except (OSError, subprocess.SubprocessError):
        return []
```

- [ ] **Step 4: Full intake suite green**

Run: `uv run --with pytest --with pyyaml --with openpyxl --with pymupdf pytest skills/fusion-intake/tests -q` → all pass (≥37).

- [ ] **Step 5: Commit**

```bash
git add skills/fusion-intake/scripts/gate.py skills/fusion-intake/tests/test_gate.py
git commit -m "fusion-intake: the gate never mistakes silence for identity — empty-shingle similarity is zero, git history survives any OS failure"
```

---

### Task 4: Fidelity reaches the awkward files — merged cells, html mail, colliding attachments, two-page docx

**Files:**
- Modify: `skills/fusion-intake/scripts/convert.py` (`_xlsx_body` + new `_sheet_matrix`, `eml_to_text` + new `_HTMLText`/`html_to_text`, imports)
- Modify: `skills/fusion-intake/references/convert.md` (fidelity checklist — two lines, see Step 5)
- Modify: `skills/fusion-intake/tests/make_fixtures.py` (three new generators)
- Test: `skills/fusion-intake/tests/test_convert.py`

**Interfaces:**
- Consumes: Task 3's gate (no code dependency).
- Produces: `html_to_text(html) -> str` (module-level, testable directly); merged xlsx ranges unfolded to their anchor value; mail attachments never overwrite each other in the run dir.

- [ ] **Step 1: Fixture generators**

Append to `skills/fusion-intake/tests/make_fixtures.py` (model constants after the existing `DOCX_*` blocks):

```python
DOCX_TWO_PAGE_DOCUMENT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body>
<w:p><w:r><w:t>Page one of the onboarding pack.</w:t></w:r></w:p>
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
<w:p><w:r><w:t>Page two: the ledger discipline in daily practice.</w:t></w:r></w:p>
</w:body></w:document>"""


def make_docx_two_page(path: Path):
    """Two pages forced by an explicit page break."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", DOCX_CONTENT_TYPES)
        z.writestr("_rels/.rels", DOCX_RELS)
        z.writestr("word/document.xml", DOCX_TWO_PAGE_DOCUMENT)


def make_html_eml(path: Path):
    """HTML-only mail: entities, style and script blocks, no text/plain part."""
    msg = EmailMessage()
    msg["From"] = "gilberte@example.com"
    msg["To"] = "studio@example.com"
    msg["Subject"] = "Studio move — final quote"
    msg["Date"] = "Fri, 10 Jul 2026 09:00:00 +0200"
    msg.set_content(
        "<html><head><style>p{color:red}</style>"
        "<script>alert('tracking')</script></head>"
        "<body><p>Quote for Dupont &amp; Fils: total 1250 euros.</p>"
        "<p>Valid until <b>2026-08-01</b>.</p></body></html>",
        subtype="html")
    path.write_bytes(bytes(msg))


def make_eml_colliding_attachments(path: Path):
    """Two distinct attachments that share one filename."""
    msg = EmailMessage()
    msg["From"] = "gilberte@example.com"
    msg["To"] = "studio@example.com"
    msg["Subject"] = "Both riders"
    msg["Date"] = "Fri, 10 Jul 2026 10:00:00 +0200"
    msg.set_content("Two riders attached, same filename.\n")
    msg.add_attachment(b"rider one\n", maintype="text", subtype="plain",
                       filename="rider.txt")
    msg.add_attachment(b"rider two\n", maintype="text", subtype="plain",
                       filename="rider.txt")
    path.write_bytes(bytes(msg))


def make_merged_xlsx(path: Path):
    """A merged title spanning two columns — the anchor value must survive."""
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Budget"
    ws["A1"] = "Q3 forecast"
    ws.merge_cells("A1:B1")
    ws.append(["item", "amount"])
    ws.append(["strings", 42.5])
    wb.save(path)
```

- [ ] **Step 2: Failing tests**

Append to `skills/fusion-intake/tests/test_convert.py`, mirroring the admit/prepare invocation idiom of the file's existing route tests (e.g. `test_docx_libreoffice_path`, and its `soffice` skip marker for the docx test):

```python
def test_html_only_mail_reads_clean(bucket):
    # decoded entities, no tags, no script/style payload
    ...  # drop make_html_eml output in inbox, admit, prepare
    text = record["pages"][0]["text"]
    assert "Dupont & Fils" in text
    assert "alert(" not in text
    assert "color:red" not in text
    assert "<p>" not in text


def test_mail_attachments_never_collide(bucket):
    ...  # make_eml_colliding_attachments, admit, prepare
    assert sorted(record["attachments"]) == ["rider-2.txt", "rider.txt"]
    # and both files exist with their own content in the run dir


def test_merged_cells_keep_their_anchor_value(bucket):
    ...  # make_merged_xlsx, admit, prepare; read the produced document body
    assert "Q3 forecast" in body
    assert "| strings | 42.5 |" in body
    assert "| item | amount |" in body          # column B survived pruning


@pytest.mark.skipif(shutil.which("soffice") is None and shutil.which("libreoffice") is None,
                    reason="LibreOffice not installed")
def test_docx_page_break_yields_two_pages(bucket):
    ...  # make_docx_two_page, admit, prepare
    assert record["page_count"] >= 2
    assert len(record["images"]) == record["page_count"]
```

Also one direct unit test, no bucket needed:

```python
def test_html_to_text_direct():
    out = convert.html_to_text(
        "<style>x{}</style><script>bad()</script>"
        "<p>A &amp; B</p><p>C</p>")
    assert out == "A & B\nC"
```

- [ ] **Step 3: Run to verify failure**

Run: `uv run --with pytest --with pyyaml --with openpyxl --with pymupdf pytest skills/fusion-intake/tests/test_convert.py -q`
Expected: FAIL — `html_to_text` doesn't exist; entities stay encoded; second `rider.txt` overwrites the first; merged body loses "Q3 forecast" pairing / column pruning; page-break docx currently passes only the `>=1` assertion elsewhere.

- [ ] **Step 4: Implement in `convert.py`**

Add `from html.parser import HTMLParser` to the imports. New module-level code (place beside `eml_to_text`):

```python
class _HTMLText(HTMLParser):
    """Text of an HTML mail body: entities decoded (convert_charrefs),
    script/style dropped whole, block tags become line breaks."""
    _SKIP = {"script", "style"}
    _BREAK = {"p", "br", "div", "tr", "li", "table",
              "h1", "h2", "h3", "h4", "h5", "h6"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._chunks: list = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP:
            self._skip_depth += 1
        elif tag in self._BREAK:
            self._chunks.append("\n")

    def handle_endtag(self, tag):
        if tag in self._SKIP and self._skip_depth:
            self._skip_depth -= 1
        elif tag in self._BREAK:
            self._chunks.append("\n")

    def handle_data(self, data):
        if not self._skip_depth:
            self._chunks.append(data)


def html_to_text(html: str) -> str:
    parser = _HTMLText()
    parser.feed(html)
    parser.close()
    lines = [re.sub(r"[ \t]+", " ", ln).strip()
             for ln in "".join(parser._chunks).splitlines()]
    return "\n".join(ln for ln in lines if ln)
```

In `eml_to_text`, replace the tag-stripping line and the attachment loop:

```python
    if body and body.get_content_subtype() == "html":
        content = html_to_text(content)
    attachments = []
    for part in msg.iter_attachments():
        name = Path(part.get_filename() or "attachment.bin").name
        stem, dot, ext = name.partition(".")
        n = 2
        while name in attachments:
            name = f"{stem}-{n}{dot}{ext}"
            n += 1
        (work_dir / name).write_bytes(part.get_payload(decode=True) or b"")
        attachments.append(name)
```

New `_sheet_matrix` beside `_xlsx_body`, and `_xlsx_body` uses it:

```python
def _sheet_matrix(ws):
    """All cell values with merged ranges unfolded — every cell a merge
    spans carries the anchor's value, so pruning never eats merged data."""
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    for rng in ws.merged_cells.ranges:
        if rng.min_row - 1 >= len(rows):
            continue
        anchor_row = rows[rng.min_row - 1]
        anchor = (anchor_row[rng.min_col - 1]
                  if rng.min_col - 1 < len(anchor_row) else None)
        for r in range(rng.min_row, min(rng.max_row, len(rows)) + 1):
            row = rows[r - 1]
            for c in range(rng.min_col, min(rng.max_col, len(row)) + 1):
                row[c - 1] = anchor
    return rows


def _xlsx_body(path: Path):
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True)
    sections, sheets, rows_total = [], 0, 0
    for name in wb.sheetnames:
        rows = _sheet_matrix(wb[name])
        live = [r for r in rows if not _row_empty(r)]
        if live:
            sheets += 1
            rows_total += max(len(live) - 1, 0)
            sections.append(f"## {name}\n\n{rows_to_table(rows)}")
    return "\n\n".join(sections) or "*No data*", sheets, rows_total
```

- [ ] **Step 5: Reference doc catches up (same commit)**

In `skills/fusion-intake/references/convert.md`, in the fidelity checklist section, extend the tables item to state that merged ranges are unfolded to their anchor value before pruning, and the mail item to state that html-only bodies are converted with entities decoded and script/style dropped, and that attachment names are de-collided (`name-2.ext`). Two sentences, matching the checklist's existing voice — no restructuring.

- [ ] **Step 6: Full intake suite green**

Run: `uv run --with pytest --with pyyaml --with openpyxl --with pymupdf pytest skills/fusion-intake/tests -q` → all pass (≥42; the docx test may SKIP where LibreOffice is absent — on this machine it must PASS).

- [ ] **Step 7: Commit**

```bash
git add skills/fusion-intake/scripts/convert.py skills/fusion-intake/references/convert.md skills/fusion-intake/tests/make_fixtures.py skills/fusion-intake/tests/test_convert.py
git commit -m "fusion-intake: fidelity reaches the awkward files — merged cells unfold, html mail reads clean, attachments never collide, two pages proven"
```

---

### Task 5: `--help` teaches — every command explains itself

**Files:**
- Modify: `cli/src/fusion/cli.py` (`build_parser` only)
- Modify: `cli/README.md` (only if its command table contradicts the new help — verify, don't rewrite)
- Test: `cli/tests/test_cli.py`

**Interfaces:**
- Consumes: Task 2's cli.py.
- Produces: no behavioral change — parser shape, flags, defaults identical; only `description=`/`help=`/`epilog=` strings are added.

- [ ] **Step 1: Failing test**

Append to `cli/tests/test_cli.py`:

```python
def test_help_describes_every_command(capsys):
    needles = {
        "new": "Scaffold", "hub": "registry", "log": "append-only",
        "index": "Deterministic", "check": "SPEC", "status": "glance",
        "today": "morning", "agenda": "horizon",
    }
    for cmd, needle in needles.items():
        with pytest.raises(SystemExit):
            main([cmd, "--help"])
        assert needle in capsys.readouterr().out, cmd
```

Run: `cd cli && uv run --group dev pytest tests/test_cli.py::test_help_describes_every_command -q` → FAIL for every command.

- [ ] **Step 2: Implement — the exact strings**

In `build_parser`, add to each `sub.add_parser(...)` a `description=` and give every positional a `help=`. The normative strings (voice: the notary's — plain, exact, a little proud):

- **new**: description `"Scaffold a conformant bucket at PATH — six zones, BUCKET.md, an opened ledger — and register it in the hub."`; `path` help `"directory to create (missing or empty)"`.
- **hub**: description `"The registry at ~/.fusion/hub.md (override: FUSION_HUB) — the agent's map of your buckets. No subcommand: list."`; `hub add` description `"Register an existing bucket (reads its BUCKET.md)."`, `path` help `"bucket root to register"`; `hub remove` description `"Retire a bucket from the hub. Files stay where they are."`, `name` help `"registered bucket name"`.
- **log**: description `"Append one signed entry to the append-only ledger — or, with no arguments, read it."`; `object` help `"what was acted on — a path, or 'a → b' for a move"`; epilog `"Read mode: 'fusion log' alone prints the ledger; --since DATE or --since last-reflection narrows it. The bucket resolves from --bucket, else by walking up from the current directory."`
- **index**: description `"Regenerate library/INDEX.md and activities/INDEX.md from the documents on disk. Deterministic: same tree, same bytes."`; `path` help `"bucket root (default: walk up from the current directory)"`.
- **check**: description `"Audit a bucket against the convention (SPEC §11). Exit 1 on errors; warnings never fail the check."`; `path` help as index's.
- **status**: description `"One bucket at a glance: documents per zone, active work, the ledger's recent tail."`; `path` help as index's.
- **today**: description `"The composed morning across every hub bucket: commitments and active work, grouped by aurora."`
- **agenda**: description `"The wider horizon across the hub: dated items first (due:/date:), then active work."`

- [ ] **Step 3: cli/README truthfulness pass**

Read `cli/README.md`; where its command table and the new descriptions disagree, align the README (the new strings are canonical). Confirm it documents `fusion log`'s no-arg read mode and `--bucket` (the Phase 3 friction) — add one line if absent.

- [ ] **Step 4: Suite green, then commit**

Run: `cd cli && uv run --group dev pytest -q` → all pass.

```bash
git add cli/src/fusion/cli.py cli/README.md cli/tests/test_cli.py
git commit -m "cli: --help teaches — every command explains itself, every positional named"
```

---

### Task 6: The vocabulary settles — one human-gated SPEC amendment

**This task begins with the controller (not a subagent) asking the human via AskUserQuestion.** Four independent decisions, each with a recommendation. Implement exactly what is approved — nothing more — in ONE commit. If the human approves none, commit nothing and record the decisions in the progress ledger.

**The four questions:**

1. **`due:` field** — `fusion agenda` already reads `due:`/`date:`, and the commitments aurora is defined by deadlines, yet SPEC §4 doesn't know the field. *Recommend: add.* If approved, insert into the §4 optional-fields table (after the `status` row):
   `| \`due\` | ISO 8601 date the thing falls due — \`fusion agenda\` surfaces it | anywhere |`
   And add `date` nowhere — `agenda`'s `date:` fallback stays an implementation courtesy, not vocabulary.
2. **`resource:` wording** — §4 says "URI of an external thing this document describes", but the amended conventions card and fusion-analyst's export gear point it at in-bucket artifacts too. *Recommend: widen.* If approved, the §4 table row becomes:
   `| \`resource\` | URI or path of a thing this document describes but does not contain | anywhere |`
3. **W5 floor** — SPEC §11 item 5: buckets with fewer than two reflections never trigger the untouched-activity warning, so a young bucket (the entire dogfood week) gets no protection. *Recommend: one reflection suffices — the window then runs from the bucket's birth to that reflection; zero reflections stays silent (no ritual yet, nothing to hold the bucket to).* If approved: §11 item 5's last sentence becomes `"Buckets that have never reflected do not trigger this warning; after the first reflection the window runs from the bucket's birth."`, and in `checker._w5_untouched_activities` the guard and window become:

   ```python
       if not reflections:
           return []
       start = reflections[-2] + 1 if len(reflections) >= 2 else 0
       window = entries[start:reflections[-1]]
   ```

   Update `cli/tests/test_checker_warnings.py`: `test_w5_never_triggers_below_two_reflections` splits into `test_w5_silent_with_no_reflection` (unchanged expectation at zero) and `test_w5_fires_after_first_reflection` (one `reflected` entry, one active activity created before it and never mentioned → W5 present). Verify the fixture stays 0/0 (`examples/crazy-ones` has exactly one `reflected` entry — if W5 now fires there, the fixture's active activities must genuinely be mentioned before that reflection; check first, and if the fixture would warn, say so in the AskUserQuestion option text so the human decides with full facts).
4. **The example actor** — `bertrand` is the fictional human in SPEC §6's grammar example and the fixture ledger (Phase 1 reviewer deferred it as user taste). *Recommend: keep — it's the author's signature in a repo whose README toasts the crazy ones.* If instead the human chooses a neutral name (offer `ren`): update SPEC.md:230, the four `bertrand` lines in `examples/crazy-ones/LEDGER.md`, `cli/tests/test_ledger.py:21`, and the mirrored line in `docs/specs/2026-07-10-fusion-design.md:229`; leave `docs/plans/*` untouched (historical record); then extend `cli/tests/test_skill_family.py`'s personal-path test to also sweep `SPEC.md`, `README.md`, `examples/`, and `docs/acceptance/`.

**If anything in the conventions card must change** (only question 2 plausibly touches it — the card's line "documents point (`resource:`) at big things, they never swallow them" already matches the widened wording, so likely nothing): apply to **all four copies byte-identically**.

- [ ] Controller asks the four questions (one AskUserQuestion call, four entries).
- [ ] Implementer applies exactly the approved set; runs `cd cli && uv run --group dev pytest -q` and `uv run --project cli fusion check examples/crazy-ones` (0/0).
- [ ] Commit (adjust message to the approved set):

```bash
git add SPEC.md cli/src/fusion/checker.py cli/tests/ examples/ docs/specs/ skills/*/references/fusion-conventions.md
git commit -m "spec: the vocabulary settles — <approved items> (human-approved amendments)"
```

---

### Task 7: The newcomer's path — Getting Started, a fixture tour, a truthful README

**Files:**
- Create: `docs/GETTING-STARTED.md`
- Create: `examples/README.md` (sibling of `crazy-ones/`, NOT inside it — the fixture stays byte-frozen)
- Modify: `README.md`

**Interfaces:**
- Consumes: Task 5's final `--help` strings (quote them accurately), Task 6's outcomes (if the actor was renamed, examples/README must not say "bertrand").
- Produces: the documents Task 8's transcript and Task 9's protocol link to.

- [ ] **Step 1: Write `docs/GETTING-STARTED.md`** — exactly this content (adjust only if Task 6 changed facts it states):

````markdown
# Getting started

Fusion is two moves: install a small CLI, copy four skills. Then you make
your first bucket and start living in it. Ten minutes, no wizard.

## What you need

- [uv](https://docs.astral.sh/uv/) — installs and runs the CLI.
- An agent that reads [Agent Skills](https://agentskills.io) — Claude Code,
  Pi, Goose, or whatever comes next.
- Optional: LibreOffice (`soffice` on PATH) — only fusion-intake's
  docx/pptx/legacy-office route needs it.

## Move one — the CLI

From a clone (or once published on PyPI: `uv tool install fusion-cli`):

```bash
git clone https://github.com/bluewaves-creations/fusion.git
uv tool install ./fusion/cli
fusion --version
```

The CLI is the notary: it records (ledger), registers (hub, manifest,
indexes), checks (the convention), and composes your day. It never judges —
that's the skills' job.

## Move two — the skills

```bash
cp -r fusion/skills/fusion-* ~/.agents/skills/
```

(Or your agent's skills directory. The skills are standard-compliant and
self-contained — copying them **is** installing them.)

Four skills, four accountabilities: **fusion-intake** guards what enters,
**fusion-librarian** owns the library, **fusion-planner** runs activities,
**fusion-analyst** builds reports and exports.

## Your first bucket

A bucket is a life-domain — personal, your studio, one per company. Few and
bold. Each is its own git repo, private by construction.

```bash
fusion new ~/buckets/personal --kind personal \
  --description "Home base: admin, health, house, money."
```

That scaffolds six zones (`inbox/ sources/ library/ activities/ workbench/
output/`), writes `BUCKET.md`, opens the ledger, and registers the bucket in
the hub (`~/.fusion/hub.md`) — the one-file map your agent reads to know
your world.

```bash
fusion hub          # your buckets
fusion status       # this bucket at a glance
fusion check        # audit against the convention — 0 errors, carry on
```

## Live in it

**You never file.** Drop anything — a PDF, a spreadsheet, a mail export —
into `inbox/` and tell your agent to run intake. The gate classifies it
(new, update, duplicate, conflicting), preserves the original byte-for-byte
under `sources/`, converts it losslessly to markdown in the library, and
signs the ledger. You judge; it operates; the files remember.

Each morning:

```bash
fusion today        # commitments and active work, across every bucket
fusion agenda       # the wider horizon: dated things first
```

And once a week, ask the librarian to **reflect**: it reads the ledger,
proposes prunes and conventions, you judge, it signs `reflected`. That's the
metabolism — the bucket learns.

## Where to go next

- [The convention itself](../SPEC.md) — SPEC.md is the actual product.
- [A finished bucket to wander](../examples/README.md) — the crazy-ones tour.
- [The CLI, command by command](../cli/README.md).
- [The four skills](../skills/README.md).
````

- [ ] **Step 2: Write `examples/README.md`** — exactly:

````markdown
# The example bucket — a tour

[`crazy-ones/`](crazy-ones/) is a complete, conformant Fusion bucket for a
fictional music studio. It is also the project's normative test fixture —
`fusion check` holds it at zero errors, zero warnings, and the golden tests
freeze its INDEX files byte-for-byte. Wander it; don't edit it.

Read it in this order:

1. **[BUCKET.md](crazy-ones/BUCKET.md)** — the identity card: name, kind,
   description, and the § Conventions section where the bucket's own rules
   and standing delegations accumulate as it learns.
2. **[LEDGER.md](crazy-ones/LEDGER.md)** — the trust record. Every act the
   librarian took, signed and dated, in eleven closed verbs. The story of
   the bucket is readable here alone.
3. **[library/](crazy-ones/library/)** — curated knowledge. Every document
   opens with three required fields (`title`, `type`, `aurora`) and a
   summary before anything else. `INDEX.md` is generated — never edited.
4. **[activities/](crazy-ones/activities/)** — work with a beginning and an
   end; `status: active` is what `fusion today` composes your morning from.
5. **[sources/](crazy-ones/sources/)** — originals, byte-for-byte, each with
   a MANIFEST row (sha256, provenance, converted twin). Immutable.
6. **[workbench/](crazy-ones/workbench/)** — the one ruleless zone; drafts
   live here without frontmatter until they're promoted.
7. **[output/](crazy-ones/output/)** — what the bucket ships: documents and
   exported deliverables.

The eight `aurora` values (commitments · focus · ops · collab · life ·
explore · archive · library) are an attention system, not a taxonomy — they
say what a thing means for your attention, and they are the same eight in
every bucket, forever.
````

- [ ] **Step 3: README edits** — three surgical changes, nothing else:

1. Lineage sentence: replace `Google's [OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog),` with `Google's [Knowledge Catalog](https://github.com/GoogleCloudPlatform/knowledge-catalog) open format ("OKF" in our design spec),` — the label a newcomer can verify.
2. After the "How it's built" section, insert:

   ```markdown
   ## Get started

   Two moves — install the CLI, copy the skills — then make your first
   bucket. The walkthrough: [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md).
   ```

3. Status table row 4: `| 4 | Dogfood + release | in progress |`.

- [ ] **Step 4: Verify and commit**

Every relative link in the three files must resolve (`docs/GETTING-STARTED.md` uses `../` links — check each). `uv run --project cli fusion check examples/crazy-ones` still 0/0 (the new `examples/README.md` sits outside the bucket).

```bash
git add docs/GETTING-STARTED.md examples/README.md README.md
git commit -m "docs: the newcomer's path — getting started in two moves, a fixture tour, a truthful README"
```

---

### Task 8: Install proven from a clean slate — the acceptance transcript

**Files:**
- Create: `docs/acceptance/2026-07-10-phase-4-install.md`

**Interfaces:**
- Consumes: Tasks 1–7 all landed (the transcript exercises final behavior — help text, JSON envelopes).
- Produces: the evidence line Task 9 cites for the ROADMAP's open-source gate box.

Play a brand-new user on this machine, touching neither the global uv tools nor the real hub. Every command and its real output goes in the transcript (trim long output with `[…]`, never fabricate).

- [ ] **Step 1: Clean-slate install** into `/tmp/fusion-clean` (isolated venv — proves the package, not the machine):

```bash
REPO=$(git rev-parse --show-toplevel)     # run from the repo; $REPO is used everywhere below
FUSION=/tmp/fusion-clean/.venv/bin/fusion
rm -rf /tmp/fusion-clean && mkdir -p /tmp/fusion-clean && cd /tmp/fusion-clean
uv venv .venv
uv pip install --python .venv/bin/python "$REPO/cli"
$FUSION --version
$FUSION --help
```

**Transcript rule (constraint 2):** the transcript writes `$REPO` and `$FUSION` verbatim — the literal absolute repo path must never appear in the committed file.

- [ ] **Step 2: Two-move check** — verify the skills install claim: `cp -r $REPO/skills/fusion-* /tmp/fusion-clean/skills/` then `ls`; note in the transcript that copying **is** installing (no build step, agentskills.io standard).

- [ ] **Step 3: First-bucket round trip**, hub sandboxed:

```bash
export FUSION_HUB=/tmp/fusion-clean/hub.md FUSION_ACTOR=newcomer
$FUSION new /tmp/fusion-clean/personal --kind personal --description "First bucket."
$FUSION hub
cd /tmp/fusion-clean/personal
$FUSION log noted BUCKET.md --note "first entry by hand"
$FUSION index && $FUSION check && $FUSION status
$FUSION today
$FUSION check /nonexistent --json ; echo "exit=$?"   # the JSON failure envelope, shown working
```

- [ ] **Step 4: The GETTING-STARTED cross-read** — follow `docs/GETTING-STARTED.md` top to bottom against what just happened; any step that lied or omitted becomes a fix to that doc **in this commit** (documentation excellence: the walkthrough is tested, not assumed).

- [ ] **Step 5: Write the transcript** (`docs/acceptance/2026-07-10-phase-4-install.md`): purpose, environment (isolated venv, sandboxed hub), each step with real output, a Frictions section (even if empty), verdict. Then:

```bash
rm -rf /tmp/fusion-clean
git add docs/acceptance/2026-07-10-phase-4-install.md docs/GETTING-STARTED.md
git commit -m "docs: install proven from a clean slate — the two-move setup holds end to end"
```

---

### Task 9: The dogfood week gets a protocol — and the gate box that can close, closes

**Files:**
- Create: `docs/dogfood/2026-07-protocol.md`
- Create: `docs/dogfood/frictions.md`
- Modify: `docs/ROADMAP.md` (one gate box)

**Interfaces:**
- Consumes: everything prior; cites Task 8's transcript as evidence.
- Produces: the running documents Part B lives in.

- [ ] **Step 1: Write `docs/dogfood/2026-07-protocol.md`** — exactly:

````markdown
# Dogfood protocol — July 2026

Phase 4's last three gate boxes close on lived evidence, not tasks. This is
the protocol for gathering it. The humans: Bertrand judges; the agent
operates; this file and [frictions.md](frictions.md) remember.

## Day one — bootstrap

- [ ] Create the two real buckets (`fusion new`), real hub, real paths —
      names, kinds, and descriptions are the human's call.
- [ ] Seed each: intake the first real legacy files through fusion-intake
      (the gate's first live customers), let the librarian shape the first
      library structure, open the first real activities with the planner.
- [ ] Run `fusion today` — the first real composed morning. Record verbatim
      in frictions.md whether it told the truth about the day.

## The week — daily

- [ ] Morning: `fusion today` (and `fusion agenda` when planning ahead).
- [ ] As things arrive: inbox → intake. Never file by hand.
- [ ] Any hesitation, wrong guess, missing affordance, or ugly output goes
      in [frictions.md](frictions.md) **the moment it happens** — a friction
      remembered at week's end is a friction lost.
- [ ] `fusion check` before closing the laptop; the ledger signed for
      everything the agent did.

## End of week — the reflections

- [ ] One full reflection cycle **per bucket**: the librarian introspects
      (`fusion log --since last-reflection`), proposes prunes and
      conventions, the human judges, learnings land in BUCKET.md
      § Conventions, `reflected` signs the cycle.
- [ ] Triage frictions.md: every row becomes fix / defer / wontfix, with the
      disposition written in the row.

## Closing the gate

- [ ] `fusion today` composed a real morning across buckets → tick, with the
      day-one record as evidence.
- [ ] One reflection cycle per bucket ran end to end → tick, citing the two
      `reflected` ledger entries.
- [ ] A week of real use, frictions recorded and triaged → tick, citing
      frictions.md.
- [ ] Update README's status table (Phase 4 → ✅) and record the phase's
      lessons in the improvement loop, per the roadmap's standing rule.
````

- [ ] **Step 2: Write `docs/dogfood/frictions.md`** — exactly:

```markdown
# Frictions — the dogfood log

Recorded the moment they happen; triaged at week's end. Severity: **blocker**
(stopped the work) · **grind** (works, but fights you) · **paper cut**
(noticed, moved on).

| # | date | bucket | during | friction | severity | disposition |
|---|---|---|---|---|---|---|
```

- [ ] **Step 3: Tick the one gate box that is now earned.** In `docs/ROADMAP.md`, Phase 4's fourth box becomes:

```markdown
- [x] Open-source pass: no personal paths, install-from-clean-machine
      test, README truthful.
      Evidence: sweep clean (test_skill_family + repo audit, 2026-07-10) ·
      docs/acceptance/2026-07-10-phase-4-install.md · README claims
      re-verified against the tree in the Task-7 commit.
```

The other three boxes stay open — they are Part B's to close.

- [ ] **Step 4: Commit**

```bash
git add docs/dogfood/ docs/ROADMAP.md
git commit -m "docs: the dogfood week has a protocol — frictions logged live, a gate that closes on evidence"
```

---

## Final review — whole branch

Dispatch the final code reviewer (most capable model) on the full range `f0f6e1a..HEAD` with the review package script, the Global Constraints above as the lens, and the Minor-findings roll-up from the task reviews. Fix Critical/Important in one wave; re-verify.

## Part B — the living gate (not tasks; begins after the final review)

Part B is real life, run through the protocol document, across real sessions:

1. **Bootstrap handoff (the very next step after the final review):** ask the human — one AskUserQuestion — for the two buckets' names, paths, kinds, and one-line descriptions (personal + pro; the spec's day-one shape), and what legacy files to feed intake first. Then bootstrap live: real `fusion new`, real hub, first real intake, first real morning.
2. **The week:** the human lives in it; the agent operates it; frictions land in `docs/dogfood/frictions.md` as they happen.
3. **The reflections and the close:** one cycle per bucket, frictions triaged, the last three ROADMAP boxes ticked with evidence, README status flipped, lessons recorded. Phase 4 ends there — and with it, v1.

## Self-review notes (writing-plans checklist, run before committing this plan)

- Spec coverage: ROADMAP Phase 4 box 4 → Tasks 6–9; boxes 1–3 → Part B protocol; deferred list → triage table (every item dispositioned).
- No placeholders: the three `...`-bearing test skeletons (Tasks 2–4) each name the exact sibling test whose fixture idiom they mirror and give normative assertions — the `...` is setup boilerplate visible in the file being edited, never unspecified behavior.
- Type consistency: `_fail(message, as_json)` matches all call-site edits; `html_to_text` name consistent across fixture, test, and implementation; `_sheet_matrix` consumed only by `_xlsx_body`.
