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
    (home / ".claude" / "skills" / "fusion-intake").mkdir(parents=True)
    results = setup.fan_out(canonical, setup.detect_agents(home), force=False)
    intake = [r for r in results if r["skill"] == "fusion-intake"][0]
    assert intake["action"] == "left"
    results = setup.fan_out(canonical, setup.detect_agents(home), force=True)
    intake = [r for r in results if r["skill"] == "fusion-intake"][0]
    assert intake["action"] == "replaced"
    assert (home / ".claude" / "skills" / "fusion-intake").is_symlink()


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
    # a stale copy refreshes on re-run
    (copied / "SKILL.md").write_text("stale")
    again = setup.fan_out(canonical, setup.detect_agents(home), force=False)
    pi_intake = [r for r in again if r["skill"] == "fusion-intake"][0]
    assert pi_intake["action"] == "copied"


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
