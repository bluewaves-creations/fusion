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
import os
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
        if dest.exists():
            if not force:
                results.append({"skill": skill.name, "action": "left",
                                "detail": f"{dest} is a file — "
                                          f"--force replaces"})
                continue
            dest.unlink()
            shutil.copytree(skill, dest)
            results.append({"skill": skill.name, "action": "replaced",
                            "detail": str(dest)})
            continue
        shutil.copytree(skill, dest)
        results.append({"skill": skill.name, "action": "installed",
                        "detail": str(dest)})
    return results


# One row per agent. mode "link": the agent does not read the standard
# ~/.agents/skills dir, so each fusion-* skill gets a symlink (or copy)
# in its own skills dir. mode "standard": the agent reads the standard
# dir — creating links there too would load every skill twice.
# legacy_subdir: a dir an earlier fusion-cli release linked into before
# the agent's native standard-dir support was verified; setup sweeps
# OUR leftovers out of it (attribution-checked, like everything else).
AGENTS = [
    {"name": "Claude Code", "marker": ".claude",
     "skills_subdir": ".claude/skills", "mode": "link",
     "docs_url": "https://code.claude.com/docs/en/skills"},
    {"name": "Codex", "marker": ".codex",
     "skills_subdir": ".agents/skills", "mode": "standard",
     "legacy_subdir": ".codex/skills",
     "docs_url": "https://developers.openai.com/codex/skills"},
    {"name": "Pi", "marker": ".pi",
     "skills_subdir": ".agents/skills", "mode": "standard",
     "legacy_subdir": ".pi/agent/skills",
     "docs_url": "https://pi.dev/docs/latest/skills"},
    {"name": "Cursor", "marker": ".cursor",
     "skills_subdir": ".agents/skills", "mode": "standard",
     "docs_url": "https://cursor.com/docs/skills"},
    {"name": "Gemini CLI", "marker": ".gemini",
     "skills_subdir": ".agents/skills", "mode": "standard",
     "docs_url": "https://geminicli.com/docs/cli/skills"},
    {"name": "opencode", "marker": ".config/opencode",
     "skills_subdir": ".agents/skills", "mode": "standard",
     "docs_url": "https://opencode.ai/docs/skills"},
    {"name": "Goose", "marker": ".config/goose",
     "skills_subdir": ".agents/skills", "mode": "standard",
     "docs_url": "https://block.github.io/goose/docs/mcp/skills-mcp"},
]


def detect_agents(home: Path) -> list[dict]:
    found = []
    for row in AGENTS:
        if (home / row["marker"]).is_dir():
            entry = {**row, "skills_dir": home / row["skills_subdir"]}
            if "legacy_subdir" in row:
                entry["legacy_dir"] = home / row["legacy_subdir"]
            found.append(entry)
    return found


def _points_into(link: Path, canonical: Path) -> bool:
    try:
        return link.resolve().is_relative_to(canonical.resolve())
    except OSError:
        return False


def _sweep_legacy(agent: dict, canonical: Path) -> list[dict]:
    """Remove OUR leftovers from a dir an earlier release linked into.

    fusion-cli <= 1.2.0 symlinked (or copy-fell-back) into Pi's and
    Codex's own dirs; both agents read the canonical dir natively, so
    those entries double-loaded every skill. Attribution-checked:
    symlinks into the canonical and sentinel-marked copies are ours;
    anything else is left with a report row.
    """
    legacy = agent.get("legacy_dir")
    if legacy is None or not legacy.is_dir():
        return []
    results = []
    for entry in sorted(legacy.glob("fusion-*")):
        row = {"agent": agent["name"], "skill": entry.name}
        if entry.is_symlink() and _points_into(entry, canonical):
            entry.unlink()
            results.append({**row, "action": "unlinked",
                            "detail": f"{entry} — this agent reads the "
                                      f"standard dir; the extra link "
                                      f"double-loaded every skill"})
        elif (entry.is_dir() and not entry.is_symlink()
              and (entry / ".fusion-setup").is_file()):
            shutil.rmtree(entry)
            results.append({**row, "action": "unlinked",
                            "detail": f"{entry} — copy from an earlier "
                                      f"fusion-cli; this agent reads the "
                                      f"standard dir"})
        else:
            results.append({**row, "action": "left",
                            "detail": f"{entry} is not attributable to "
                                      f"setup — left in place"})
    return results


def fan_out(canonical: Path, agents: list[dict], force: bool) -> list[dict]:
    results = []
    skills = sorted(canonical.glob("fusion-*"))
    for agent in agents:
        if agent["mode"] == "standard":
            results.extend(_sweep_legacy(agent, canonical))
            if canonical.resolve() != agent["skills_dir"].resolve():
                detail = (f"reads ~/.agents/skills — but your skills are "
                          f"at {canonical}, which this agent does not read")
            else:
                detail = "reads ~/.agents/skills — nothing to do"
            results.append({"agent": agent["name"], "skill": "*",
                            "action": "standard", "detail": detail})
            continue
        if _points_into(agent["skills_dir"], canonical):
            results.append({
                "agent": agent["name"], "skill": "*", "action": "served",
                "detail": f"{agent['skills_dir']} resolves into "
                          f"{canonical} — the canonical install already "
                          f"serves this agent; nothing to link"})
            continue
        agent["skills_dir"].mkdir(parents=True, exist_ok=True)
        for skill in skills:
            target = agent["skills_dir"] / skill.name
            row = {"agent": agent["name"], "skill": skill.name}
            replaced = False
            if target.is_symlink():
                if _points_into(target, canonical):
                    results.append({**row, "action": "up-to-date",
                                    "detail": str(target)})
                    continue
                if not force:
                    results.append({**row, "action": "left",
                                    "detail": f"{target} links elsewhere — "
                                              f"--force replaces"})
                    continue
                target.unlink()
                replaced = True
            elif target.is_dir():
                if target.resolve() == skill.resolve():
                    results.append({**row, "action": "served",
                                    "detail": f"{target} already resolves "
                                              f"to the canonical skill"})
                    continue
                if tree_digest(target) == tree_digest(skill):
                    pass          # our current copy, refresh below keeps it current
                elif (target / ".fusion-setup").is_file():
                    pass          # our stale copy (sentinel proves provenance) — refresh
                elif not force:
                    results.append({**row, "action": "left",
                                    "detail": f"{target} exists and is not "
                                              f"ours — --force replaces"})
                    continue
                else:
                    replaced = True
                shutil.rmtree(target)
            elif target.exists():
                if not force:
                    results.append({**row, "action": "left",
                                    "detail": f"{target} is a file — "
                                              f"--force replaces"})
                    continue
                target.unlink()
                replaced = True
            try:
                os.symlink(skill, target, target_is_directory=True)
                results.append({**row,
                                "action": "replaced" if replaced else "linked",
                                "detail": str(target)})
            except OSError:
                shutil.copytree(skill, target)
                (target / ".fusion-setup").write_text(
                    f"{payload_version()}\n{tree_digest(skill)}\n",
                    encoding="utf-8", newline="\n")
                results.append({**row,
                                "action": "replaced" if replaced else "copied",
                                "detail": f"{target} (symlinks unavailable — "
                                          f"re-run setup after upgrades)"})
    return results


def remove_all(canonical: Path, home: Path) -> list[dict]:
    results = []
    for agent in detect_agents(home):
        if agent["mode"] == "standard":
            results.extend(_sweep_legacy(agent, canonical))
            continue
        if _points_into(agent["skills_dir"], canonical):
            continue  # entries here ARE the canonical skills; the
                      # canonical phase below removes them exactly once
        entries = (sorted(agent["skills_dir"].glob("fusion-*"))
                   if agent["skills_dir"].is_dir() else [])
        for entry in entries:
            row = {"agent": agent["name"], "skill": entry.name}
            if entry.is_symlink() and _points_into(entry, canonical):
                entry.unlink()
                results.append({**row, "action": "removed",
                                "detail": str(entry)})
            elif entry.is_dir() and not entry.is_symlink() \
                    and (canonical / entry.name).is_dir() \
                    and ((entry / ".fusion-setup").is_file()
                         or tree_digest(entry) == tree_digest(canonical / entry.name)):
                shutil.rmtree(entry)
                results.append({**row, "action": "removed",
                                "detail": str(entry)})
            else:
                results.append({**row, "action": "left",
                                "detail": f"{entry} is not attributable to "
                                          f"setup — left in place"})
    for skill in sorted(canonical.glob("fusion-*")):
        row = {"agent": "canonical", "skill": skill.name}
        if skill.is_symlink():
            results.append({**row, "action": "left",
                            "detail": f"{skill} is a symlink you manage"})
            continue
        shutil.rmtree(skill)
        results.append({**row, "action": "removed", "detail": str(skill)})
    return results


def environment_advice(home: Path) -> list[dict]:
    import os as _os
    import subprocess
    advice = []
    if shutil.which("fusion") is None:
        # spec §4d: fix PATH via uv's own mechanism when allowed
        if _os.environ.get("FUSION_NO_MODIFY_PATH") != "1" \
                and shutil.which("uv") is not None:
            done = subprocess.run(["uv", "tool", "update-shell"],
                                  capture_output=True).returncode == 0
            advice.append({
                "topic": "path",
                "text": "uv tool update-shell ran — restart your shell so "
                        "`fusion` resolves" if done else
                        "uv tool update-shell failed — add uv's tool bin "
                        "dir to PATH yourself (`uv tool dir --bin`)"})
        else:
            advice.append({
                "topic": "path",
                "text": "the uv tool bin dir is not on PATH — run: "
                        "uv tool update-shell (or manage PATH yourself)"})
    if shutil.which("git") is None:
        advice.append({
            "topic": "git",
            "text": "git not found — buckets are git repos; install git"})
    if shutil.which("soffice") is None:
        advice.append({
            "topic": "libreoffice",
            "text": "LibreOffice (soffice) not found — only docx/pptx/"
                    "legacy-office/html intake needs it "
                    "(brew install --cask libreoffice · apt install "
                    "libreoffice · winget install LibreOffice.LibreOffice)"})
    return advice


def run_setup(home: Path, skills_dir: Path, force: bool,
              no_agents: bool, remove: bool) -> dict:
    if remove:
        results = remove_all(skills_dir, home)
        return {"ok": True, "removed": results,
                "next": ["uv tool uninstall fusion-cli"]}
    payload = payload_root()
    skills = install_canonical(payload, skills_dir, force)
    agents = [] if no_agents else fan_out(
        skills_dir, detect_agents(home), force)
    return {
        "ok": True,
        "cli": {"version": payload_version()},
        "skills": {"dir": str(skills_dir), "results": skills},
        "agents": agents,
        "advice": environment_advice(home),
        "next": ["fusion new ~/buckets/personal --kind personal "
                 "--description \"Home base.\"",
                 "https://github.com/bluewaves-creations/fusion/blob/"
                 "main/docs/GETTING-STARTED.md"],
    }
