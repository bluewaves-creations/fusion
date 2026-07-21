"""Fixtures for the fusion-librarian script suite. No fusion package
imports — the skill is self-contained; buckets are built by hand to
SPEC 1.0 (mirrors fusion-intake's tests/conftest.py)."""

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

# link-repair.py carries a hyphen (matches the CLI invocation shown in
# SKILL.md / cross-reference.md) so it can't be `import`ed by filename —
# load it once under the underscored module name and register it in
# sys.modules so every test file can `import link_repair as lr`.
_spec = importlib.util.spec_from_file_location(
    "link_repair", SCRIPTS / "link-repair.py"
)
_link_repair = importlib.util.module_from_spec(_spec)
sys.modules["link_repair"] = _link_repair
_spec.loader.exec_module(_link_repair)

BUCKET_CARD = """---
name: {name}
kind: personal
description: Scratch bucket for librarian tests.
fusion_version: "1.0"
created: 2026-07-10
---

Scratch bucket.

## Conventions

### Rules

### Delegations
"""

MANIFEST_HEADER = (
    "# Manifest\n\n| file | added | by | sha256 | library |\n|---|---|---|---|---|\n"
)

ZONES = ("inbox", "sources", "library", "activities", "workbench", "output")

DOC_TEMPLATE = """---
title: {title}
type: note
aurora: library
created: 2026-01-01
---

## Summary

Test document.

---

{body}
"""


@pytest.fixture
def bucket(tmp_path):
    root = tmp_path / "scratch"
    for zone in ZONES:
        (root / zone).mkdir(parents=True)
    (root / "BUCKET.md").write_text(
        BUCKET_CARD.format(name="scratch"), encoding="utf-8"
    )
    (root / "LEDGER.md").write_text("# Ledger\n", encoding="utf-8")
    (root / "sources" / "MANIFEST.md").write_text(MANIFEST_HEADER, encoding="utf-8")
    return root


def seed_source(root: Path, rel: str, content: str = "binary-ish content") -> Path:
    """Put a file in sources/ — link-repair's candidate index scans the
    tree on disk, not MANIFEST registration."""
    p = root / "sources" / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def write_doc(root: Path, rel: str, body: str, title: str | None = None) -> Path:
    """Put a conformant document in library/ or activities/ with the given
    body — the caller embeds links as plain markdown."""
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    title = title or Path(rel).stem
    p.write_text(DOC_TEMPLATE.format(title=title, body=body), encoding="utf-8")
    return p
