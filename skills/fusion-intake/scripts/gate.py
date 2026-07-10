#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""fusion-intake Stage 1 — the deterministic gate classifier.

Hashes every file in inbox/, compares against the sources/ tree, normalizes
filenames, scores content similarity, and writes a gate manifest with four
buckets: exact_dups, near_dups, update_candidates, clean_new. It classifies
and reports — it never writes to sources/ or library/. Stage 2 (the agent,
references/gate.md) assigns the final class and asks the human where the
locked rule requires it.

Usage:
    uv run <skill>/scripts/gate.py --bucket <bucket-root> [--out <path>]
"""
import argparse
import hashlib
import json
import re
import subprocess
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# Locked lineage thresholds (doc-converter, kept verbatim).
NEAR_DUP_THRESHOLD = 0.85   # best content sim >= this (and not exact) -> near-dup
UPDATE_SIM_FLOOR = 0.30     # [floor, near): name match -> update candidate
SHINGLE_K = 3               # word-shingle size for similarity

_DATE_PREFIX = re.compile(r"^(?:\d{4}-\d{2}-\d{2}|\d{8})[_-]")
_SEP_RUN = re.compile(r"[\s_-]+")
_WORD = re.compile(r"\w+")

SKIP_NAMES = {"MANIFEST.md", "README.md"}


def normalize_filename(name: str) -> str:
    """Strip a leading date prefix, lowercase, collapse separators to '-',
    drop the extension."""
    stem = Path(name).stem
    stem = _DATE_PREFIX.sub("", stem)
    stem = stem.lower()
    stem = _SEP_RUN.sub("-", stem).strip("-")
    return stem


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_text(path: Path) -> str:
    """Text for similarity scoring. Binary formats decode to noise and
    effectively compare on filename only — full content comparison is
    Stage 2's judgment work."""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


@dataclass
class SourceIndex:
    by_hash: dict = field(default_factory=lambda: defaultdict(list))
    by_name: dict = field(default_factory=lambda: defaultdict(list))
    text_by_path: dict = field(default_factory=dict)


def _iter_files(root: Path):
    for p in sorted(root.rglob("*")):
        if p.is_file() and not p.name.startswith(".") and p.name not in SKIP_NAMES:
            yield p


def index_sources(sources_dir: Path) -> SourceIndex:
    idx = SourceIndex()
    sources_dir = Path(sources_dir)
    for p in _iter_files(sources_dir):
        rel = str(p.relative_to(sources_dir))
        idx.by_hash[sha256_of(p)].append(rel)
        idx.by_name[normalize_filename(p.name)].append(rel)
        idx.text_by_path[rel] = extract_text(p)
    return idx


def _shingles(text: str, k: int = SHINGLE_K) -> set:
    """Produce word k-shingles from text. Texts below k word tokens yield NO
    shingles—there is no linguistic evidence at sub-k thresholds by design."""
    tokens = _WORD.findall(text.lower())
    if len(tokens) < k:
        return set()
    return {" ".join(tokens[i:i + k]) for i in range(len(tokens) - k + 1)}


def similarity(a: str, b: str) -> float:
    """Jaccard over word k-shingles: 0.0 disjoint .. 1.0 identical. Texts
    under SHINGLE_K words always score 0.0—no evidence, not identity. Exact
    duplicates are sha256's catch upstream, not this function's."""
    sa, sb = _shingles(a), _shingles(b)
    if not sa or not sb:
        return 0.0
    union = len(sa | sb)
    return len(sa & sb) / union if union else 0.0


def git_history(path: Path, cwd: Path, limit: int = 10) -> list:
    """Prior-version evidence via git log --follow; [] outside a repo or on
    any failure (liberal reader)."""
    try:
        out = subprocess.run(
            ["git", "log", "--follow", "--date=short",
             f"-n{limit}", "--format=%ad\t%s", "--", str(path)],
            cwd=str(cwd), capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if out.returncode != 0:
        return []
    history = []
    for line in out.stdout.splitlines():
        date, _, subject = line.partition("\t")
        if date:
            history.append({"date": date, "subject": subject})
    return history


def _best_match(incoming_text: str, idx: SourceIndex):
    """Best (path, sim) over ALL sources — catches renamed near-dups."""
    best_path, best_sim = None, 0.0
    for path, src_text in idx.text_by_path.items():
        s = similarity(incoming_text, src_text)
        if s >= best_sim:
            best_path, best_sim = path, s
    return best_path, best_sim


def classify_intake(inbox_dir: Path, sources_dir: Path, idx: SourceIndex) -> dict:
    result = {"exact_dups": [], "near_dups": [],
              "update_candidates": [], "clean_new": []}
    for f in _iter_files(Path(inbox_dir)):
        rel = str(f.relative_to(inbox_dir))
        h = sha256_of(f)

        if h in idx.by_hash:
            result["exact_dups"].append({
                "incoming": rel,
                "matched_source": idx.by_hash[h][0],
                "hash": h,
                "auto_skip": True,
            })
            continue

        name_match = normalize_filename(f.name) in idx.by_name
        match_path, sim = _best_match(extract_text(f), idx)

        if match_path is not None and sim >= NEAR_DUP_THRESHOLD:
            result["near_dups"].append({
                "incoming": rel, "matched_source": match_path,
                "similarity": round(sim, 4), "auto_skip": False,
            })
        elif match_path is not None and sim >= UPDATE_SIM_FLOOR and name_match:
            result["update_candidates"].append({
                "incoming": rel, "matched_source": match_path,
                "similarity": round(sim, 4),
                "history": git_history(Path("sources") / match_path,
                                       Path(sources_dir).parent),
                "auto_skip": False,
            })
        elif match_path is not None and sim >= UPDATE_SIM_FLOOR:
            result["near_dups"].append({
                "incoming": rel, "matched_source": match_path,
                "similarity": round(sim, 4), "auto_skip": False,
            })
        else:
            result["clean_new"].append({"incoming": rel})
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="fusion-intake Stage-1 gate classifier")
    ap.add_argument("--bucket", required=True, help="bucket root")
    ap.add_argument("--out", help="manifest path "
                    "(default: <bucket>/workbench/.intake/gate-<runid>.json)")
    args = ap.parse_args(argv)

    root = Path(args.bucket).expanduser().resolve()
    inbox, sources = root / "inbox", root / "sources"
    if not inbox.is_dir() or not sources.is_dir():
        print(f"not a bucket (no inbox/ + sources/): {root}")
        return 1

    idx = index_sources(sources)
    buckets = classify_intake(inbox, sources, idx)
    manifest = {
        "version": 1,
        "counts": {k: len(v) for k, v in buckets.items()},
        "buckets": buckets,
    }
    out = Path(args.out) if args.out else (
        root / "workbench" / ".intake" / f"gate-{uuid.uuid4().hex[:12]}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"gate: {manifest['counts']} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
