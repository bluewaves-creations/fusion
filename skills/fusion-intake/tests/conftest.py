"""Fixtures for the fusion-intake script suite. No fusion package imports —
the skill is self-contained; buckets are built by hand to SPEC 1.0."""
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

BUCKET_CARD = """---
name: {name}
kind: personal
description: Scratch bucket for intake tests.
fusion_version: "1.0"
created: 2026-07-10
---

Scratch bucket.

## Conventions

### Rules

### Delegations
"""

MANIFEST_HEADER = (
    "# Manifest\n\n| file | added | by | sha256 | library |\n"
    "|---|---|---|---|---|\n"
)

ZONES = ("inbox", "sources", "library", "activities", "workbench", "output")


@pytest.fixture
def bucket(tmp_path):
    root = tmp_path / "scratch"
    for zone in ZONES:
        (root / zone).mkdir(parents=True)
    (root / "BUCKET.md").write_text(
        BUCKET_CARD.format(name="scratch"), encoding="utf-8")
    (root / "LEDGER.md").write_text("# Ledger\n", encoding="utf-8")
    (root / "sources" / "MANIFEST.md").write_text(
        MANIFEST_HEADER, encoding="utf-8")
    return root


def drop(root: Path, name: str, content: str) -> Path:
    """Put a text file in inbox/."""
    p = root / "inbox" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def seed_source(root: Path, rel: str, content: str) -> Path:
    """Put a text file in sources/ (registration in MANIFEST is not the
    gate's concern — it compares against the tree on disk)."""
    p = root / "sources" / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p
