from datetime import datetime

import pytest

from fusion import ledger


def test_verbs_are_the_eleven_verbatim():
    assert ledger.VERBS == (
        "created", "converted", "classified", "indexed", "moved",
        "promoted", "archived", "restructured", "shipped", "reflected",
        "noted",
    )


def test_parse_fixture(fixture_bucket):
    entries = ledger.read(fixture_bucket)
    assert len(entries) == 17
    first = entries[0]
    assert (first.date, first.time, first.actor, first.verb) == (
        "2026-07-08", "09:00", "bertrand", "created"
    )
    assert first.obj == "BUCKET.md"
    assert first.note == "bucket born"
    assert sum(1 for e in entries if e.verb == "reflected") == 1
    # arrow objects survive intact
    moved = [e for e in entries if e.verb == "moved"]
    assert moved[0].obj == (
        "activities/demo-ep/plan.md → activities/archive/demo-ep/plan.md"
    )


def test_read_missing_ledger_is_empty(tmp_path):
    assert ledger.read(tmp_path) == []


def test_append_same_day_and_new_day(tmp_path):
    (tmp_path / "LEDGER.md").write_text("# Ledger\n", encoding="utf-8")
    ledger.append(tmp_path, "claude", "created", "library/a.md",
                  at=datetime(2026, 7, 10, 9, 0))
    ledger.append(tmp_path, "claude", "noted", "workbench/b.md",
                  note="half-baked", at=datetime(2026, 7, 10, 9, 5))
    ledger.append(tmp_path, "pi", "indexed", "library/ (1 document)",
                  at=datetime(2026, 7, 11, 8, 0))
    text = (tmp_path / "LEDGER.md").read_text(encoding="utf-8")
    assert text == (
        "# Ledger\n"
        "\n"
        "## 2026-07-10\n"
        "- 09:00 · claude · created · library/a.md\n"
        '- 09:05 · claude · noted · workbench/b.md — "half-baked"\n'
        "\n"
        "## 2026-07-11\n"
        "- 08:00 · pi · indexed · library/ (1 document)\n"
    )
    assert len(ledger.read(tmp_path)) == 3


def test_append_creates_header_when_missing(tmp_path):
    ledger.append(tmp_path, "claude", "created", "BUCKET.md",
                  note="bucket born", at=datetime(2026, 7, 10, 9, 0))
    text = (tmp_path / "LEDGER.md").read_text(encoding="utf-8")
    assert text.startswith("# Ledger\n\n## 2026-07-10\n")


def test_append_rejects_unknown_verb(tmp_path):
    with pytest.raises(ValueError, match="verb"):
        ledger.append(tmp_path, "claude", "yeeted", "x")


def test_append_rejects_multiword_actor(tmp_path):
    with pytest.raises(ValueError, match="single token"):
        ledger.append(tmp_path, "Claude Code", "noted", "x")


def test_append_collapses_newlines_in_object_and_note(tmp_path):
    entry = ledger.append(tmp_path, "claude", "noted", "a\nb",
                          note="line one\nline two",
                          at=datetime(2026, 7, 10, 9, 0))
    assert entry.obj == "a b" and entry.note == "line one line two"
    read = ledger.read(tmp_path)[0]
    assert (read.obj, read.note) == ("a b", "line one line two")


def test_round_trip_note_with_em_dash(tmp_path):
    ledger.append(tmp_path, "claude", "restructured", "library/",
                  note="taxonomy — it stopped serving",
                  at=datetime(2026, 7, 10, 9, 0))
    entry = ledger.read(tmp_path)[0]
    assert entry.note == "taxonomy — it stopped serving"
    assert entry.obj == "library/"


def test_resolve_actor(monkeypatch):
    assert ledger.resolve_actor("pi") == "pi"
    monkeypatch.setenv("FUSION_ACTOR", "goose")
    assert ledger.resolve_actor() == "goose"
    monkeypatch.delenv("FUSION_ACTOR")
    assert ledger.resolve_actor()  # falls back to the OS username, non-empty


def test_parse_is_liberal_ignores_malformed_lines():
    text = (
        "# Ledger\n\n## 2026-07-10\n"
        "- 09:00 · claude · created · library/a.md\n"
        "not an entry at all\n"
        "- 9:0 · bad · time · format\n"
        "- 09:05 · claude · yeeted · library/b.md\n"
    )
    entries = ledger.parse(text)
    # malformed lines are skipped; unknown verbs are read (validation is E6's job)
    assert [(e.verb, e.obj) for e in entries] == [
        ("created", "library/a.md"), ("yeeted", "library/b.md"),
    ]
