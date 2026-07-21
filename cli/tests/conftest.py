from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = REPO_ROOT / "examples" / "crazy-ones"


@pytest.fixture
def fixture_bucket() -> Path:
    assert FIXTURE.is_dir(), "examples/crazy-ones must exist — it is normative"
    return FIXTURE


VALID_DOC = """---
title: Notes
type: note
aurora: library
---

## Summary

A perfectly conformant note.

---

Body.
"""

BUCKET_CARD = """---
name: scratch
kind: personal
description: A scratch bucket for tests.
fusion_version: "1.0"
created: 2026-07-10
inbox_max_age_days: 7
---

Scratch bucket.

## Conventions

### Rules

### Delegations
"""


@pytest.fixture
def make_bucket(tmp_path):
    """Factory: a minimal bucket that passes `check` with 0 errors, 0 warnings."""
    from fusion import indexer
    from fusion.bucket import ZONES

    def _make(name: str = "scratch"):
        root = tmp_path / name
        for zone in ZONES:
            (root / zone).mkdir(parents=True)
        # newline="\n" pinned throughout: the checker byte-compares INDEX.md
        # against indexer.generate()'s LF-only output (checker.py's W2 check),
        # and on Windows plain write_text() translates '\n' to os.linesep
        # (CRLF) on write, which would make every register file here diverge
        # from what the checker regenerates. Pin LF everywhere a register
        # file is written so this fixture reproduces the same bytes on every
        # platform.
        (root / "BUCKET.md").write_text(
            BUCKET_CARD.replace("name: scratch", f"name: {name}"),
            encoding="utf-8",
            newline="\n",
        )
        (root / "LEDGER.md").write_text(
            "# Ledger\n\n## 2026-07-10\n"
            '- 09:00 · test · created · BUCKET.md — "bucket born"\n',
            encoding="utf-8",
            newline="\n",
        )
        (root / "sources" / "MANIFEST.md").write_text(
            "# Manifest\n\n| file | added | by | sha256 | library |\n"
            "|---|---|---|---|---|\n",
            encoding="utf-8",
            newline="\n",
        )
        (root / "library" / "notes.md").write_text(
            VALID_DOC,
            encoding="utf-8",
            newline="\n",
        )
        for zone in ("library", "activities"):
            index = indexer.generate(root / zone, zone)
            (root / zone / "INDEX.md").write_text(
                index,
                encoding="utf-8",
                newline="\n",
            )
        return root

    return _make
