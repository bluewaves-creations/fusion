from pathlib import Path

import pytest

from fusion import bucket, hub, manifest


HUB_TEXT = """# Fusion Hub

- **personal** · personal · ~/Fusion/personal — life, training, the wide-open days
- **studio** · studio · /tmp/studio — music — photography — instruments
"""


@pytest.fixture
def tmp_hub(tmp_path, monkeypatch):
    path = tmp_path / "hub.md"
    monkeypatch.setenv("FUSION_HUB", str(path))
    return path


def test_hub_parse_grammar(tmp_hub):
    tmp_hub.write_text(HUB_TEXT, encoding="utf-8")
    entries = hub.load()
    assert [e.name for e in entries] == ["personal", "studio"]
    assert entries[0].kind == "personal"
    assert entries[0].path == "~/Fusion/personal"
    # description keeps its own em dashes — split happens on the FIRST separator
    assert entries[1].description == "music — photography — instruments"


def test_hub_missing_file_is_empty(tmp_hub):
    assert hub.load() == []


def test_hub_add_save_remove(tmp_hub):
    hub.add(hub.HubEntry("studio", "studio", "/tmp/studio", "the studio"))
    assert [e.name for e in hub.load()] == ["studio"]
    with pytest.raises(ValueError, match="already registered"):
        hub.add(hub.HubEntry("studio", "club", "/elsewhere", "dupe"))
    assert hub.remove("studio") is True
    assert hub.remove("studio") is False
    assert hub.load() == []


def test_hub_save_never_writes_multiline_entries(tmp_hub):
    forged = "desc\n- **evil** · personal · /tmp/evil — forged"
    hub.add(hub.HubEntry("good", "personal", "/tmp/good", forged))
    entries = hub.load()
    assert [e.name for e in entries] == ["good"]
    assert "evil" not in tmp_hub.read_text(encoding="utf-8").split(" — ")[0]


def test_manifest_fixture(fixture_bucket):
    rows = manifest.read(fixture_bucket)
    assert len(rows) == 1
    row = rows[0]
    assert row.file == "gear/pedalboard-inventory.csv"
    assert row.sha256 == "8462022317d2d07b"
    assert row.library == "library/instruments/pedalboard.md"


def test_manifest_missing_is_empty(tmp_path):
    assert manifest.read(tmp_path) == []


def test_find_root(fixture_bucket):
    nested = fixture_bucket / "library" / "instruments"
    assert bucket.find_root(nested) == fixture_bucket
    assert bucket.find_root(Path("/")) is None


def test_load_bucket(fixture_bucket):
    b = bucket.load(fixture_bucket)
    assert b.name == "crazy-ones"
    assert b.kind == "studio"
    assert b.inbox_max_age_days == 7


def test_iter_documents_fixture(fixture_bucket):
    docs = list(bucket.iter_documents(fixture_bucket))
    assert len(docs) == 7
    from collections import Counter
    zone_counts = Counter(zone for zone, _, _ in docs)
    assert zone_counts == {"library": 3, "activities": 3, "output": 1}
    names = {rel.name for _, rel, _ in docs}
    assert "INDEX.md" not in names
    # yields (zone, path relative to the zone, Document)
    rels = sorted(rel.as_posix() for zone, rel, _ in docs if zone == "library")
    assert rels == [
        "instruments/jazzmaster-1962.md",
        "instruments/pedalboard.md",
        "recipes/tape-echo-settings.md",
    ]


def test_iter_documents_skips_dot_directories(tmp_path):
    lib = tmp_path / "library" / ".obsidian"
    lib.mkdir(parents=True)
    (lib / "workspace.md").write_text("junk", encoding="utf-8")
    (tmp_path / "library" / "real.md").write_text(
        "---\ntitle: Real\ntype: note\naurora: library\n---\n\n"
        "## Summary\n\nReal.\n\n---\n\nBody.\n", encoding="utf-8")
    rels = [rel.as_posix() for _, rel, _ in bucket.iter_documents(tmp_path)]
    assert rels == ["real.md"]
