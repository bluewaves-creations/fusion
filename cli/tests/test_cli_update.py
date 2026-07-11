"""fusion update end to end through the CLI surface.

Same isolation contract as test_cli_setup.py: no real subprocess is
ever reached; a fake runner records the exact command sequence.
"""
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from fusion import update
from fusion.cli import build_parser, main

# find_uv wraps which()'s answer in Path, so the argv the runner sees is
# the platform's rendering of this stub ("\\stub\\uv" on Windows).
STUB_UV = str(Path("/stub/uv"))


class FakeRunner:
    """Answers uv/fusion invocations from a script of canned results."""

    def __init__(self, bin_dir: Path, *, list_stdout="fusion-cli v1.2.1\n- fusion\n",
                 list_rc=0, upgrade_rc=0, setup_rc=0):
        self.bin_dir = bin_dir
        self.list_stdout = list_stdout
        self.list_rc = list_rc
        self.upgrade_rc = upgrade_rc
        self.setup_rc = setup_rc
        self.calls = []

    def __call__(self, argv, **kwargs):
        self.calls.append([str(a) for a in argv])
        prog, rest = Path(argv[0]).name, [str(a) for a in argv[1:]]
        if prog.startswith("uv") and rest == ["tool", "list"]:
            return SimpleNamespace(returncode=self.list_rc,
                                   stdout=self.list_stdout, stderr="")
        if prog.startswith("uv") and rest == ["tool", "upgrade", "fusion-cli"]:
            return SimpleNamespace(returncode=self.upgrade_rc, stdout="", stderr="")
        if prog.startswith("uv") and rest == ["tool", "dir", "--bin"]:
            return SimpleNamespace(returncode=0, stdout=f"{self.bin_dir}\n", stderr="")
        if prog.startswith("fusion") and rest[:1] == ["setup"]:
            return SimpleNamespace(returncode=self.setup_rc, stdout="", stderr="")
        raise AssertionError(f"unexpected command: {argv}")


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))          # windows
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    monkeypatch.setattr(update.shutil, "which",
                        lambda name, *a, **kw: "/stub/uv" if name == "uv" else None)
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **kw: pytest.fail("real subprocess reached"))
    bin_dir = tmp_path / "toolbin"
    bin_dir.mkdir()
    (bin_dir / "fusion").write_text("")
    return SimpleNamespace(home=home, bin_dir=bin_dir)


def _install_runner(monkeypatch, runner):
    monkeypatch.setattr(update, "_runner", lambda: runner)


def test_update_happy_path_runs_upgrade_then_setup(sandbox, monkeypatch, capsys):
    runner = FakeRunner(sandbox.bin_dir)
    _install_runner(monkeypatch, runner)
    assert main(["update"]) == 0
    assert runner.calls == [
        [STUB_UV, "tool", "list"],
        [STUB_UV, "tool", "upgrade", "fusion-cli"],
        [STUB_UV, "tool", "dir", "--bin"],
        [str(sandbox.bin_dir / "fusion"), "setup"],
    ]


def test_update_forwards_setup_flags(sandbox, monkeypatch):
    runner = FakeRunner(sandbox.bin_dir)
    _install_runner(monkeypatch, runner)
    custom = str(sandbox.home / "custom-skills")
    assert main(["update", "--force", "--skills-dir", custom,
                 "--no-agents"]) == 0
    assert runner.calls[-1] == [str(sandbox.bin_dir / "fusion"), "setup",
                                "--force", "--skills-dir", custom,
                                "--no-agents"]


def test_update_propagates_setup_exit_code(sandbox, monkeypatch):
    runner = FakeRunner(sandbox.bin_dir, setup_rc=3)
    _install_runner(monkeypatch, runner)
    assert main(["update"]) == 3


def test_update_without_uv_fails_with_manual_path(sandbox, monkeypatch, capsys):
    monkeypatch.setattr(update.shutil, "which", lambda name, *a, **kw: None)
    _install_runner(monkeypatch, FakeRunner(sandbox.bin_dir))
    assert main(["update"]) == 1
    err = capsys.readouterr().err
    assert "uv" in err and "fusion setup" in err


def test_update_finds_uv_at_install_sh_fallback(sandbox, monkeypatch):
    monkeypatch.setattr(update.shutil, "which", lambda name, *a, **kw: None)
    fallback = sandbox.home / ".local" / "bin" / "uv"
    fallback.parent.mkdir(parents=True)
    fallback.write_text("")
    fallback.chmod(0o755)
    runner = FakeRunner(sandbox.bin_dir)
    _install_runner(monkeypatch, runner)
    assert main(["update"]) == 0
    assert runner.calls[0][0] == str(fallback)


def test_update_refuses_non_uv_install(sandbox, monkeypatch, capsys):
    runner = FakeRunner(sandbox.bin_dir, list_stdout="black v24.0.0\n- black\n")
    _install_runner(monkeypatch, runner)
    assert main(["update"]) == 1
    err = capsys.readouterr().err
    assert "not managed by uv" in err and "fusion setup" in err
    # never got as far as upgrading
    assert [STUB_UV, "tool", "upgrade", "fusion-cli"] not in runner.calls
    assert runner.calls == [[STUB_UV, "tool", "list"]]


def test_update_reports_failed_upgrade_with_retry_ritual(sandbox, monkeypatch,
                                                         capsys):
    runner = FakeRunner(sandbox.bin_dir, upgrade_rc=1)
    _install_runner(monkeypatch, runner)
    assert main(["update"]) == 1
    err = capsys.readouterr().err
    assert "uv tool upgrade fusion-cli && fusion setup" in err
    # setup never ran on a failed upgrade
    assert all(c[1:2] != ["setup"] for c in runner.calls)


def test_update_appears_in_help(sandbox):
    assert "update" in build_parser().format_help()
