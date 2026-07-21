"""fusion check — conformance per SPEC §11. Liberal reader: reports, never raises."""

from __future__ import annotations

import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from . import hub, indexer, ledger, manifest
from .bucket import DOC_ZONES, REQUIRED_BUCKET_FIELDS, ZONES, load, iter_documents
from .document import AURORAS, FILENAME_RE, MAX_STEM

# SPEC §2, §11: output/ MAY hold non-markdown deliverables (exports); their
# filenames must still be lowercase-hyphen slugs, just with any lowercase
# extension rather than a hard-coded .md.
EXPORT_FILENAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*\.[a-z0-9]+$")

# SPEC §11 W6: sealed containers are delivery vehicles (fusion-intake
# unpacks and discards them at admit) — one never belongs committed.
CONTAINER_EXTS = (".athena", ".zip")

# SPEC §11 W7: GitHub's hard push limit is 100MB; warn a good margin before
# it, so a bucket never crosses it unpushable between one check and the next.
MAX_TRACKED_BYTES = 95 * 1024 * 1024


@dataclass
class Finding:
    level: str  # "error" | "warning"
    code: str  # E1..E8, W1..W8 — plus H1..H2 from check_hub (CLI vocabulary, not SPEC)
    path: str  # bucket-relative, "" when bucket-wide
    message: str


def _missing_fields(mapping: dict, fields: tuple[str, ...]) -> list[str]:
    """A required field is missing when absent, None, or blank."""
    return [
        f
        for f in fields
        if (value := mapping.get(f)) is None
        or (isinstance(value, str) and not value.strip())
    ]


def check(root: Path) -> list[Finding]:
    errors: list[Finding] = []
    errors += _e1_zones(root)
    errors += _e2_bucket_card(root)
    errors += _e3_e4_e5_documents(root)
    errors += _e6_ledger_verbs(root)
    errors += _e7_manifest(root)
    errors += _e8_filenames(root)
    warnings = _warnings(root)

    def key(f: Finding) -> tuple[str, str]:
        return (f.code, f.path)

    return sorted(errors, key=key) + sorted(warnings, key=key)


def _e1_zones(root: Path) -> list[Finding]:
    return [
        Finding("error", "E1", zone, f"zone missing from bucket root: {zone}/")
        for zone in ZONES
        if not (root / zone).is_dir()
    ]


def _e2_bucket_card(root: Path) -> list[Finding]:
    if not (root / "BUCKET.md").is_file():
        return [Finding("error", "E2", "BUCKET.md", "BUCKET.md missing")]
    b = load(root)
    if b.frontmatter is None:
        return [
            Finding(
                "error",
                "E2",
                "BUCKET.md",
                f"BUCKET.md frontmatter unreadable: {b.fm_error}",
            )
        ]
    return [
        Finding(
            "error", "E2", "BUCKET.md", f"BUCKET.md missing required field: {field}"
        )
        for field in _missing_fields(b.frontmatter, REQUIRED_BUCKET_FIELDS)
    ]


def _e3_e4_e5_documents(root: Path) -> list[Finding]:
    findings = []
    for zone, rel, doc in iter_documents(root):
        path = f"{zone}/{rel.as_posix()}"
        if doc.frontmatter is None:
            findings.append(
                Finding("error", "E3", path, f"unreadable frontmatter: {doc.fm_error}")
            )
            continue
        for field in _missing_fields(doc.frontmatter, ("title", "type", "aurora")):
            findings.append(
                Finding("error", "E3", path, f"missing required field: {field}")
            )
        aurora = doc.frontmatter.get("aurora")
        blank = isinstance(aurora, str) and not aurora.strip()
        if aurora is not None and not blank and aurora not in AURORAS:
            findings.append(
                Finding(
                    "error", "E4", path, f"aurora '{aurora}' is not one of the eight"
                )
            )
        if not doc.summary_first:
            findings.append(
                Finding(
                    "error",
                    "E5",
                    path,
                    "body is not summary-first (## Summary, then a --- line)",
                )
            )
    return findings


def _e6_ledger_verbs(root: Path) -> list[Finding]:
    return [
        Finding(
            "error", "E6", "LEDGER.md", f"unknown verb '{e.verb}' at {e.date} {e.time}"
        )
        for e in ledger.read(root)
        if e.verb not in ledger.VERBS
    ]


def _e7_manifest(root: Path) -> list[Finding]:
    sources = root / "sources"
    if not sources.is_dir():
        return []
    on_disk = {
        p.relative_to(sources).as_posix()
        for p in sources.rglob("*")
        if p.is_file()
        and p.name != "MANIFEST.md"
        and not any(part.startswith(".") for part in p.relative_to(sources).parts)
    }
    rows = {r.file for r in manifest.read(root)}
    findings = [
        Finding("error", "E7", f"sources/{f}", f"sources file has no manifest row: {f}")
        for f in sorted(on_disk - rows)
    ]
    findings += [
        Finding(
            "error",
            "E7",
            "sources/MANIFEST.md",
            f"manifest row's file is missing or invisible "
            f"(dot-directories are not scanned): {f}",
        )
        for f in sorted(rows - on_disk)
    ]
    return findings


def _e8_filenames(root: Path) -> list[Finding]:
    findings = []
    for zone in DOC_ZONES:
        zone_dir = root / zone
        if not zone_dir.is_dir():
            continue
        for p in sorted(zone_dir.rglob("*")):
            if (
                not p.is_file()
                or p.name == "INDEX.md"
                or any(part.startswith(".") for part in p.relative_to(zone_dir).parts)
            ):
                continue
            rel = f"{zone}/{p.relative_to(zone_dir).as_posix()}"
            if zone == "output" and p.suffix.lower() != ".md":
                if not EXPORT_FILENAME_RE.match(p.name):
                    findings.append(
                        Finding(
                            "error",
                            "E8",
                            rel,
                            "export filename must be a lowercase-hyphen slug "
                            "with a lowercase extension",
                        )
                    )
                elif len(p.stem) > MAX_STEM:
                    findings.append(
                        Finding(
                            "error",
                            "E8",
                            rel,
                            f"filename stem exceeds {MAX_STEM} characters",
                        )
                    )
                continue
            if not FILENAME_RE.match(p.name):
                findings.append(
                    Finding(
                        "error",
                        "E8",
                        rel,
                        "filename must be a lowercase-hyphen .md slug",
                    )
                )
            elif len(p.stem) > MAX_STEM:
                findings.append(
                    Finding(
                        "error",
                        "E8",
                        rel,
                        f"filename stem exceeds {MAX_STEM} characters",
                    )
                )
    return findings


def _warnings(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    findings += _w1_stale_inbox(root)
    findings += _w2_indexes(root)
    findings += _w3_w4_documents(root)
    findings += _w5_untouched_activities(root)
    findings += _w6_committed_containers(root)
    findings += _w7_large_tracked_files(root)
    findings += _w8_summary_only(root)
    return findings


def _tracked_files(root: Path) -> list[str] | None:
    """git-tracked paths, bucket-relative, POSIX-separated.

    None when `root` isn't a git repo or git is unavailable — the checker
    is a liberal reader (SPEC §0) and W6/W7 simply stay silent rather than
    raise; a bucket without git has no push to protect yet.
    """
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=root,
            capture_output=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    text = result.stdout.decode("utf-8", errors="surrogateescape")
    return [p for p in text.split("\0") if p]


def _w6_committed_containers(root: Path) -> list[Finding]:
    findings = []
    for rel in sorted(_tracked_files(root) or ()):
        if Path(rel).suffix.lower() not in CONTAINER_EXTS:
            continue
        if rel.startswith("inbox/"):
            findings.append(
                Finding(
                    "warning",
                    "W6",
                    rel,
                    "container committed in inbox/ — a delivery vehicle, not "
                    "an original; unpack it and discard it (fusion-intake's "
                    "admit route), then remove it from git",
                )
            )
        else:
            findings.append(
                Finding(
                    "warning",
                    "W6",
                    rel,
                    "sealed container committed — its content belongs "
                    "unpacked in sources/ + library/, not the archive itself; "
                    "remove it from git",
                )
            )
    return findings


def _w7_large_tracked_files(root: Path) -> list[Finding]:
    findings = []
    for rel in sorted(_tracked_files(root) or ()):
        path = root / rel
        if not path.is_file():
            continue
        size = path.stat().st_size
        if size > MAX_TRACKED_BYTES:
            mb = size / (1024 * 1024)
            findings.append(
                Finding(
                    "warning",
                    "W7",
                    rel,
                    f"tracked file is {mb:.1f}MB — GitHub's hard limit is "
                    "100MB and the bucket becomes unpushable; keep big "
                    "binaries in their native home and point to them "
                    "(resource:, §4) instead of committing them",
                )
            )
    return findings


def _w8_summary_only(root: Path) -> list[Finding]:
    # A pointer document (source:/resource: in frontmatter) is exempt —
    # its designed shape IS summary + pointer; the body is the thing it
    # points at, not missing prose.
    return [
        Finding(
            "warning",
            "W8",
            f"{zone}/{rel.as_posix()}",
            "document is only a summary — nothing beneath the closing "
            "separator and no source:/resource: pointer; write the "
            "body, point at the thing, or reconsider whether the "
            "document should exist",
        )
        for zone, rel, doc in iter_documents(root)
        if doc.summary_first
        and doc.summary_only
        and not (doc.frontmatter or {}).get("source")
        and not (doc.frontmatter or {}).get("resource")
    ]


def _w1_stale_inbox(root: Path) -> list[Finding]:
    inbox = root / "inbox"
    if not inbox.is_dir():
        return []
    max_age = load(root).inbox_max_age_days
    cutoff = time.time() - max_age * 86400
    return [
        Finding(
            "warning",
            "W1",
            f"inbox/{p.relative_to(inbox).as_posix()}",
            f"inbox file older than {max_age} days",
        )
        for p in sorted(inbox.rglob("*"))
        if p.is_file() and not p.name.startswith(".") and p.stat().st_mtime < cutoff
    ]


def _w2_indexes(root: Path) -> list[Finding]:
    findings = []
    for zone in indexer.INDEXED_ZONES:
        zone_dir = root / zone
        if not zone_dir.is_dir():
            continue
        index_path = zone_dir / "INDEX.md"
        rel = f"{zone}/INDEX.md"
        if not index_path.exists():
            findings.append(Finding("warning", "W2", rel, "INDEX.md missing"))
        elif index_path.read_bytes() != indexer.generate(zone_dir, zone).encode(
            "utf-8"
        ):
            findings.append(
                Finding("warning", "W2", rel, "INDEX.md stale — regeneration differs")
            )
    return findings


def _w3_w4_documents(root: Path) -> list[Finding]:
    findings = []
    for zone, rel, doc in iter_documents(root):
        path = f"{zone}/{rel.as_posix()}"
        on_archive_path = "archive" in rel.parts
        is_archive_aurora = doc.aurora == "archive"
        if on_archive_path and not is_archive_aurora:
            findings.append(
                Finding("warning", "W3", path, "archived path without aurora: archive")
            )
        elif is_archive_aurora and not on_archive_path:
            findings.append(
                Finding(
                    "warning", "W3", path, "aurora: archive outside an archive/ path"
                )
            )
        doc_dir = (root / zone / rel).parent
        for link in doc.links:
            target = link.split("#", 1)[0]
            if not target:
                continue
            if not (doc_dir / target).resolve().exists():
                findings.append(
                    Finding("warning", "W4", path, f"broken relative link: {link}")
                )
    return findings


def _w5_untouched_activities(root: Path) -> list[Finding]:
    entries = ledger.read(root)
    reflections = [i for i, e in enumerate(entries) if e.verb == "reflected"]
    if not reflections:
        return []
    start = reflections[-2] + 1 if len(reflections) >= 2 else 0
    findings = []
    for zone, rel, doc in iter_documents(root, zones=("activities",)):
        if doc.status != "active":
            continue
        doc_path = f"activities/{rel.as_posix()}"
        activity_dir = f"activities/{rel.parent.as_posix()}/"
        mentions = [
            i
            for i, e in enumerate(entries)
            if doc_path in e.obj or activity_dir in e.obj
        ]
        if any(start <= i < reflections[-1] for i in mentions):
            continue
        if mentions and mentions[0] > reflections[-1]:
            continue  # born after the reflection — not yet through a window
        findings.append(
            Finding(
                "warning",
                "W5",
                doc_path,
                "active activity with no ledger mention across the last "
                "reflection window",
            )
        )
    return findings


def check_hub() -> list[Finding]:
    """The hub's own audit — dangling entries and name drift.

    H-codes are CLI vocabulary, not SPEC conformance codes: the hub is a
    per-machine register and consumers must tolerate anything in it. All
    findings are warnings; a hub audit never fails.
    """
    findings: list[Finding] = []
    for entry in hub.load():
        root = hub.resolve(entry)
        if not (root / "BUCKET.md").is_file():
            findings.append(
                Finding(
                    "warning",
                    "H1",
                    entry.path,
                    f"'{entry.name}' — no bucket at this path; clone it "
                    f"there, or `fusion hub remove {entry.name}`",
                )
            )
            continue
        name = load(root).name
        if name and name != entry.name:
            findings.append(
                Finding(
                    "warning",
                    "H2",
                    entry.path,
                    f"hub says '{entry.name}' but BUCKET.md says '{name}' — "
                    "re-register: `fusion hub remove` then `fusion hub add`",
                )
            )
    return findings
