"""setup core: payload resolution, canonical install, digests."""

from pathlib import Path


from fusion import setup


def make_payload(root: Path, names=("fusion-intake", "fusion-librarian")) -> Path:
    for name in names:
        d = root / name
        (d / "references").mkdir(parents=True)
        (d / "SKILL.md").write_text(f"---\nname: {name}\n---\nbody\n")
        (d / "references" / "guide.md").write_text("guide\n")
    return root


def test_payload_root_prefers_bundled_then_repo():
    # in the dev checkout there is no _skills package dir, so the repo
    # skills/ fallback resolves — and it contains the four real skills
    root = setup.payload_root()
    assert sorted(p.name for p in root.glob("fusion-*")) == [
        "fusion-analyst",
        "fusion-intake",
        "fusion-librarian",
        "fusion-planner",
    ]


def test_tree_digest_stable_and_content_sensitive(tmp_path):
    a = make_payload(tmp_path / "a")
    b = make_payload(tmp_path / "b")
    d1 = setup.tree_digest(a / "fusion-intake")
    assert d1 == setup.tree_digest(b / "fusion-intake")
    (b / "fusion-intake" / "SKILL.md").write_text("changed")
    assert d1 != setup.tree_digest(b / "fusion-intake")


def test_install_canonical_fresh(tmp_path):
    payload = make_payload(tmp_path / "payload")
    dest = tmp_path / "agents-skills"
    results = setup.install_canonical(payload, dest, force=False)
    assert {r["skill"]: r["action"] for r in results} == {
        "fusion-intake": "installed",
        "fusion-librarian": "installed",
    }
    assert (dest / "fusion-intake" / "references" / "guide.md").read_text() == "guide\n"


def test_install_canonical_refreshes_and_reports_upgrade(tmp_path):
    payload = make_payload(tmp_path / "payload")
    dest = tmp_path / "agents-skills"
    setup.install_canonical(payload, dest, force=False)
    (dest / "fusion-intake" / "SKILL.md").write_text("stale")
    results = setup.install_canonical(payload, dest, force=False)
    by = {r["skill"]: r["action"] for r in results}
    assert by["fusion-intake"] == "updated"
    assert by["fusion-librarian"] == "up-to-date"
    assert (dest / "fusion-intake" / "SKILL.md").read_text().startswith("---")


def test_install_canonical_leaves_plain_file_unless_forced(tmp_path):
    payload = make_payload(tmp_path / "payload")
    dest = tmp_path / "agents-skills"
    dest.mkdir()
    (dest / "fusion-intake").write_text("not a skill, just a file\n")
    results = setup.install_canonical(payload, dest, force=False)
    by = {r["skill"]: r["action"] for r in results}
    assert by["fusion-intake"] == "left"
    assert (dest / "fusion-intake").is_file()
    assert not (dest / "fusion-intake").is_dir()
    # --force replaces it with a real dir
    results = setup.install_canonical(payload, dest, force=True)
    by = {r["skill"]: r["action"] for r in results}
    assert by["fusion-intake"] == "replaced"
    assert (dest / "fusion-intake").is_dir()
    assert (dest / "fusion-intake" / "references" / "guide.md").read_text() == "guide\n"


def test_install_canonical_leaves_foreign_symlink(tmp_path):
    payload = make_payload(tmp_path / "payload")
    dest = tmp_path / "agents-skills"
    dest.mkdir()
    theirs = tmp_path / "their-clone" / "fusion-intake"
    theirs.mkdir(parents=True)
    (dest / "fusion-intake").symlink_to(theirs)
    results = setup.install_canonical(payload, dest, force=False)
    by = {r["skill"]: r["action"] for r in results}
    assert by["fusion-intake"] == "left"
    assert (dest / "fusion-intake").is_symlink()
    # --force replaces it with a real dir
    results = setup.install_canonical(payload, dest, force=True)
    by = {r["skill"]: r["action"] for r in results}
    assert by["fusion-intake"] == "replaced"
    assert not (dest / "fusion-intake").is_symlink()
