"""fusion new — a complete bucket, born conformant (SPEC §2, §3)."""
from __future__ import annotations

import os
import subprocess
from datetime import datetime
from pathlib import Path

import yaml

from . import hub, indexer, ledger
from .bucket import ZONES

BUCKET_TEMPLATE = """---
name: {name}
kind: {kind}
description: {description}
fusion_version: "1.0"
created: {created}
inbox_max_age_days: 7
reflection_cadence: weekly
---

{description_body}

## Conventions

### Rules

### Delegations
"""


def _yaml_scalar(value: str) -> str:
    """Render a string as a safe single-line YAML scalar (quoted only when needed)."""
    style = '"' if "\n" in value else None
    return yaml.safe_dump(
        value, allow_unicode=True, width=2**31 - 1, default_style=style
    ).split("\n")[0]

MANIFEST_HEADER = (
    "# Manifest\n\n| file | added | by | sha256 | library |\n"
    "|---|---|---|---|---|\n"
)

GITATTRIBUTES = (
    "# written by fusion new — multi-machine merges stay safe (SPEC §6)\n"
    "* text=auto eol=lf\n"
    "LEDGER.md merge=union\n"
    "sources/MANIFEST.md merge=union\n"
)


class ScaffoldError(Exception):
    pass


def new_bucket(
    path: Path,
    name: str | None = None,
    kind: str = "personal",
    description: str | None = None,
    actor: str = "human",
    at: datetime | None = None,
    register: bool = True,
) -> tuple[Path, list[str]]:
    root = path.expanduser().resolve()
    name = name or root.name
    description = description or f"A {kind} bucket. Describe me."
    at = at or datetime.now()

    if root.exists() and not root.is_dir():
        raise ScaffoldError(f"target exists and is not a directory: {root}")
    if root.exists() and any(root.iterdir()):
        raise ScaffoldError(f"target exists and is not empty: {root}")
    if register and any(e.name == name for e in hub.load()):
        raise ScaffoldError(f"bucket '{name}' is already registered in the hub")

    for zone in ZONES:
        (root / zone).mkdir(parents=True, exist_ok=True)
    for zone in ("inbox", "workbench", "output"):
        (root / zone / ".gitkeep").write_text("", encoding="utf-8", newline="\n")
    (root / "BUCKET.md").write_text(
        BUCKET_TEMPLATE.format(
            name=_yaml_scalar(name), kind=_yaml_scalar(kind),
            description=_yaml_scalar(description),
            description_body=description,
            created=at.strftime("%Y-%m-%d"),
        ),
        encoding="utf-8", newline="\n",
    )
    (root / "sources" / "MANIFEST.md").write_text(
        MANIFEST_HEADER, encoding="utf-8", newline="\n"
    )
    (root / ".gitattributes").write_text(
        GITATTRIBUTES, encoding="utf-8", newline="\n"
    )
    ledger.append(root, actor, "created", "BUCKET.md", note="bucket born", at=at)
    indexer.write_indexes(root, actor=None)

    warnings: list[str] = []
    for cmd in (
        ["git", "init", "-q"],
        ["git", "add", "-A"],
        ["git", "commit", "-q", "-m", "fusion new: bucket born"],
    ):
        try:
            result = subprocess.run(
                cmd, cwd=root, capture_output=True, text=True, timeout=30,
                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
            )
            if result.returncode != 0:
                warnings.append(
                    f"{' '.join(cmd)}: {result.stderr.strip() or 'failed'}"
                )
                break
        except FileNotFoundError:
            warnings.append("git not found — bucket created without a repository")
            break
        except subprocess.TimeoutExpired:
            warnings.append(f"{' '.join(cmd)}: timed out after 30s")
            break

    if register:
        try:
            hub.add(hub.HubEntry(name, kind, hub.display_path(root), description))
        except (ValueError, OSError) as exc:
            warnings.append(f"hub registration failed: {exc}")

    return root, warnings
