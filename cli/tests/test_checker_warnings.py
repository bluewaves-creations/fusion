import os
import time

from fusion.checker import check


def warnings(root):
    return [f for f in check(root) if f.level == "warning"]


def wcodes(root):
    return {f.code for f in warnings(root)}


def test_fixture_has_zero_warnings(fixture_bucket):
    assert warnings(fixture_bucket) == []


def test_scratch_bucket_has_zero_warnings(make_bucket):
    assert warnings(make_bucket()) == []


def test_w1_stale_inbox_and_dotfile_exemption(make_bucket):
    root = make_bucket()
    stale = root / "inbox" / "forgotten.pdf"
    stale.write_text("x", encoding="utf-8")
    keep = root / "inbox" / ".gitkeep"
    keep.write_text("", encoding="utf-8")
    ten_days_ago = time.time() - 10 * 86400
    os.utime(stale, (ten_days_ago, ten_days_ago))
    os.utime(keep, (ten_days_ago, ten_days_ago))
    found = warnings(root)
    assert any(f.code == "W1" and "forgotten.pdf" in f.path for f in found)
    assert not any(".gitkeep" in f.path for f in found)


def test_w2_missing_and_stale_index(make_bucket):
    root = make_bucket()
    (root / "activities" / "INDEX.md").unlink()
    assert any(f.code == "W2" and f.path == "activities/INDEX.md"
               and "missing" in f.message for f in warnings(root))
    root2 = make_bucket("scratch2")
    (root2 / "library" / "INDEX.md").write_text("stale bytes\n", encoding="utf-8")
    assert any(f.code == "W2" and f.path == "library/INDEX.md"
               and "stale" in f.message for f in warnings(root2))


ARCHIVED_DOC = """---
title: Old
type: note
aurora: {aurora}
---

## Summary

Old thing.

---

Body.
"""


def test_w3_path_aurora_disagreement(make_bucket):
    root = make_bucket()
    target = root / "library" / "archive" / "old.md"
    target.parent.mkdir()
    target.write_text(ARCHIVED_DOC.format(aurora="library"), encoding="utf-8")
    live = root / "library" / "not-done.md"
    live.write_text(ARCHIVED_DOC.format(aurora="archive"), encoding="utf-8")
    found = [f for f in warnings(root) if f.code == "W3"]
    paths = {f.path for f in found}
    assert paths == {"library/archive/old.md", "library/not-done.md"}


def test_w4_broken_relative_link(make_bucket):
    root = make_bucket()
    doc = root / "library" / "linked.md"
    doc.write_text(
        "---\ntitle: L\ntype: note\naurora: library\n---\n\n"
        "## Summary\n\nLinks out.\n\n---\n\n"
        "A [good](notes.md) link, a [bad](missing.md) link, "
        "an [outside](https://example.com/) one.\n",
        encoding="utf-8",
    )
    found = [f for f in warnings(root) if f.code == "W4"]
    assert len(found) == 1
    assert "missing.md" in found[0].message and found[0].path == "library/linked.md"


ACTIVE_PLAN = """---
title: Plan
type: plan
aurora: focus
status: active
---

## Summary

An active plan.

---

Body.
"""

LEDGER_TWO_REFLECTIONS = """# Ledger

## 2026-06-25
- 09:00 · test · created · BUCKET.md — "bucket born"
- 09:10 · test · created · activities/quiet/plan.md
- 09:20 · test · created · activities/busy/plan.md

## 2026-07-01
- 10:00 · test · reflected · bucket

## 2026-07-08
- 09:30 · test · noted · activities/busy/plan.md — "touched"
- 10:00 · test · reflected · bucket
"""
# The window between the two reflections mentions only `busy` —
# `quiet` was created BEFORE the first reflection and never touched since.


def test_w5_active_activity_unmentioned_between_reflections(make_bucket):
    root = make_bucket()
    for name in ("quiet", "busy"):
        plan = root / "activities" / name / "plan.md"
        plan.parent.mkdir()
        plan.write_text(ACTIVE_PLAN, encoding="utf-8")
    (root / "LEDGER.md").write_text(LEDGER_TWO_REFLECTIONS, encoding="utf-8")
    # regenerate the activities INDEX so W2 stays quiet
    from fusion import indexer
    indexer.write_indexes(root)
    found = [f for f in warnings(root) if f.code == "W5"]
    assert [f.path for f in found] == ["activities/quiet/plan.md"]


def test_w5_never_triggers_below_two_reflections(make_bucket):
    root = make_bucket()
    plan = root / "activities" / "quiet" / "plan.md"
    plan.parent.mkdir()
    plan.write_text(ACTIVE_PLAN, encoding="utf-8")
    from fusion import indexer
    indexer.write_indexes(root)
    assert "W5" not in wcodes(root)


def test_w5_applies_on_archive_paths_too(make_bucket):
    root = make_bucket()
    plan = root / "activities" / "archive" / "quiet" / "plan.md"
    plan.parent.mkdir(parents=True)
    plan.write_text(ACTIVE_PLAN.replace("aurora: focus", "aurora: archive"),
                    encoding="utf-8")
    (root / "LEDGER.md").write_text(LEDGER_TWO_REFLECTIONS, encoding="utf-8")
    from fusion import indexer
    indexer.write_indexes(root)
    found = [f for f in warnings(root) if f.code == "W5"]
    assert [f.path for f in found] == ["activities/archive/quiet/plan.md"]


def test_w5_directory_mention_suppresses(make_bucket):
    root = make_bucket()
    plan = root / "activities" / "quiet" / "plan.md"
    plan.parent.mkdir()
    plan.write_text(ACTIVE_PLAN, encoding="utf-8")
    ledger_text = LEDGER_TWO_REFLECTIONS.replace(
        '- 09:30 · test · noted · activities/busy/plan.md — "touched"',
        "- 09:30 · test · indexed · activities/quiet/ (1 document)",
    )
    (root / "LEDGER.md").write_text(ledger_text, encoding="utf-8")
    from fusion import indexer
    indexer.write_indexes(root)
    assert not [f for f in warnings(root) if f.code == "W5"]
