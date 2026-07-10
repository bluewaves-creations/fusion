"""~/.fusion/hub.md — the machine's registry of buckets (SPEC §1)."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

_ENTRY_RE = re.compile(r"^- \*\*(.+?)\*\* · ([^·]+?) · (.+?) — (.*)$")


@dataclass
class HubEntry:
    name: str
    kind: str
    path: str
    description: str


def hub_path() -> Path:
    return Path(os.environ.get("FUSION_HUB", "~/.fusion/hub.md")).expanduser()


def display_path(root: Path) -> str:
    """Absolute path, ~-contracted when under the user's home."""
    try:
        return "~/" + root.relative_to(Path.home()).as_posix()
    except ValueError:
        return str(root)


def load() -> list[HubEntry]:
    path = hub_path()
    if not path.exists():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").split("\n"):
        m = _ENTRY_RE.match(line)
        if m:
            entries.append(HubEntry(*(g.strip() for g in m.groups())))
    return entries


def _one_line(value: str) -> str:
    return " ".join(str(value).split())


def save(entries: list[HubEntry]) -> None:
    path = hub_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Fusion Hub", ""]
    lines += [
        f"- **{_one_line(e.name)}** · {_one_line(e.kind)} · "
        f"{_one_line(e.path)} — {_one_line(e.description)}"
        for e in entries
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def add(entry: HubEntry) -> None:
    entries = load()
    if any(e.name == entry.name for e in entries):
        raise ValueError(f"bucket '{entry.name}' is already registered")
    entries.append(entry)
    save(entries)


def remove(name: str) -> bool:
    entries = load()
    kept = [e for e in entries if e.name != name]
    if len(kept) == len(entries):
        return False
    save(kept)
    return True


def resolve(entry: HubEntry) -> Path:
    return Path(entry.path).expanduser()
