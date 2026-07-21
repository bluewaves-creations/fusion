#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "PyYAML>=6.0",
# ]
# ///
"""fusion-librarian link repair — scan proposes, the human approves, apply
signs off.

Productizes the pattern run by hand during the 2026-07-10 delivery: 67
broken relative links repaired across two passes on a real bucket
(docs/dogfood/frictions.md row 7). `scan` never writes — it walks
library/ and activities/, finds relative links whose target does not
exist from the doc's own directory, and proposes a repair by basename
match against sources/ + the doc zones: a UNIQUE basename match is
`exact`; a unique match only after lowercase/hyphen-insensitive
normalization is `fuzzy` — never silently folded into an exact batch;
two or more candidates is `unrepairable` (never guess between them).

`apply` rewrites ONLY the pairs the human hands back in an approved
proposals file, validating every pair (doc inside library/ or
activities/, target exists, no path escapes the bucket) BEFORE writing
any of them — the intake gate's validate-before-damage discipline. It
writes no ledger entry: the gear's protocol (references/cross-reference.md)
has the operator sign one `noted` for the pass and re-run `fusion
index`/`fusion check`.

Usage:
    uv run link-repair.py scan --bucket <bucket-root> > proposals.json
    uv run link-repair.py apply --bucket <bucket-root> --proposals <file.json>
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import yaml

TODAY = datetime.now().strftime("%Y-%m-%d")

# Documents that can carry broken links worth repairing — never output/
# (deliverables are frozen) and never a zone outside the doc format.
DOC_ZONES = ("library", "activities")

# Where a repair candidate may be found: the doc zones themselves (a link
# that drifted to a sibling that moved) plus sources/ (the assets/X ->
# sources/... pattern proven live).
SEARCH_ZONES = ("sources", "library", "activities")

# Registers with a single writer elsewhere — never a link-repair target
# or a document to scan for links.
SKIP_NAMES = {"MANIFEST.md", "INDEX.md"}

# `](target)` — target's first char excludes ')' and '#' so bare anchor
# links ([x](#heading)) never match; http(s)/mailto are filtered after,
# by scheme, since they share the same bracket-paren shape.
LINK_RE = re.compile(r"\]\(([^)#][^)]*)\)")
_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")

# CommonMark §6.3: a destination may sit in <angle brackets>, and a
# "…"/'…' title may follow after whitespace — neither is part of the
# path, and the title must survive a rewrite untouched.
_DEST_RE = re.compile(
    r"^(?:<(?P<angled>[^>]*)>|(?P<bare>[^\s<]\S*))"
    r"(?P<title>\s+(?:\"[^\"]*\"|'[^']*'))?$"
)


def _split_destination(raw: str):
    """Return (path-ish destination, title suffix to preserve on
    rewrite) — liberal: text matching no known shape IS the destination."""
    m = _DEST_RE.match(raw.strip())
    if not m:
        return raw.strip(), ""
    dest = m.group("angled")
    if dest is None:
        dest = m.group("bare")
    return dest, m.group("title") or ""


# Code is not prose: fenced blocks and inline code spans never carry a
# real relative link, so they're blanked out before extraction — the
# same fix as cli/src/fusion/document.py's `_blank_code` (twin
# implementation, kept independent so this skill stays self-contained).
_FENCE_OPEN_RE = re.compile(r"^(\s*)(`{3,}|~{3,})")
_INLINE_CODE_RE = re.compile(r"(`+)((?:(?!\1)[^\n])*?)\1")


def _blank_code(body: str) -> str:
    """Blank fenced blocks (opener to closer inclusive, unterminated
    fences swallow to EOF) and single-line inline code spans, replacing
    each with equal-length whitespace so link extraction never reads
    code as prose. Inline spans use a run of N backticks as delimiter
    (CommonMark's literal-backtick idiom, e.g.
    `` `` `code with ` backtick` `` ``), closing only on the next run of
    the SAME length, so a shorter backtick run inside the span is just
    content, not a terminator."""
    lines = body.split("\n")
    out = []
    i = 0
    n = len(lines)
    while i < n:
        opener = _FENCE_OPEN_RE.match(lines[i])
        if not opener:
            out.append(lines[i])
            i += 1
            continue
        fence_char, fence_len = opener.group(2)[0], len(opener.group(2))
        closer_re = re.compile(
            r"^\s*" + re.escape(fence_char) + "{" + str(fence_len) + ",}\\s*$"
        )
        out.append(" " * len(lines[i]))
        i += 1
        while i < n:
            out.append(" " * len(lines[i]))
            closed = bool(closer_re.match(lines[i]))
            i += 1
            if closed:
                break
    blanked = "\n".join(out)
    return _INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), blanked)


class RepairError(Exception):
    """Strict-writer refusal — named loudly, never silently skipped."""


# ── discovery ────────────────────────────────────────────────────────────


def _iter_files(zone_dir: Path):
    for p in sorted(zone_dir.rglob("*")):
        if not p.is_file() or p.name in SKIP_NAMES:
            continue
        rel = p.relative_to(zone_dir)
        if any(part.startswith(".") for part in rel.parts):
            continue
        yield p


def _iter_docs(root: Path):
    """Every .md in library/ and activities/, skipping dot-dirs and the
    generated INDEX.md — hand-editing a register is never on the table."""
    for zone in DOC_ZONES:
        zone_dir = root / zone
        if not zone_dir.is_dir():
            continue
        for p in _iter_files(zone_dir):
            if p.suffix.lower() == ".md":
                yield p


def _normalize(name: str) -> str:
    """Lowercase, hyphen-insensitive basename key: case differences and
    hyphen placement collapse to the same key (amua-map.png and
    a-mua-map.png both key to 'amuamap.png') — a fuzzy match, extension
    still required so unrelated files never collide."""
    stem = Path(name).stem.lower().replace("-", "")
    ext = Path(name).suffix.lower()
    return f"{stem}{ext}"


def _index_candidates(root: Path):
    """basename -> [bucket-relative paths] and normalized-basename ->
    [...] over sources/ + the doc zones — the search space link-repair
    is allowed to propose targets from."""
    exact: dict[str, list[Path]] = {}
    normalized: dict[str, list[Path]] = {}
    for zone in SEARCH_ZONES:
        zone_dir = root / zone
        if not zone_dir.is_dir():
            continue
        for p in _iter_files(zone_dir):
            rel = p.relative_to(root)
            exact.setdefault(p.name, []).append(rel)
            normalized.setdefault(_normalize(p.name), []).append(rel)
    return exact, normalized


def _extract_links(text: str):
    """Yield (raw_target, path_part, anchor, title) for every candidate
    relative link — http(s)/mailto skipped by scheme (checked after the
    peel, so <https://…> is caught too), anchor-only already excluded by
    LINK_RE's negative first-char class, and fenced/inline code blanked
    first so code is never read as prose."""
    for m in LINK_RE.finditer(_blank_code(text)):
        target = m.group(1)
        dest, title = _split_destination(target)
        if _SCHEME_RE.match(dest):
            continue
        path_part, _, anchor = dest.partition("#")
        if not path_part:
            continue
        yield target, path_part, anchor, title


# ── scan ─────────────────────────────────────────────────────────────────


def scan(root: Path) -> dict:
    root = Path(root)
    exact_idx, normalized_idx = _index_candidates(root)
    proposals, unrepairable = [], []

    for doc in _iter_docs(root):
        doc_rel = doc.relative_to(root).as_posix()
        text = doc.read_text(encoding="utf-8", errors="replace")
        for raw_target, path_part, anchor, title in _extract_links(text):
            if (doc.parent / path_part).exists():
                continue  # not broken

            basename = Path(path_part).name
            candidates = exact_idx.get(basename, [])
            confidence = None
            chosen = None
            if len(candidates) == 1:
                confidence, chosen = "exact", candidates[0]
            else:
                norm_candidates = normalized_idx.get(_normalize(basename), [])
                if len(norm_candidates) == 1:
                    confidence, chosen = "fuzzy", norm_candidates[0]

            if chosen is None:
                unrepairable.append({"doc": doc_rel, "link": raw_target})
                continue

            new_path = os.path.relpath(root / chosen, start=doc.parent)
            target = (
                new_path.replace(os.sep, "/") + (f"#{anchor}" if anchor else "") + title
            )
            proposals.append(
                {
                    "doc": doc_rel,
                    "link": raw_target,
                    "target": target,
                    "confidence": confidence,
                }
            )

    return {"proposals": proposals, "unrepairable": unrepairable}


def _print_table(result: dict) -> None:
    exact = [p for p in result["proposals"] if p["confidence"] == "exact"]
    fuzzy = [p for p in result["proposals"] if p["confidence"] == "fuzzy"]

    def _rows(items):
        for p in items:
            print(f"  {p['doc']}: {p['link']} -> {p['target']}", file=sys.stderr)

    print(f"EXACT ({len(exact)}) — safe to apply as-is", file=sys.stderr)
    _rows(exact)
    print(
        f"\nFUZZY ({len(fuzzy)}) — normalized match only, "
        "confirm per group before applying",
        file=sys.stderr,
    )
    _rows(fuzzy)
    print(
        f"\nUNREPAIRABLE ({len(result['unrepairable'])}) — "
        "ambiguous or no candidate, never guessed",
        file=sys.stderr,
    )
    for u in result["unrepairable"]:
        print(f"  {u['doc']}: {u['link']}", file=sys.stderr)


# ── apply ────────────────────────────────────────────────────────────────


def _split_frontmatter(text: str, doc_rel: str):
    if not text.startswith("---\n"):
        raise RepairError(f"no frontmatter block: {doc_rel}")
    try:
        end = text.index("\n---", 4)
    except ValueError:
        raise RepairError(f"unterminated frontmatter block: {doc_rel}") from None
    fm = yaml.safe_load(text[4:end])
    if not isinstance(fm, dict):
        raise RepairError(f"frontmatter is not a mapping: {doc_rel}")
    return fm, text[end + 4 :]


def _bump_updated(text: str, doc_rel: str) -> str:
    fm, rest = _split_frontmatter(text, doc_rel)
    fm["updated"] = TODAY
    front = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, width=2**31 - 1)
    return f"---\n{front}---{rest}"


def apply_proposals(root: Path, proposals: list) -> int:
    """Rewrite ONLY the given (doc, link) -> target pairs. Validates every
    pair — doc under library/ or activities/, doc not a single-writer
    register (SKIP_NAMES), doc exists, the literal `](link)` text is
    present, target resolves inside the bucket and exists on disk, AND the
    doc's frontmatter parses — BEFORE writing any file
    (validate-all-before-damage, the intake gate's rule applied here). The
    frontmatter check runs in phase 1 specifically so a later doc's
    malformed frontmatter can never be discovered mid-write, after an
    earlier doc in the same batch was already rewritten: phase 2's own
    _bump_updated call stays as a safety net, but by construction it can
    no longer raise."""
    root = Path(root).resolve()
    zone_roots = {zone: (root / zone).resolve() for zone in DOC_ZONES}

    # ── phase 1: validate every pair, read but never write ───────────────
    plan: dict[Path, list[tuple[str, str]]] = {}
    doc_texts: dict[Path, str] = {}
    frontmatter_checked: set[Path] = set()
    for i, p in enumerate(proposals):
        doc_rel = p["doc"]
        link = p["link"]
        target = p["target"]
        doc_path = (root / doc_rel).resolve()
        if doc_path.name in SKIP_NAMES:
            raise RepairError(
                f"proposals[{i}]: refuses a single-writer register, "
                f"never a repair target (skip: {doc_rel!r})"
            )
        if not any(doc_path.is_relative_to(z) for z in zone_roots.values()):
            raise RepairError(
                f"proposals[{i}]: doc outside library/ or activities/: {doc_rel!r}"
            )
        if not doc_path.is_file():
            raise RepairError(f"proposals[{i}]: doc does not exist: {doc_rel!r}")

        dest, _ = _split_destination(target)
        target_path_part, _, _ = dest.partition("#")
        target_abs = (doc_path.parent / target_path_part).resolve()
        if not target_abs.is_relative_to(root):
            raise RepairError(f"proposals[{i}]: target escapes the bucket: {target!r}")
        if not target_abs.is_file():
            raise RepairError(
                f"proposals[{i}]: target does not exist: {target!r} (doc {doc_rel!r})"
            )

        text = doc_texts.setdefault(doc_path, doc_path.read_text(encoding="utf-8"))
        if f"]({link})" not in text:
            raise RepairError(
                f"proposals[{i}]: link text not found verbatim in {doc_rel!r}: {link!r}"
            )

        if doc_path not in frontmatter_checked:
            # Raises RepairError (unparseable/missing frontmatter) before
            # any document in this batch has been written — the same
            # parse _bump_updated would otherwise only attempt in phase 2,
            # by which point earlier docs could already be on disk.
            _split_frontmatter(text, doc_rel)
            frontmatter_checked.add(doc_path)

        plan.setdefault(doc_path, []).append((link, target))

    # ── phase 2: execute — every pair already validated ───────────────────
    changed = 0
    for doc_path, edits in plan.items():
        rel = doc_path.relative_to(root).as_posix()
        text = doc_texts[doc_path]
        new_text = text
        for link, target in edits:
            new_text = new_text.replace(f"]({link})", f"]({target})")
        if new_text != text:
            new_text = _bump_updated(new_text, rel)
            doc_path.write_text(new_text, encoding="utf-8", newline="\n")
            changed += 1
    return changed


# ── CLI ──────────────────────────────────────────────────────────────────


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="fusion-librarian link-repair: scan / apply"
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser(
        "scan",
        help="propose repairs for broken relative links in library/ and activities/",
    )
    p.add_argument("--bucket", required=True)

    p = sub.add_parser("apply", help="apply an approved subset of a scan's proposals")
    p.add_argument("--bucket", required=True)
    p.add_argument(
        "--proposals",
        required=True,
        help='JSON file: {"proposals": [...]} or a bare list',
    )

    args = ap.parse_args(argv)
    root = Path(args.bucket).expanduser()

    try:
        if args.cmd == "scan":
            result = scan(root)
            _print_table(result)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            payload = json.loads(Path(args.proposals).read_text(encoding="utf-8"))
            proposals = payload["proposals"] if isinstance(payload, dict) else payload
            changed = apply_proposals(root, proposals)
            print(json.dumps({"changed": changed}, indent=2, ensure_ascii=False))
    except RepairError as exc:
        print(f"link-repair: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
