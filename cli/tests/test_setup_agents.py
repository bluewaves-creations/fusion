"""Agent detection, fan-out, and the attribution-checked remove."""
from pathlib import Path

import pytest

from fusion import setup
from tests.test_setup_core import make_payload


@pytest.fixture
def home(tmp_path) -> Path:
    return tmp_path


@pytest.fixture
def canonical(home) -> Path:
    payload = make_payload(home / "_payload")
    dest = home / ".agents" / "skills"
    setup.install_canonical(payload, dest, force=False)
    return dest


def test_registry_shape():
    names = {a["name"] for a in setup.AGENTS}
    assert {"Claude Code", "Codex", "Pi", "Cursor", "Gemini CLI",
            "opencode", "Goose"} == names
    modes = {a["name"]: a["mode"] for a in setup.AGENTS}
    assert modes["Claude Code"] == "link"
    assert modes["Cursor"] == "standard"


def test_detect_agents_only_present(home):
    (home / ".claude").mkdir()
    (home / ".config" / "goose").mkdir(parents=True)
    found = {a["name"] for a in setup.detect_agents(home)}
    assert found == {"Claude Code", "Goose"}


def test_fan_out_links_link_agents_and_reports_standard(home, canonical):
    (home / ".claude").mkdir()
    (home / ".cursor").mkdir()
    results = setup.fan_out(canonical, setup.detect_agents(home), force=False)
    claude = [r for r in results if r["agent"] == "Claude Code"]
    assert {r["action"] for r in claude} == {"linked"}
    link = home / ".claude" / "skills" / "fusion-intake"
    assert link.is_symlink() and link.resolve() == (canonical / "fusion-intake").resolve()
    cursor = [r for r in results if r["agent"] == "Cursor"]
    assert len(cursor) == 1 and cursor[0]["action"] == "standard"
    # idempotent re-run
    again = setup.fan_out(canonical, setup.detect_agents(home), force=False)
    assert {r["action"] for r in again if r["agent"] == "Claude Code"} == {"up-to-date"}


def test_fan_out_leaves_foreign_dir_unless_forced(home, canonical):
    foreign = home / ".claude" / "skills" / "fusion-intake"
    foreign.mkdir(parents=True)
    (foreign / "SKILL.md").write_text("---\nname: my-own-tool\n---\n")
    (foreign / "data.txt").write_text("do not touch\n")
    results = setup.fan_out(canonical, setup.detect_agents(home), force=False)
    intake = [r for r in results if r["skill"] == "fusion-intake"][0]
    assert intake["action"] == "left"
    assert (foreign / "data.txt").read_text() == "do not touch\n"
    assert (foreign / "SKILL.md").read_text() == "---\nname: my-own-tool\n---\n"
    results = setup.fan_out(canonical, setup.detect_agents(home), force=True)
    intake = [r for r in results if r["skill"] == "fusion-intake"][0]
    assert intake["action"] == "replaced"
    assert (home / ".claude" / "skills" / "fusion-intake").is_symlink()


def test_fan_out_standard_mode_warns_when_canonical_is_custom(home):
    payload = make_payload(home / "_payload")
    custom_canonical = home / "custom-skills"
    setup.install_canonical(payload, custom_canonical, force=False)
    (home / ".cursor").mkdir()
    results = setup.fan_out(custom_canonical, setup.detect_agents(home),
                            force=False)
    cursor = [r for r in results if r["agent"] == "Cursor"][0]
    assert cursor["action"] == "standard"
    assert "does not read" in cursor["detail"]


def test_fan_out_leaves_plain_file_unless_forced(home, canonical):
    skills_dir = home / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "fusion-intake").write_text("just a file\n")
    results = setup.fan_out(canonical, setup.detect_agents(home), force=False)
    intake = [r for r in results if r["agent"] == "Claude Code"
             and r["skill"] == "fusion-intake"][0]
    assert intake["action"] == "left"
    assert (skills_dir / "fusion-intake").is_file()
    assert not (skills_dir / "fusion-intake").is_symlink()
    results = setup.fan_out(canonical, setup.detect_agents(home), force=True)
    intake = [r for r in results if r["agent"] == "Claude Code"
             and r["skill"] == "fusion-intake"][0]
    assert intake["action"] == "replaced"
    assert (skills_dir / "fusion-intake").is_symlink()


def test_fan_out_copies_when_symlink_unavailable(home, canonical, monkeypatch):
    (home / ".pi").mkdir()

    def no_symlink(*a, **k):
        raise OSError("symlinks disabled")
    monkeypatch.setattr(setup.os, "symlink", no_symlink)
    results = setup.fan_out(canonical, setup.detect_agents(home), force=False)
    pi = [r for r in results if r["agent"] == "Pi"]
    assert {r["action"] for r in pi} == {"copied"}
    copied = home / ".pi" / "agent" / "skills" / "fusion-intake"
    assert copied.is_dir() and not copied.is_symlink()
    # the copy carries a provenance sentinel — that's how we know it's ours
    sentinel = copied / ".fusion-setup"
    assert sentinel.is_file()
    assert sentinel.read_text().splitlines()[1] == setup.tree_digest(
        canonical / "fusion-intake")
    # a stale copy refreshes on re-run, recognized via the sentinel branch
    # (a copy can never digest-equal the canonical skill — the sentinel
    # itself is an extra file — so the sentinel is what proves provenance)
    (copied / "SKILL.md").write_text("stale")
    again = setup.fan_out(canonical, setup.detect_agents(home), force=False)
    pi_intake = [r for r in again if r["skill"] == "fusion-intake"][0]
    assert pi_intake["action"] == "copied"
    assert (copied / ".fusion-setup").is_file()


def test_remove_all_is_attribution_checked(home, canonical):
    (home / ".claude").mkdir()
    setup.fan_out(canonical, setup.detect_agents(home), force=False)
    foreign = home / ".claude" / "skills" / "fusion-mine"
    foreign.mkdir()
    results = setup.remove_all(canonical, home)
    assert foreign.is_dir()                      # not ours — untouched
    assert not (home / ".claude" / "skills" / "fusion-intake").exists()
    assert not (canonical / "fusion-intake").exists()
    assert any(r["action"] == "removed" for r in results)


def test_remove_all_removes_sentinel_copies_and_leaves_foreign(
        home, canonical, monkeypatch):
    (home / ".pi").mkdir()

    def no_symlink(*a, **k):
        raise OSError("symlinks disabled")
    monkeypatch.setattr(setup.os, "symlink", no_symlink)
    setup.fan_out(canonical, setup.detect_agents(home), force=False)
    ours = home / ".pi" / "agent" / "skills" / "fusion-intake"
    assert (ours / ".fusion-setup").is_file()     # our sentinel-marked copy

    # a foreign dir sharing a canonical skill's name — same shape, no
    # sentinel, different content — must survive removal untouched, even
    # discovered fresh (this agent never went through fan_out)
    (home / ".claude").mkdir()
    foreign = home / ".claude" / "skills" / "fusion-intake"
    foreign.mkdir(parents=True)
    (foreign / "SKILL.md").write_text("---\nname: my-own-tool\n---\n")
    (foreign / "data.txt").write_text("do not touch\n")

    results = setup.remove_all(canonical, home)

    assert not ours.exists()                      # our copy: removed
    pi_result = [r for r in results
                 if r["agent"] == "Pi" and r["skill"] == "fusion-intake"][0]
    assert pi_result["action"] == "removed"

    assert foreign.is_dir()                        # foreign: left in place
    assert (foreign / "data.txt").read_text() == "do not touch\n"
    claude_result = [r for r in results
                      if r["agent"] == "Claude Code"
                      and r["skill"] == "fusion-intake"][0]
    assert claude_result["action"] == "left"


def test_fan_out_survives_skills_dir_symlinked_to_canonical(home, canonical):
    # the topology that destroyed skills in v1.1.0-v1.2.0: the agent's
    # whole skills dir is a symlink AT the canonical directory
    (home / ".claude").mkdir()
    (home / ".claude" / "skills").symlink_to(
        canonical, target_is_directory=True)
    results = setup.fan_out(canonical, setup.detect_agents(home),
                            force=False)
    claude = [r for r in results if r["agent"] == "Claude Code"]
    assert len(claude) == 1 and claude[0]["action"] == "served"
    # the canonical skills are alive, real, and readable
    assert (canonical / "fusion-intake" / "SKILL.md").is_file()
    assert not (canonical / "fusion-intake").is_symlink()


def test_remove_all_survives_skills_dir_symlinked_to_canonical(
        home, canonical):
    (home / ".claude").mkdir()
    (home / ".claude" / "skills").symlink_to(
        canonical, target_is_directory=True)
    setup.remove_all(canonical, home)
    # the canonical phase removed the skills exactly once; the user's
    # own dir-level symlink is not ours and stays
    assert not (canonical / "fusion-intake").exists()
    assert (home / ".claude" / "skills").is_symlink()
