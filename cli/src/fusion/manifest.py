"""sources/MANIFEST.md — the register of preserved originals (SPEC §7)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_ROW_RE = re.compile(r"^\| (.+?) \| (.+?) \| (.+?) \| (.+?) \| (.+?) \|$")


@dataclass
class ManifestRow:
    file: str
    added: str
    by: str
    sha256: str
    library: str


def read(bucket_root: Path) -> list[ManifestRow]:
    path = bucket_root / "sources" / "MANIFEST.md"
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").split("\n"):
        m = _ROW_RE.match(line)
        if not m:
            continue
        cells = [c.strip() for c in m.groups()]
        if cells[0] == "file" or set(cells[0]) <= {"-"}:
            continue  # header and separator rows
        rows.append(ManifestRow(*cells))
    return rows
