from datetime import datetime

import pytest

from fusion import hub, ledger
from fusion.checker import check
from fusion.scaffold import ScaffoldError, new_bucket


@pytest.fixture(autouse=True)
def tmp_hub(tmp_path, monkeypatch):
    monkeypatch.setenv("FUSION_HUB", str(tmp_path / "hub.md"))


def test_new_bucket_is_conformant(tmp_path):
    root, warnings = new_bucket(
        tmp_path / "studio", kind="studio",
        description="Music and gear.", actor="claude",
        at=datetime(2026, 7, 10, 9, 0),
    )
    assert check(root) == []          # zero errors, zero warnings, day one
    for zone in ("inbox", "workbench", "output"):
        assert (root / zone / ".gitkeep").exists()
    assert (root / "sources" / "MANIFEST.md").exists()
    assert (root / "library" / "INDEX.md").exists()
    entries = ledger.read(root)
    assert len(entries) == 1
    assert (entries[0].verb, entries[0].obj, entries[0].note) == (
        "created", "BUCKET.md", "bucket born"
    )
    assert (root / ".git").is_dir()
    card = (root / "BUCKET.md").read_text(encoding="utf-8")
    assert "name: studio" in card and 'fusion_version: "1.0"' in card
    assert "## Conventions" in card


def test_new_bucket_registers_in_hub(tmp_path):
    new_bucket(tmp_path / "studio", description="d", actor="claude")
    assert [e.name for e in hub.load()] == ["studio"]


def test_new_bucket_refuses_non_empty_target(tmp_path):
    target = tmp_path / "busy"
    target.mkdir()
    (target / "file.txt").write_text("x", encoding="utf-8")
    with pytest.raises(ScaffoldError, match="not empty"):
        new_bucket(target, actor="claude")


def test_new_bucket_refuses_file_target(tmp_path):
    target = tmp_path / "afile"
    target.write_text("x", encoding="utf-8")
    with pytest.raises(ScaffoldError, match="not a directory"):
        new_bucket(target, actor="claude")


def test_new_bucket_refuses_taken_name(tmp_path):
    new_bucket(tmp_path / "studio", description="d", actor="claude")
    with pytest.raises(ScaffoldError, match="already registered"):
        new_bucket(tmp_path / "elsewhere", name="studio",
                   description="d", actor="claude")


HOSTILE_DESCRIPTIONS = [
    "Music: gear, #1 priority — 100% real",
    # sentence-length prose crosses PyYAML's default 80-column wrap width
    "A long description of my studio bucket: microphones, preamps, "
    "compressors, cables, and everything else that lives in the racks "
    "upstairs, plus the tape machines.",
    "first line\nsecond line",
]


def test_new_bucket_conformant_with_hostile_description(tmp_path):
    from fusion import bucket
    for i, description in enumerate(HOSTILE_DESCRIPTIONS):
        root, _ = new_bucket(
            tmp_path / f"tricky-{i}", description=description, actor="claude",
        )
        assert check(root) == []
        assert bucket.load(root).description == description


def test_hub_path_contraction_respects_boundaries(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "bertrand"))
    (tmp_path / "bertrand").mkdir()
    new_bucket(tmp_path / "bertrand" / "inside", description="d", actor="c")
    new_bucket(tmp_path / "bertrand2" / "outside", description="d", actor="c")
    paths = {e.name: e.path for e in hub.load()}
    assert paths["inside"] == "~/inside"
    assert paths["outside"] == str(tmp_path / "bertrand2" / "outside")


def test_hub_failure_is_a_warning_not_an_error(tmp_path, monkeypatch):
    def boom(entry):
        raise ValueError("hub on fire")
    monkeypatch.setattr(hub, "add", boom)
    root, warnings = new_bucket(tmp_path / "b", description="d", actor="c")
    assert root.exists()
    assert any("hub registration failed" in w for w in warnings)
