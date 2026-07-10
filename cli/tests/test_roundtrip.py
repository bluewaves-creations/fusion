"""The Phase 2 gate, as a test: new → all 11 verbs → index → check → views."""
import json

import pytest

from fusion.cli import main
from fusion.ledger import VERBS


@pytest.fixture(autouse=True)
def tmp_world(tmp_path, monkeypatch):
    monkeypatch.setenv("FUSION_HUB", str(tmp_path / "hub.md"))
    monkeypatch.setenv("FUSION_ACTOR", "roundtrip")


def out_json(capsys):
    return json.loads(capsys.readouterr().out)


def test_round_trip(tmp_path, capsys):
    root = tmp_path / "scratch"

    # 1. born conformant
    assert main(["new", str(root), "--description", "Round trip."]) == 0
    capsys.readouterr()
    assert main(["check", str(root)]) == 0

    # 2. a document arrives; the index notices; check stays green
    (root / "library" / "first-note.md").write_text(
        "---\ntitle: First Note\ntype: note\naurora: library\n---\n\n"
        "## Summary\n\nThe first note.\n\n---\n\nBody.\n",
        encoding="utf-8",
    )
    capsys.readouterr()
    assert main(["index", str(root)]) == 0
    capsys.readouterr()
    assert main(["check", str(root)]) == 0
    capsys.readouterr()

    # 3. every verb in the closed set, appended and read back
    for i, verb in enumerate(VERBS):
        assert main([
            "log", verb, f"workbench/thing-{i}.md",
            "--at", f"2026-07-10 {10 + i // 60:02d}:{i % 60:02d}",
            "--bucket", str(root),
        ]) == 0
    capsys.readouterr()
    assert main(["log", "--bucket", str(root), "--json"]) == 0
    entries = out_json(capsys)
    # founding entry + indexed (from `fusion index`) + the eleven
    assert len(entries) == 13
    assert [e["verb"] for e in entries[-len(VERBS):]] == list(VERBS)

    # 4. still conformant — the ledger accepts the whole vocabulary
    assert main(["check", str(root)]) == 0
    capsys.readouterr()

    # 5. the views stay sane
    assert main(["status", str(root), "--json"]) == 0
    status = out_json(capsys)
    assert status["bucket"] == "scratch" and status["documents"] == 1
    assert main(["today", "--json"]) == 0
    today = out_json(capsys)
    assert today["buckets"] == ["scratch"]
    assert main(["agenda", "--json"]) == 0
    assert out_json(capsys) == {"dated": [], "active": [], "missing": []}
