"""fusion update — one verb to bring the whole system current.

Upgrades fusion-cli through uv, then re-runs `fusion setup` from the
NEW binary: this process keeps the old skills payload in memory, so
setup must run in a child for the refreshed payload to land. Every
decision is testable without a real subprocess — the runner is a seam.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from .setup import payload_version


class UpdateError(Exception):
    """An update step that cannot proceed."""


def _runner():
    return subprocess.run


def find_uv(home: Path) -> Path | None:
    found = shutil.which("uv")
    if found:
        return Path(found)
    # install.sh's landing spot, for shells whose PATH never learned it
    for name in ("uv.exe", "uv") if os.name == "nt" else ("uv",):
        candidate = home / ".local" / "bin" / name
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def uv_owns_install(uv: Path, run) -> bool:
    proc = run([str(uv), "tool", "list"], capture_output=True, text=True)
    if proc.returncode != 0:
        return False
    return any(line.split()[:1] == ["fusion-cli"] for line in proc.stdout.splitlines())


def fusion_binary(uv: Path, run) -> Path:
    proc = run([str(uv), "tool", "dir", "--bin"], capture_output=True, text=True)
    if proc.returncode != 0 or not proc.stdout.strip():
        raise UpdateError(
            "could not resolve uv's tool bin dir — finish by hand: "
            "uv tool dir --bin, then <that dir>/fusion setup"
        )
    bin_dir = Path(proc.stdout.strip())
    for name in ("fusion", "fusion.exe"):
        candidate = bin_dir / name
        if candidate.is_file():
            return candidate
    raise UpdateError(
        f"fusion not found in {bin_dir} after the upgrade — check: uv tool list"
    )


def run_update(home: Path, setup_args: list[str]) -> int:
    run = _runner()
    uv = find_uv(home)
    if uv is None:
        raise UpdateError(
            "uv not found — fusion updates through uv "
            "(https://docs.astral.sh/uv/). Install it, or upgrade "
            "fusion-cli with whatever installed it, then run: fusion setup"
        )
    if not uv_owns_install(uv, run):
        raise UpdateError(
            "this fusion-cli is not managed by uv — upgrade it with "
            "whatever installed it (pip, pipx, a checkout), then run: "
            "fusion setup"
        )
    print(f"fusion-cli {payload_version()} — asking uv for newer…")
    sys.stdout.flush()  # keep our line ahead of uv's inherited stdio
    if run([str(uv), "tool", "upgrade", "fusion-cli"]).returncode != 0:
        raise UpdateError(
            "uv tool upgrade failed — on Windows the running fusion.exe "
            "can hold the lock. Exit this process, then run: "
            "uv tool upgrade fusion-cli && fusion setup"
        )
    child = run([str(fusion_binary(uv, run)), "setup", *setup_args])
    return child.returncode
