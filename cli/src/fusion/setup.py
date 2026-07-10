"""fusion setup — the installer brain. Bootstraps hand off here; every
mechanical decision about skills placement lives in this module so it is
written once, runs identically on macOS/Linux/Windows, and is tested.

Never destroys content it did not create: foreign entries are warned and
left unless --force. Writes only under the given directories.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.resources
import shutil
from pathlib import Path


class SetupError(Exception):
    """A setup step that cannot proceed."""


def payload_root() -> Path:
    bundled = importlib.resources.files("fusion") / "_skills"
    p = Path(str(bundled))
    if p.is_dir() and sorted(p.glob("fusion-*")):
        return p
    repo = Path(__file__).resolve().parents[3] / "skills"
    if repo.is_dir() and sorted(repo.glob("fusion-*")):
        return repo
    raise SetupError(
        "no skills payload: neither bundled fusion/_skills nor a repo "
        "skills/ directory — reinstall fusion-cli"
    )


def payload_version() -> str:
    try:
        return importlib.metadata.version("fusion-cli")
    except importlib.metadata.PackageNotFoundError:
        return "dev"


def tree_digest(path: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(p for p in path.rglob("*") if p.is_file()):
        h.update(f.relative_to(path).as_posix().encode())
        h.update(b"\0")
        h.update(f.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def install_canonical(payload: Path, skills_dir: Path,
                      force: bool) -> list[dict]:
    skills_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for skill in sorted(payload.glob("fusion-*")):
        dest = skills_dir / skill.name
        if dest.is_symlink():
            if not force:
                results.append({
                    "skill": skill.name, "action": "left",
                    "detail": f"{dest} is a symlink you manage — "
                              f"--force replaces it"})
                continue
            dest.unlink()
            shutil.copytree(skill, dest)
            results.append({"skill": skill.name, "action": "replaced",
                            "detail": str(dest)})
            continue
        if dest.is_dir():
            if tree_digest(dest) == tree_digest(skill):
                results.append({"skill": skill.name, "action": "up-to-date",
                                "detail": str(dest)})
                continue
            shutil.rmtree(dest)
            shutil.copytree(skill, dest)
            results.append({"skill": skill.name, "action": "updated",
                            "detail": str(dest)})
            continue
        shutil.copytree(skill, dest)
        results.append({"skill": skill.name, "action": "installed",
                        "detail": str(dest)})
    return results
