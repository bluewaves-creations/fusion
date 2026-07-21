"""LEDGER.md — append-only, chronological, exactly one writer (SPEC §6)."""

from __future__ import annotations

import getpass
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

VERBS: tuple[str, ...] = (
    "created",
    "converted",
    "classified",
    "indexed",
    "moved",
    "promoted",
    "archived",
    "restructured",
    "shipped",
    "reflected",
    "noted",
)

_ENTRY_RE = re.compile(r"^- (\d{2}:\d{2}) · (\S+) · (\S+) · (.*)$")
_NOTE_SEP = ' — "'


@dataclass
class Entry:
    date: str
    time: str
    actor: str
    verb: str
    obj: str
    note: str | None = None


def parse(text: str) -> list[Entry]:
    """Liberal reader: lines that don't match the grammar are ignored."""
    entries: list[Entry] = []
    date: str | None = None
    for line in text.split("\n"):
        if line.startswith("## "):
            date = line[3:].strip()
            continue
        m = _ENTRY_RE.match(line)
        if not (m and date):
            continue
        obj, note = m.group(4), None
        if _NOTE_SEP in obj and obj.endswith('"'):
            obj, _, rest = obj.partition(_NOTE_SEP)
            note = rest[:-1]
        entries.append(Entry(date, m.group(1), m.group(2), m.group(3), obj, note))
    return entries


def read(bucket_root: Path) -> list[Entry]:
    path = bucket_root / "LEDGER.md"
    if not path.exists():
        return []
    return parse(path.read_text(encoding="utf-8"))


def format_line(entry: Entry) -> str:
    line = f"- {entry.time} · {entry.actor} · {entry.verb} · {entry.obj}"
    if entry.note:
        line += f' — "{entry.note}"'
    return line


def append(
    bucket_root: Path,
    actor: str,
    verb: str,
    obj: str,
    note: str | None = None,
    at: datetime | None = None,
) -> Entry:
    """The one writer. Strict: refuses verbs outside the eleven.

    Actors must be single tokens; objects and notes are collapsed to one
    line — the register must round-trip through its own reader.
    """
    if verb not in VERBS:
        raise ValueError(f"verb must be one of: {', '.join(VERBS)}")
    if (
        not actor
        or actor != actor.strip()
        or any(c.isspace() for c in actor)
        or "·" in actor
    ):
        raise ValueError(
            f"actor must be a single token with no spaces or '·': {actor!r}"
        )
    obj = " ".join(obj.split())
    if note is not None:
        note = " ".join(note.split())
    at = at or datetime.now()
    entry = Entry(at.strftime("%Y-%m-%d"), at.strftime("%H:%M"), actor, verb, obj, note)
    path = bucket_root / "LEDGER.md"
    text = path.read_text(encoding="utf-8") if path.exists() else "# Ledger\n"
    lines = text.rstrip("\n").split("\n")
    heading = f"## {entry.date}"
    last_heading = next(
        (line for line in reversed(lines) if line.startswith("## ")), None
    )
    if last_heading == heading:
        lines.append(format_line(entry))
    else:
        lines.extend(["", heading, format_line(entry)])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return entry


def resolve_actor(explicit: str | None = None) -> str:
    """--as > FUSION_ACTOR > OS username. The pen always has a name."""
    return explicit or os.environ.get("FUSION_ACTOR") or getpass.getuser()
