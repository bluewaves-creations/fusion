"""fusion setup end to end through the CLI surface."""

import json
import subprocess
from pathlib import Path

import pytest

from fusion import setup
from fusion.cli import main
from tests.test_setup_core import make_payload

# Everything "found" by default: no PATH/tool advice, no subprocess call.
# Individual tests override the which-map to exercise the §4d branches.
_ALL_FOUND = {
    "fusion": "/stub/fusion",
    "git": "/stub/git",
    "soffice": "/stub/soffice",
    "uv": "/stub/uv",
}


def _no_real_subprocess(*args, **kwargs):
    raise AssertionError("real subprocess reached from tests")


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))  # windows
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    payload = make_payload(tmp_path / "payload")
    monkeypatch.setattr(setup, "payload_root", lambda: payload)

    # Isolation is deliberate, not accidental: environment_advice() must
    # never see a real PATH or spawn a real subprocess from under pytest.
    monkeypatch.setattr(
        setup.shutil, "which", lambda name, *a, **kw: _ALL_FOUND.get(name)
    )
    # setup.py imports subprocess *inside* environment_advice (a local
    # import), but that still binds the same sys.modules["subprocess"]
    # object, so patching the stdlib attribute directly reaches it too.
    monkeypatch.setattr(subprocess, "run", _no_real_subprocess)

    return home


def test_setup_json_reports_all_sections(sandbox, capsys):
    assert main(["setup", "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["skills"]["dir"].endswith(".agents/skills") or out["skills"][
        "dir"
    ].endswith(".agents\\skills")
    assert {r["action"] for r in out["skills"]["results"]} == {"installed"}
    assert any(
        a["agent"] == "Claude Code" and a["action"] == "linked" for a in out["agents"]
    )
    assert isinstance(out["advice"], list)


def test_setup_skills_dir_and_no_agents(sandbox, capsys):
    custom = str(sandbox / "custom-skills")
    assert main(["setup", "--json", "--skills-dir", custom, "--no-agents"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["skills"]["dir"] == custom
    assert out["agents"] == []
    assert (Path(custom) / "fusion-intake").is_dir()


def test_setup_env_vars_apply_and_flags_win(sandbox, capsys, monkeypatch):
    monkeypatch.setenv("FUSION_SKILLS_DIR", str(sandbox / "from-env"))
    monkeypatch.setenv("FUSION_NO_AGENTS", "1")
    assert main(["setup", "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["skills"]["dir"] == str(sandbox / "from-env")
    assert out["agents"] == []


def test_setup_expands_tilde_in_skills_dir_env(sandbox, capsys, monkeypatch):
    monkeypatch.setenv("FUSION_SKILLS_DIR", "~/x")
    assert main(["setup", "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["skills"]["dir"] == str(sandbox / "x")
    assert (sandbox / "x" / "fusion-intake").is_dir()


def test_setup_remove_round_trip(sandbox, capsys):
    assert main(["setup", "--json"]) == 0
    capsys.readouterr()
    assert main(["setup", "--remove", "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert not (sandbox / ".agents" / "skills" / "fusion-intake").exists()
    assert not (sandbox / ".claude" / "skills" / "fusion-intake").exists()
    assert "uv tool uninstall fusion-cli" in json.dumps(out)


def test_setup_human_report_names_agents(sandbox, capsys):
    assert main(["setup"]) == 0
    text = capsys.readouterr().out
    assert "Claude Code" in text and "fusion-intake" in text
    assert "next" in text.lower()


def test_setup_advice_runs_update_shell_when_fusion_off_path(
    sandbox, capsys, monkeypatch
):
    which_map = {**_ALL_FOUND, "fusion": None}
    monkeypatch.setattr(
        setup.shutil, "which", lambda name, *a, **kw: which_map.get(name)
    )

    calls = []

    def _recorder(cmd, **kwargs):
        calls.append(cmd)
        return type("Result", (), {"returncode": 0})()

    monkeypatch.setattr(subprocess, "run", _recorder)

    assert main(["setup", "--json"]) == 0
    out = json.loads(capsys.readouterr().out)

    assert calls == [["uv", "tool", "update-shell"]]
    assert any(a["topic"] == "path" and "restart" in a["text"] for a in out["advice"])


def test_setup_advice_respects_no_modify_path(sandbox, capsys, monkeypatch):
    which_map = {**_ALL_FOUND, "fusion": None}
    monkeypatch.setattr(
        setup.shutil, "which", lambda name, *a, **kw: which_map.get(name)
    )
    monkeypatch.setenv("FUSION_NO_MODIFY_PATH", "1")

    calls = []

    def _recorder(cmd, **kwargs):
        calls.append(cmd)
        return type("Result", (), {"returncode": 0})()

    monkeypatch.setattr(subprocess, "run", _recorder)

    assert main(["setup", "--json"]) == 0
    out = json.loads(capsys.readouterr().out)

    assert calls == []
    assert any(a["topic"] == "path" and "yourself" in a["text"] for a in out["advice"])
