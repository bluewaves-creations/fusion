import pytest

from fusion import views
from fusion.ledger import Entry


def test_status_fixture(fixture_bucket):
    s = views.status(fixture_bucket)
    assert s["bucket"] == "crazy-ones"
    assert s["documents"] == 7
    assert s["auroras"] == {"archive": 1, "collab": 1, "focus": 2, "library": 3}
    assert s["types"] == {"instrument": 2, "plan": 3, "press-kit": 1, "recipe": 1}
    assert s["activities"] == {"active": 2, "done": 1}
    assert len(s["ledger"]) == 10  # last ten of nineteen
    assert s["ledger"][-1]["verb"] == "reflected"


def test_status_since_date(fixture_bucket):
    s = views.status(fixture_bucket, since="2026-07-10")
    assert len(s["ledger"]) == 7
    assert all(e["date"] == "2026-07-10" for e in s["ledger"])


def test_filter_since_last_reflection():
    entries = [
        Entry("2026-07-01", "09:00", "t", "created", "a"),
        Entry("2026-07-01", "10:00", "t", "reflected", "bucket"),
        Entry("2026-07-02", "09:00", "t", "noted", "b"),
    ]
    assert [e.obj for e in views.filter_since(entries, "last-reflection")] == ["b"]
    # no reflection yet → everything
    assert len(views.filter_since(entries[:1], "last-reflection")) == 1


ACTIVE_PLAN = """---
title: {title}
type: plan
aurora: {aurora}
status: active
{extra}---

## Summary

{title}.

---

Body.
"""


@pytest.fixture
def two_bucket_hub(tmp_path, monkeypatch):
    from fusion.scaffold import new_bucket

    monkeypatch.setenv("FUSION_HUB", str(tmp_path / "hub.md"))
    for name, plans in {
        "studio": [("lp", "LP", "focus", "")],
        "pro": [
            ("client", "Client Call", "commitments", "due: 2026-07-12\n"),
            ("ship", "Ship It", "focus", "date: 2026-07-11\n"),
        ],
    }.items():
        root, _ = new_bucket(tmp_path / name, description="d", actor="test")
        for slug, title, aurora, extra in plans:
            plan = root / "activities" / slug / "plan.md"
            plan.parent.mkdir()
            plan.write_text(
                ACTIVE_PLAN.format(title=title, aurora=aurora, extra=extra),
                encoding="utf-8",
            )
    return tmp_path


def test_today_composes_across_buckets(two_bucket_hub):
    t = views.today()
    assert set(t["buckets"]) == {"studio", "pro"}
    # canonical aurora order: commitments before focus
    assert list(t["groups"]) == ["commitments", "focus"]
    focus_titles = {i["title"] for i in t["groups"]["focus"]}
    assert focus_titles == {"LP", "Ship It"}
    commit = t["groups"]["commitments"][0]
    assert commit["bucket"] == "pro" and commit["title"] == "Client Call"
    assert commit["path"] == "activities/client/plan.md"


def test_agenda_dated_sorted_then_active(two_bucket_hub):
    a = views.agenda()
    assert [i["title"] for i in a["dated"]] == ["Ship It", "Client Call"]
    assert [i["date"] for i in a["dated"]] == ["2026-07-11", "2026-07-12"]
    assert [i["title"] for i in a["active"]] == ["LP"]


def test_today_lists_empty_buckets_as_read(tmp_path, monkeypatch):
    from fusion.scaffold import new_bucket

    monkeypatch.setenv("FUSION_HUB", str(tmp_path / "hub.md"))
    new_bucket(tmp_path / "emptybucket", description="d", actor="test")
    t = views.today()
    assert t["buckets"] == ["emptybucket"]  # read, even with zero documents
    assert t["groups"] == {}


def test_today_skips_hub_entries_without_bucket(tmp_path, monkeypatch):
    from fusion import hub

    monkeypatch.setenv("FUSION_HUB", str(tmp_path / "hub.md"))
    hub.add(hub.HubEntry("ghost", "personal", str(tmp_path / "gone"), "missing"))
    t = views.today()
    assert t["buckets"] == []
    assert t["missing"] == [
        {"name": "ghost", "path": str(tmp_path / "gone")}
    ]


def test_views_exclude_archive_aurora_off_archive_paths(two_bucket_hub):
    """A document with aurora: archive should be excluded from today() and
    agenda() even if it's not on an archive/ path."""
    # Add a mislabeled document with aurora: archive in activities/mislabeled/
    root = two_bucket_hub / "studio"
    plan_dir = root / "activities" / "mislabeled"
    plan_dir.mkdir()
    doc = ("---\ntitle: Mislabeled\ntype: plan\naurora: archive\n"
           "status: active\n---\n\n## Summary\n\nShould not compose.\n\n---\n\nBody.\n")
    (plan_dir / "plan.md").write_text(doc, encoding="utf-8")

    # Check that it does not appear in today()
    everything = [i["path"] for items in views.today()["groups"].values() for i in items]
    assert not any("mislabeled" in p for p in everything)

    # Check that it does not appear in agenda()
    assert not any("mislabeled" in i["path"] for i in views.agenda()["active"])
