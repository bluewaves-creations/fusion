# Friction Improvements (rows 14–17) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the four dogfood learnings from the bucket-import program: a `relink` verb on the MANIFEST single writer (frictions 12+14), a W8 summary-only-document warning (friction 17), the remote first-contact recipe (friction 15), and the `source:` string-or-list convention (friction 16) — shipped as fusion v1.4.0.

**Architecture:** `relink` joins `convert.py` (the only writer of `sources/MANIFEST.md`) as a strict in-place repoint of one value inside a `library` cell. W8 extends the checker's existing warning family via a new `summary_only` field on the `Document` model, following the same `iter_documents` pass pattern as W3/W4. Everything else is documentation with exact text below.

**Tech Stack:** Python (stdlib + pyyaml), pytest; repo `~/Developer/fusion`.

## Global Constraints

- `sources/MANIFEST.md` has exactly ONE writer: `skills/fusion-intake/scripts/convert.py`. No other code, script, or hand-edit may touch it. The `relink` verb must live there.
- The checker is a liberal reader (SPEC §0 idiom, `checker.py:1`): it reports, never raises; warnings never become errors.
- W8 is a **warning**. Rule (exact): a document whose body parses summary-first (`doc.summary_first` is `True`), has nothing but whitespace after the `---` line that closes the summary, AND whose frontmatter carries neither `source:` nor `resource:`. The pointer exemption is load-bearing: a converted scan's designed shape IS summary + `source:` pointer (72 such docs live in family-business — verified 2026-07-12, plan-review simulation: with the exemption, all five live buckets show ZERO W8 hits). Documents that fail summary-first are E5's territory — W8 must stay silent for them (no double-flagging).
- The fusion-intake test suite imports `convert` directly via `conftest.py`'s `sys.path` insertion and builds buckets by hand — no `fusion` package imports in skill tests (see `skills/fusion-intake/tests/conftest.py:1-8`).
- Register files are written with `encoding="utf-8", newline="\n"` — every existing writer pins LF; new writes must too.
- MANIFEST cell grammar: 5 pipe-separated cells; empty `library` cell is `—`; multi-value cells are joined with `", "` (see `manifest_link`, `convert.py:208-225`). `relink` must preserve this grammar byte-for-byte for untouched values.
- Do NOT bump SPEC.md's "Version 1.0" header — precedent: W6/W7 shipped without a SPEC version bump; `fusion_version: "1.0"` in every live BUCKET.md ties to that string. The release is carried by the CLI version: `cli/pyproject.toml` `version = "1.4.0"`.
- Exact test commands (from `.github/workflows/ci.yml`):
  - CLI: `cd cli && uv run --group dev pytest -q`
  - intake: `uv run --with pytest --with pyyaml --with openpyxl --with pymupdf --with pillow pytest skills/fusion-intake/tests -q`
  - librarian: `uv run --with pytest --with pyyaml pytest skills/fusion-librarian/tests -q`
- Commit at the end of each task; commit messages end with `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.

---

### Task 1: `relink` verb on the single writer

**Files:**
- Modify: `skills/fusion-intake/scripts/convert.py` (three spots: after `manifest_link` ~line 226; after `link` ~line 710; CLI parser+dispatch ~lines 865/885)
- Modify: `skills/fusion-intake/SKILL.md` (the "Running it" command list, after the `link` command ~line 91)
- Modify: `skills/fusion-librarian/references/restructure.md` (step 3, "Execute")
- Test: `skills/fusion-intake/tests/test_convert.py`

**Interfaces:**
- Produces: `relink(root, source_rel, old_doc, new_doc) -> dict` and CLI `convert.py relink --bucket --source --from --to`. Task 4 references the verb in friction dispositions; no other task consumes it.

- [ ] **Step 1: Write the failing tests** (append to `skills/fusion-intake/tests/test_convert.py`)

```python
# ── relink ───────────────────────────────────────────────────────────────

def _doc(root, rel):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("---\ntitle: T\ntype: note\naurora: library\n---\n\n"
                 "## Summary\n\nS.\n\n---\n\nBody.\n", encoding="utf-8")
    return rel


def test_relink_repoints_single_value(bucket):
    put_inbox(bucket, "deed.xlsx", fx.make_xlsx)
    admit(bucket, "deed.xlsx")
    old = _doc(bucket, "library/records/deed.md")
    convert.link(bucket, "records/deed.xlsx", old)
    new = _doc(bucket, "library/areas/legal/deed.md")
    out = convert.relink(bucket, "records/deed.xlsx", old, new)
    assert out == {"source": "records/deed.xlsx", "from": old, "to": new}
    manifest = (bucket / "sources" / "MANIFEST.md").read_text(encoding="utf-8")
    row = manifest.strip().splitlines()[-1]
    cells = [c.strip() for c in row.strip("|").split("|")]
    assert cells[4] == new
    assert old not in manifest


def test_relink_multi_value_cell_touches_only_the_target(bucket):
    put_inbox(bucket, "deed.xlsx", fx.make_xlsx)
    admit(bucket, "deed.xlsx")
    keep = _doc(bucket, "library/records/summary.md")
    old = _doc(bucket, "library/records/deed.md")
    convert.link(bucket, "records/deed.xlsx", keep)
    convert.link(bucket, "records/deed.xlsx", old)
    new = _doc(bucket, "library/areas/legal/deed.md")
    convert.relink(bucket, "records/deed.xlsx", old, new)
    manifest = (bucket / "sources" / "MANIFEST.md").read_text(encoding="utf-8")
    row = manifest.strip().splitlines()[-1]
    cells = [c.strip() for c in row.strip("|").split("|")]
    assert cells[4] == f"{keep}, {new}"


def test_relink_refusals(bucket):
    put_inbox(bucket, "deed.xlsx", fx.make_xlsx)
    admit(bucket, "deed.xlsx")
    old = _doc(bucket, "library/records/deed.md")
    new = _doc(bucket, "library/areas/legal/deed.md")
    # row exists but cell is empty — old value not present
    with pytest.raises(convert.IntakeError, match="does not carry"):
        convert.relink(bucket, "records/deed.xlsx", old, new)
    convert.link(bucket, "records/deed.xlsx", old)
    # no such source row
    with pytest.raises(convert.IntakeError, match="not in manifest"):
        convert.relink(bucket, "records/ghost.xlsx", old, new)
    # from == to is not a change
    with pytest.raises(convert.IntakeError, match="is a change"):
        convert.relink(bucket, "records/deed.xlsx", old, old)
    # target must exist on disk
    with pytest.raises(convert.IntakeError, match="does not exist on disk"):
        convert.relink(bucket, "records/deed.xlsx", old, "library/nowhere.md")
    # target already linked
    convert.link(bucket, "records/deed.xlsx", new)
    with pytest.raises(convert.IntakeError, match="already carries"):
        convert.relink(bucket, "records/deed.xlsx", old, new)
    # nothing was mutated by any refusal: both values still present, in order
    manifest = (bucket / "sources" / "MANIFEST.md").read_text(encoding="utf-8")
    row = manifest.strip().splitlines()[-1]
    cells = [c.strip() for c in row.strip("|").split("|")]
    assert cells[4] == f"{old}, {new}"


def test_relink_cli(bucket):
    put_inbox(bucket, "deed.xlsx", fx.make_xlsx)
    admit(bucket, "deed.xlsx")
    old = _doc(bucket, "library/records/deed.md")
    convert.link(bucket, "records/deed.xlsx", old)
    new = _doc(bucket, "library/areas/legal/deed.md")
    rc = convert.main(["relink", "--bucket", str(bucket),
                       "--source", "records/deed.xlsx",
                       "--from", old, "--to", new])
    assert rc == 0
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run --with pytest --with pyyaml --with openpyxl --with pymupdf --with pillow pytest skills/fusion-intake/tests/test_convert.py -q -k relink`
Expected: FAIL — `AttributeError: module 'convert' has no attribute 'relink'`

- [ ] **Step 3: Implement `manifest_relink` + `relink` + CLI wiring**

In `convert.py`, directly after `manifest_link` (line ~226):

```python
def manifest_relink(root: Path, rel: str, old_doc: str, new_doc: str) -> None:
    path = _manifest_path(root)
    if not path.is_file():
        raise IntakeError(f"no manifest at {path}")
    if old_doc == new_doc:
        raise IntakeError(
            f"relink is a change: --from and --to are both {old_doc!r}")
    if not (Path(root) / new_doc).is_file():
        raise IntakeError(f"relink target does not exist on disk: {new_doc}")
    lines = path.read_text(encoding="utf-8").splitlines()
    hit = False
    for i, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 5 and cells[0] == rel:
            values = ([] if cells[4] in ("—", "")
                      else [v.strip() for v in cells[4].split(",")])
            if old_doc not in values:
                raise IntakeError(
                    f"cell does not carry {old_doc!r} for source {rel} "
                    f"(cell: {cells[4]!r})")
            if new_doc in values:
                raise IntakeError(
                    f"cell already carries {new_doc!r} for source {rel}")
            cells[4] = ", ".join(
                new_doc if v == old_doc else v for v in values)
            lines[i] = "| " + " | ".join(cells) + " |"
            hit = True
            break
    if not hit:
        raise IntakeError(f"source not in manifest: {rel}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
```

Directly after `link` (line ~710):

```python
def relink(root: Path, source_rel: str, old_doc: str, new_doc: str) -> dict:
    manifest_relink(Path(root), source_rel, old_doc, new_doc)
    return {"source": source_rel, "from": old_doc, "to": new_doc}
```

In the CLI parser block, after the `link` subparser:

```python
    p = sub.add_parser("relink", help="repoint one value in a MANIFEST "
                       "library cell after a document moved")
    p.add_argument("--bucket", required=True)
    p.add_argument("--source", required=True,
                   help="path relative to sources/")
    p.add_argument("--from", dest="from_doc", required=True,
                   help="current zone-relative doc path in the cell")
    p.add_argument("--to", dest="to_doc", required=True,
                   help="new zone-relative doc path (must exist)")
```

In the dispatch chain, after the `link` branch:

```python
        elif args.cmd == "relink":
            out = relink(Path(args.bucket), args.source,
                         args.from_doc, args.to_doc)
```

- [ ] **Step 4: Run the tests to verify they pass, then the full intake suite**

Run: `uv run --with pytest --with pyyaml --with openpyxl --with pymupdf --with pillow pytest skills/fusion-intake/tests -q`
Expected: PASS, no regressions.

- [ ] **Step 5: Document the verb where its users look**

In `skills/fusion-intake/SKILL.md`, AFTER the whole of item "4. **Close** (per file)" in "Running it" (i.e., after the `cleanup` line that ends it — do NOT splice into the middle of the close sequence), add as its own item:

```
5. **Relink** (only when a linked document later moves):
   `uv run <skill>/scripts/convert.py relink --bucket <root> --source <cat>/<name> --from <old-doc> --to <new-doc>`
   — repoints the cell value in place. MANIFEST.md is single-writer; a
   stale cell is never hand-edited.
```

(If the items in "Running it" are not numbered, match the surrounding list style instead of `5.` — the placement rule stands.)

In `skills/fusion-librarian/references/restructure.md`, replace step 3 with:

```
3. **Execute.** Move files; update relative links in affected documents
   (grep for the old paths); keep filenames conformant. If a moved
   document is named by a MANIFEST `library` cell (it was converted from
   a source), repoint the cell with the intake writer — `MANIFEST.md` is
   single-writer, never hand-edited:
   `uv run <fusion-intake>/scripts/convert.py relink --bucket <root>
   --source <cat>/<file> --from <old-path> --to <new-path>`
   (one call per moved document per source row that names it).
```

- [ ] **Step 6: Commit**

```bash
git add skills/fusion-intake/scripts/convert.py skills/fusion-intake/tests/test_convert.py skills/fusion-intake/SKILL.md skills/fusion-librarian/references/restructure.md
git commit -m "intake: relink verb — repoint a MANIFEST library cell in place (frictions 12+14)"
```

---

### Task 2: W8 — a document that is only a summary

**Files:**
- Modify: `cli/src/fusion/document.py` (new `summary_only` field + helper; `read_document` sets it)
- Modify: `cli/src/fusion/checker.py` (`_w8_summary_only`, registered in `_warnings`; `Finding.code` comment `W1..W7` → `W1..W8`)
- Modify: `SPEC.md` §11 warnings list (item 8, after the W7 item ~line 387)
- Test: `cli/tests/test_document.py`, `cli/tests/test_checker_warnings.py`

**Interfaces:**
- Consumes: `iter_documents(root)` and the `Document` dataclass as-is.
- Produces: `Document.summary_only: bool` (default `False`); warning code `"W8"`.

- [ ] **Step 1: Write the failing tests**

Append to `cli/tests/test_checker_warnings.py`:

```python
SUMMARY_ONLY_DOC = """---
title: Stub
type: note
aurora: library
---

## Summary

A summary and nothing else.

---
"""


def test_w8_summary_only_document(make_bucket):
    root = make_bucket()
    (root / "library" / "stub.md").write_text(SUMMARY_ONLY_DOC,
                                              encoding="utf-8")
    found = [f for f in warnings(root) if f.code == "W8"]
    assert [f.path for f in found] == ["library/stub.md"]
    assert "only a summary" in found[0].message


def test_w8_silent_with_a_body(make_bucket):
    root = make_bucket()
    (root / "library" / "real.md").write_text(
        SUMMARY_ONLY_DOC + "\nBody text.\n", encoding="utf-8")
    assert not [f for f in warnings(root) if f.code == "W8"]


def test_w8_silent_when_not_summary_first(make_bucket):
    # a shapeless body is E5's territory — W8 must not double-flag it
    root = make_bucket()
    (root / "library" / "loose.md").write_text(
        "---\ntitle: L\ntype: note\naurora: library\n---\n\nJust prose.\n",
        encoding="utf-8")
    assert not [f for f in warnings(root) if f.code == "W8"]


def test_w8_silent_for_pointer_documents(make_bucket):
    # a converted scan's designed shape IS summary + source: pointer —
    # its body is the source file, not missing prose
    root = make_bucket()
    (root / "library" / "scan.md").write_text(
        SUMMARY_ONLY_DOC.replace(
            "aurora: library", "aurora: library\nsource: sources/records/scan.pdf"),
        encoding="utf-8")
    (root / "library" / "link.md").write_text(
        SUMMARY_ONLY_DOC.replace(
            "aurora: library", "aurora: library\nresource: https://example.com/x"),
        encoding="utf-8")
    assert not [f for f in warnings(root) if f.code == "W8"]
```

Append to `cli/tests/test_document.py` (imports at top of file already include `read_document` or a local equivalent — match the file's existing import style):

```python
def test_summary_only_field(tmp_path):
    p = tmp_path / "stub.md"
    p.write_text("---\ntitle: S\ntype: note\naurora: library\n---\n\n"
                 "## Summary\n\nOnly this.\n\n---\n", encoding="utf-8")
    assert read_document(p).summary_only is True
    p2 = tmp_path / "real.md"
    p2.write_text("---\ntitle: S\ntype: note\naurora: library\n---\n\n"
                  "## Summary\n\nLine.\n\n---\n\nBody.\n", encoding="utf-8")
    assert read_document(p2).summary_only is False
    p3 = tmp_path / "loose.md"
    p3.write_text("---\ntitle: S\ntype: note\naurora: library\n---\n\nProse.\n",
                  encoding="utf-8")
    assert read_document(p3).summary_only is False
```

- [ ] **Step 2: Run to verify failure**

Run: `cd cli && uv run --group dev pytest tests/test_document.py tests/test_checker_warnings.py -q -k "summary_only or w8"`
Expected: FAIL — `Document` has no attribute/field `summary_only`.

- [ ] **Step 3: Implement**

`document.py` — add to the `Document` dataclass, after `summary_line`:

```python
    summary_only: bool = False
```

Add after `_summary`:

```python
def _summary_only(body: str) -> bool:
    """True when the document is ONLY a summary — a summary-first shape
    with nothing but whitespace after the '---' that closes it (§4 wants
    a body below the separator; whether a stub deserves to exist is the
    operator's call, so the checker warns rather than errors: W8)."""
    lines = body.split("\n")
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i == len(lines) or lines[i].strip() != "## Summary":
        return False
    for j in range(i + 1, len(lines)):
        if lines[j].strip() == "---":
            return not "".join(lines[j + 1:]).strip()
    return False
```

In `read_document`, wherever the successful-parse `Document(...)` is constructed, add `summary_only=_summary_only(body)` (the error-path constructions keep the default `False`).

`checker.py` — register in `_warnings` after `_w7_large_tracked_files(root)`:

```python
    findings += _w8_summary_only(root)
```

Add after `_w7_large_tracked_files`:

```python
def _w8_summary_only(root: Path) -> list[Finding]:
    # A pointer document (source:/resource: in frontmatter) is exempt —
    # its designed shape IS summary + pointer; the body is the thing it
    # points at, not missing prose.
    return [
        Finding("warning", "W8", f"{zone}/{rel.as_posix()}",
                "document is only a summary — nothing beneath the closing "
                "separator and no source:/resource: pointer; write the "
                "body, point at the thing, or reconsider whether the "
                "document should exist")
        for zone, rel, doc in iter_documents(root)
        if doc.summary_first and doc.summary_only
        and not (doc.frontmatter or {}).get("source")
        and not (doc.frontmatter or {}).get("resource")
    ]
```

Update the `Finding` dataclass's `code` comment from `E1..E8, W1..W7` to `E1..E8, W1..W8`.

- [ ] **Step 4: Run the CLI suite**

Run: `cd cli && uv run --group dev pytest -q`
Expected: PASS, no regressions (the `make_bucket` fixture's own docs all carry bodies).

- [ ] **Step 5: SPEC §11** — after the W7 list item (~line 387), add:

```
8. A document that is only a summary — nothing beneath the `---` line
   that closes it (§4) — and whose frontmatter carries neither `source:`
   nor `resource:`. Pointer documents are exempt: a converted scan's
   designed shape IS summary + pointer. A warning, not an error: whether
   a stub deserves to exist is operator judgment, and a stub that
   carries boilerplate text is a semantic call no checker should fake.
```

- [ ] **Step 6: Commit**

```bash
git add cli/src/fusion/document.py cli/src/fusion/checker.py cli/tests/test_document.py cli/tests/test_checker_warnings.py SPEC.md
git commit -m "checker: W8 summary-only documents — a vacuous doc is flagged, not failed (friction 17)"
```

---

### Task 3: docs — a bucket meets its remote; the `source:` convention

**Files:**
- Modify: `docs/BUCKETS-EVERYWHERE.md` ("One bucket, two machines", the remote passage ~line 58)
- Modify: `SPEC.md` §4 (after the frontmatter example block, ~line 165)

**Interfaces:** none — documentation only. No code, no tests; the QA bar is the newcomer cold-read (each addition must be executable/checkable as written).

- [ ] **Step 1: BUCKETS-EVERYWHERE** — replace the passage

```
Give the bucket a private remote and it travels like any repo:
```

and its bash block with:

````
Give the bucket a private remote and it travels like any repo. Create
the remote **empty** — no README, no .gitignore, no license: the bucket
was born with its own history, and any scaffold commit on the remote
means your first push is rejected.

```bash
cd ~/buckets/studio
git remote add origin git@github.com:you/studio-bucket.git
git push -u origin main
```

Already created the remote with a scaffold README? It holds one commit
your bucket has never seen. Join the two histories once — and never
force-push a bucket, the remote may know things this machine does not:

```bash
git fetch origin
git merge origin/main --allow-unrelated-histories --no-edit
git push -u origin main
```

The merge usually completes on its own (the scaffold's files don't
overlap the bucket's). If it stops on a conflict — you added your own
README, say — keep the bucket's version and finish the merge:

```bash
git checkout --ours README.md && git add README.md
git commit --no-edit
git push -u origin main
```
````

(Keep everything after the original bash block — the union-driver paragraph onward — unchanged.)

- [ ] **Step 2: SPEC §4** — insert immediately BEFORE the `**Summary-first, always:**` paragraph (SPEC.md ~line 195, after the Required/Optional field tables — NOT at ~line 165, which is inside the fenced example):

```
`source:` names the `sources/` original a document was converted from —
a single path. A document reconciled from **multiple** originals (a
confirmed merge of two copies of the same record) may carry a list, one
`sources/` path per original. Anything else stays a string.
```

- [ ] **Step 3: Cold-read check**

Run: `grep -n "allow-unrelated-histories" docs/BUCKETS-EVERYWHERE.md && grep -n "multiple" SPEC.md`
Expected: both hits present; read each addition once in place for flow.

- [ ] **Step 4: Commit**

```bash
git add docs/BUCKETS-EVERYWHERE.md SPEC.md
git commit -m "docs: remote first-contact recipe + source: string-or-list convention (frictions 15+16)"
```

---

### Task 4: v1.4.0 + friction dispositions

**Files:**
- Modify: `cli/pyproject.toml` (line 3: `version = "1.3.2"` → `version = "1.4.0"`)
- Modify: `docs/dogfood/frictions.md` (rows 12, 14, 16, 17 dispositions)

**Interfaces:**
- Consumes: the commit hashes of Tasks 1–3 (run `git log --oneline -3` and use the real short hashes).

- [ ] **Step 1: Bump the version**

In `cli/pyproject.toml`: `version = "1.4.0"`. (`fusion.__version__` reads package metadata — no second edit exists.)

- [ ] **Step 2: Flip the dispositions** in `docs/dogfood/frictions.md`, keeping each row's friction text untouched:

- Row 12: `**backlog** — needs a proper CLI/skill verb …` → `**fixed** — \`convert.py relink\` (<task-1-hash>, v1.4.0) repoints a MANIFEST library cell in place; see row 14`
- Row 14: replace `**build this session** — …` with `**fixed** — \`convert.py relink\` shipped on the single writer (<task-1-hash>): row/old-value/target-exists assertions, multi-value cells preserved; SKILL.md + restructure.md carry the protocol. The 7flows room-era provenance blocks stay as-is (history is history)`
- Row 16: replace `**standardized this session** — …` with `**standardized** — SPEC §4 (<task-3-hash>): \`source:\` is a string; a list only for a doc reconciled from multiple originals. The 2 live docs already conform`
- Row 17: replace `**build this session** — …` with `**fixed** — checker W8 (<task-2-hash>, v1.4.0): a summary-only document with no \`source:\`/\`resource:\` pointer (nothing beneath the closing separator) warns, never errors; SPEC §11 item 8. The pointer exemption is deliberate — a converted scan's designed shape IS summary + pointer (72 such docs in family-business stay silent, verified live). Boundary held: boilerplate stubs WITH text remain operator judgment`

- [ ] **Step 3: Full test sweep**

Run all three suite commands from Global Constraints.
Expected: all PASS.

- [ ] **Step 4: Commit** (`cli/uv.lock` is rewritten by the Step-3 `uv run` after the version bump — every prior release commit includes it)

```bash
git add cli/pyproject.toml cli/uv.lock docs/dogfood/frictions.md
git commit -m "release: fusion v1.4.0 — relink, W8, remote recipe, source: convention"
```

---

## Deploy & verify (controller, not a subagent task)

1. `uv cache clean fusion-cli && uv tool install --reinstall --from ~/Developer/fusion/cli fusion-cli` → `fusion --version` prints `fusion 1.4.0`.
2. `fusion setup` re-fans the skills; verify `grep -n "def relink" ~/.agents/skills/fusion-intake/scripts/convert.py` hits.
3. Live proof, W6/W7-style: scratch probe bucket — a summary-only doc fires W8; `relink` on a probe MANIFEST row round-trips; then `fusion check` on all five real buckets + `fusion check --hub` stay at zero warnings.
4. Push `~/Developer/fusion` main; confirm CI green.
