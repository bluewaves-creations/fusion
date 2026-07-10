"""fusion check — conformance per SPEC §11. Liberal reader: reports, never raises."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import ledger, manifest
from .bucket import DOC_ZONES, REQUIRED_BUCKET_FIELDS, ZONES, load, iter_documents
from .document import AURORAS, FILENAME_RE, MAX_STEM


@dataclass
class Finding:
    level: str  # "error" | "warning"
    code: str   # E1..E8, W1..W5
    path: str   # bucket-relative, "" when bucket-wide
    message: str


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
        for field in REQUIRED_BUCKET_FIELDS
        if field not in b.frontmatter
    ]


def _e3_e4_e5_documents(root: Path) -> list[Finding]:
    findings = []
    for zone, rel, doc in iter_documents(root):
        path = f"{zone}/{rel.as_posix()}"
        if doc.frontmatter is None:
            findings.append(Finding("error", "E3", path,
                                    f"unreadable frontmatter: {doc.fm_error}"))
            continue
        for field in ("title", "type", "aurora"):
            if field not in doc.frontmatter:
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
    return []  # W1–W5 land in the next task
