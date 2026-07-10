"""fusion check — conformance per SPEC §11. Liberal reader: reports, never raises."""
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path

from . import indexer, ledger, manifest
from .bucket import DOC_ZONES, REQUIRED_BUCKET_FIELDS, ZONES, load, iter_documents
from .document import AURORAS, FILENAME_RE, MAX_STEM

# SPEC §2, §11: output/ MAY hold non-markdown deliverables (exports); their
# filenames must still be lowercase-hyphen slugs, just with any lowercase
# extension rather than a hard-coded .md.
EXPORT_FILENAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*\.[a-z0-9]+$")


@dataclass
class Finding:
    level: str  # "error" | "warning"
    code: str   # E1..E8, W1..W5
    path: str   # bucket-relative, "" when bucket-wide
    message: str


def _missing_fields(mapping: dict, fields: tuple[str, ...]) -> list[str]:
    """A required field is missing when absent, None, or blank."""
    return [
        f for f in fields
        if mapping.get(f) is None
        or (isinstance(mapping.get(f), str) and not mapping.get(f).strip())
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
    key = lambda f: (f.code, f.path)
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
        return [Finding("error", "E2", "BUCKET.md",
                        f"BUCKET.md frontmatter unreadable: {b.fm_error}")]
    return [
        Finding("error", "E2", "BUCKET.md",
                f"BUCKET.md missing required field: {field}")
        for field in _missing_fields(b.frontmatter, REQUIRED_BUCKET_FIELDS)
    ]


def _e3_e4_e5_documents(root: Path) -> list[Finding]:
    findings = []
    for zone, rel, doc in iter_documents(root):
        path = f"{zone}/{rel.as_posix()}"
        if doc.frontmatter is None:
            findings.append(Finding("error", "E3", path,
                                    f"unreadable frontmatter: {doc.fm_error}"))
            continue
        for field in _missing_fields(doc.frontmatter, ("title", "type", "aurora")):
            findings.append(Finding("error", "E3", path,
                                    f"missing required field: {field}"))
        aurora = doc.frontmatter.get("aurora")
        if aurora is not None and aurora not in AURORAS:
            findings.append(Finding("error", "E4", path,
                                    f"aurora '{aurora}' is not one of the eight"))
        if not doc.summary_first:
            findings.append(Finding(
                "error", "E5", path,
                "body is not summary-first (## Summary, then a --- line)"))
    return findings


def _e6_ledger_verbs(root: Path) -> list[Finding]:
    return [
        Finding("error", "E6", "LEDGER.md",
                f"unknown verb '{e.verb}' at {e.date} {e.time}")
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
        if p.is_file() and p.name != "MANIFEST.md"
        and not p.name.startswith(".")
    }
    rows = {r.file for r in manifest.read(root)}
    findings = [
        Finding("error", "E7", f"sources/{f}",
                f"sources file has no manifest row: {f}")
        for f in sorted(on_disk - rows)
    ]
    findings += [
        Finding("error", "E7", "sources/MANIFEST.md",
                f"manifest row's file is gone: {f}")
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
            if not p.is_file() or p.name == "INDEX.md" or p.name.startswith("."):
                continue
            rel = f"{zone}/{p.relative_to(zone_dir).as_posix()}"
            if zone == "output" and p.suffix.lower() != ".md":
                if not EXPORT_FILENAME_RE.match(p.name):
                    findings.append(Finding(
                        "error", "E8", rel,
                        "export filename must be a lowercase-hyphen slug "
                        "with a lowercase extension"))
                elif len(p.stem) > MAX_STEM:
                    findings.append(Finding(
                        "error", "E8", rel,
                        f"filename stem exceeds {MAX_STEM} characters"))
                continue
            if not FILENAME_RE.match(p.name):
                findings.append(Finding(
                    "error", "E8", rel,
                    "filename must be a lowercase-hyphen .md slug"))
            elif len(p.stem) > MAX_STEM:
                findings.append(Finding(
                    "error", "E8", rel,
                    f"filename stem exceeds {MAX_STEM} characters"))
    return findings


def _warnings(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    findings += _w1_stale_inbox(root)
    findings += _w2_indexes(root)
    findings += _w3_w4_documents(root)
    findings += _w5_untouched_activities(root)
    return findings


def _w1_stale_inbox(root: Path) -> list[Finding]:
    inbox = root / "inbox"
    if not inbox.is_dir():
        return []
    max_age = load(root).inbox_max_age_days
    cutoff = time.time() - max_age * 86400
    return [
        Finding("warning", "W1", f"inbox/{p.relative_to(inbox).as_posix()}",
                f"inbox file older than {max_age} days")
        for p in sorted(inbox.rglob("*"))
        if p.is_file() and not p.name.startswith(".")
        and p.stat().st_mtime < cutoff
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
        elif index_path.read_bytes() != indexer.generate(zone_dir, zone).encode("utf-8"):
            findings.append(Finding("warning", "W2", rel,
                                    "INDEX.md stale — regeneration differs"))
    return findings


def _w3_w4_documents(root: Path) -> list[Finding]:
    findings = []
    for zone, rel, doc in iter_documents(root):
        path = f"{zone}/{rel.as_posix()}"
        on_archive_path = "archive" in rel.parts
        is_archive_aurora = doc.aurora == "archive"
        if on_archive_path and not is_archive_aurora:
            findings.append(Finding("warning", "W3", path,
                                    "archived path without aurora: archive"))
        elif is_archive_aurora and not on_archive_path:
            findings.append(Finding("warning", "W3", path,
                                    "aurora: archive outside an archive/ path"))
        doc_dir = (root / zone / rel).parent
        for link in doc.links:
            target = link.split("#", 1)[0]
            if not target:
                continue
            if not (doc_dir / target).resolve().exists():
                findings.append(Finding("warning", "W4", path,
                                        f"broken relative link: {link}"))
    return findings


def _w5_untouched_activities(root: Path) -> list[Finding]:
    entries = ledger.read(root)
    reflections = [i for i, e in enumerate(entries) if e.verb == "reflected"]
    if len(reflections) < 2:
        return []
    window = entries[reflections[-2] + 1 : reflections[-1]]
    findings = []
    for zone, rel, doc in iter_documents(root, zones=("activities",)):
        if doc.status != "active":
            continue
        doc_path = f"activities/{rel.as_posix()}"
        activity_dir = f"activities/{rel.parent.as_posix()}/"
        mentioned = any(
            doc_path in e.obj or activity_dir in e.obj for e in window
        )
        if not mentioned:
            findings.append(Finding(
                "warning", "W5", doc_path,
                "active activity with no ledger mention across the last "
                "reflection window"))
    return findings
