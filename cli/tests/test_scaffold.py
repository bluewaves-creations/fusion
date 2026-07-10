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


def test_new_bucket_refuses_taken_name(tmp_path):
    new_bucket(tmp_path / "studio", description="d", actor="claude")
    with pytest.raises(ScaffoldError, match="already registered"):
        new_bucket(tmp_path / "elsewhere", name="studio",
                   description="d", actor="claude")
