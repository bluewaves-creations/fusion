"""The bucket — zones, identity card, and document iteration (SPEC §2, §3)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from .document import Document, read_document, split_frontmatter

ZONES: tuple[str, ...] = (
    "inbox",
    "sources",
    "library",
    "activities",
    "workbench",
    "output",
)
DOC_ZONES: tuple[str, ...] = ("library", "activities", "output")
REQUIRED_BUCKET_FIELDS: tuple[str, ...] = (
    "name",
    "kind",
    "description",
    "fusion_version",
    "created",
)


@dataclass
class Bucket:
    root: Path
    frontmatter: dict[str, Any] | None
    fm_error: str | None

    def _get(self, key: str) -> Any:
        return (self.frontmatter or {}).get(key)

    @property
    def name(self) -> Any:
        return self._get("name")

    @property
    def kind(self) -> Any:
        return self._get("kind")

    @property
    def description(self) -> Any:
        return self._get("description")

    @property
    def inbox_max_age_days(self) -> int:
        value = self._get("inbox_max_age_days")
        try:
            return int(value)
        except (TypeError, ValueError):
            return 7


def find_root(start: Path) -> Path | None:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / "BUCKET.md").is_file():
            return candidate
    return None


def load(root: Path) -> Bucket:
    card = root / "BUCKET.md"
    if not card.exists():
        return Bucket(root, None, "BUCKET.md missing")
    fm, err, _ = split_frontmatter(card.read_text(encoding="utf-8"))
    return Bucket(root, fm, err)


def iter_documents(
    root: Path, zones: tuple[str, ...] = DOC_ZONES
) -> Iterator[tuple[str, Path, Document]]:
    for zone in zones:
        zone_dir = root / zone
        if not zone_dir.is_dir():
            continue
        for path in sorted(zone_dir.rglob("*.md")):
            rel = path.relative_to(zone_dir)
            if path.name == "INDEX.md" or any(
                part.startswith(".") for part in rel.parts
            ):
                continue
            yield zone, rel, read_document(path)
