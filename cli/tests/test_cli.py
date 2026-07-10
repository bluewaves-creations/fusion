import json
import shutil

import pytest

from fusion.cli import main


@pytest.fixture(autouse=True)
def tmp_hub(tmp_path, monkeypatch):
    monkeypatch.setenv("FUSION_HUB", str(tmp_path / "hub.md"))
    monkeypatch.setenv("FUSION_ACTOR", "test")


def out_json(capsys):
    return json.loads(capsys.readouterr().out)


def test_check_fixture_clean_exit_zero(fixture_bucket, capsys):
    assert main(["check", str(fixture_bucket), "--json"]) == 0
    payload = out_json(capsys)
    assert payload["ok"] is True
    assert payload["errors"] == [] and payload["warnings"] == []


def test_check_broken_bucket_exit_one(fixture_bucket, tmp_path, capsys):
    broken = tmp_path / "broken"
    shutil.copytree(fixture_bucket, broken)
    shutil.rmtree(broken / "workbench")
    assert main(["check", str(broken), "--json"]) == 1
    payload = out_json(capsys)
    assert payload["ok"] is False
    assert payload["errors"][0]["code"] == "E1"


def test_new_then_hub_list(tmp_path, capsys):
    assert main(["new", str(tmp_path / "studio"), "--kind", "studio",
                 "--description", "Music.", "--json"]) == 0
    born = out_json(capsys)
    assert born["bucket"] == "studio"
    assert main(["hub", "--json"]) == 0
    entries = out_json(capsys)
    assert entries[0]["name"] == "studio" and entries[0]["kind"] == "studio"


def test_hub_add_remove(tmp_path, capsys):
    main(["new", str(tmp_path / "studio"), "--description", "d"])
    capsys.readouterr()
    assert main(["hub", "remove", "studio", "--json"]) == 0
    assert main(["hub", "remove", "studio"]) == 1  # already gone
    capsys.readouterr()
    assert main(["hub", "add", str(tmp_path / "studio"), "--json"]) == 0
    assert main(["hub", "add", str(tmp_path)]) == 1  # not a bucket


def test_log_append_and_read(tmp_path, capsys):
    main(["new", str(tmp_path / "b"), "--description", "d"])
    capsys.readouterr()
    root = str(tmp_path / "b")
    assert main(["log", "noted", "workbench/x.md", "--note", "hello",
                 "--at", "2026-07-10 09:30", "--bucket", root, "--json"]) == 0
    appended = out_json(capsys)
    assert appended["verb"] == "noted" and appended["note"] == "hello"
    assert main(["log", "--bucket", root, "--json"]) == 0
    entries = out_json(capsys)
    assert [e["verb"] for e in entries] == ["created", "noted"]
    assert main(["log", "yeeted", "x", "--bucket", root]) == 1  # closed verbs


def test_log_requires_a_bucket(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["log", "noted", "x"]) == 1


def test_index_logs_when_changed(tmp_path, capsys):
    main(["new", str(tmp_path / "b"), "--description", "d"])
    capsys.readouterr()
    root = tmp_path / "b"
    (root / "library" / "note.md").write_text(
        "---\ntitle: N\ntype: note\naurora: library\n---\n\n"
        "## Summary\n\nA note.\n\n---\n\nBody.\n",
        encoding="utf-8",
    )
    assert main(["index", str(root), "--json"]) == 0
    results = out_json(capsys)
    assert {"zone": "library", "documents": 1, "changed": True} in results
    assert main(["check", str(root)]) == 0  # index current again


def test_status_today_agenda_json(fixture_bucket, capsys):
    assert main(["status", str(fixture_bucket), "--json"]) == 0
    assert out_json(capsys)["documents"] == 6
    assert main(["today", "--json"]) == 0
    assert out_json(capsys)["groups"] == {}  # empty hub, empty day
    assert main(["agenda", "--json"]) == 0
    assert out_json(capsys) == {"dated": [], "active": []}


def test_every_command_has_help(capsys):
    for cmd in ("new", "hub", "log", "index", "check",
                "status", "today", "agenda"):
        with pytest.raises(SystemExit) as exc:
            main([cmd, "--help"])
        assert exc.value.code == 0
        assert "--json" in capsys.readouterr().out


def test_hub_add_refuses_blank_required_field(tmp_path, capsys):
    root = tmp_path / "halfcard"
    root.mkdir()
    (root / "BUCKET.md").write_text(
        "---\nname: halfcard\nkind: personal\ndescription:\n---\n\nBody.\n",
        encoding="utf-8",
    )
    assert main(["hub", "add", str(root)]) == 1  # blank description = missing


def test_hub_add_resolves_relative_paths(tmp_path, monkeypatch, capsys):
    main(["new", str(tmp_path / "b"), "--description", "d"])
    main(["hub", "remove", "b"])
    capsys.readouterr()
    monkeypatch.chdir(tmp_path / "b")
    assert main(["hub", "add", "."]) == 0
    capsys.readouterr()
    from fusion import hub
    entry = hub.load()[0]
    assert entry.path not in (".", "./")
    from pathlib import Path as P
    assert P(entry.path).expanduser().is_absolute()


def test_failure_emits_json_envelope(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)          # nowhere near a bucket
    assert main(["log", "noted", "x", "--json"]) == 1
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["ok"] is False
    assert "bucket" in payload["error"]
    assert captured.err == ""


def test_failure_stays_human_without_json(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["log", "noted", "x"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("fusion: ")


def test_check_names_the_missing_path(capsys):
    assert main(["check", "/nonexistent/nowhere"]) == 1
    assert "/nonexistent/nowhere" in capsys.readouterr().err


def test_help_describes_every_command(capsys):
    needles = {
        "new": "Scaffold", "hub": "registry", "log": "append-only",
        "index": "Deterministic", "check": "SPEC", "status": "glance",
        "today": "morning", "agenda": "horizon",
    }
    for cmd, needle in needles.items():
        with pytest.raises(SystemExit):
            main([cmd, "--help"])
        assert needle in capsys.readouterr().out, cmd
