"""fusion status / today / agenda — the composed day (design spec §5)."""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from pathlib import Path

from . import bucket, hub, ledger
from .document import AURORAS


def filter_since(entries: list[ledger.Entry], since: str | None):
    if not since:
        return entries
    if since == "last-reflection":
        last = max(
            (i for i, e in enumerate(entries) if e.verb == "reflected"),
            default=None,
        )
        return entries if last is None else entries[last + 1 :]
    return [e for e in entries if e.date >= since]


def status(root: Path, since: str | None = None) -> dict:
    b = bucket.load(root)
    auroras: Counter = Counter()
    types: Counter = Counter()
    activities: Counter = Counter()
    total = 0
    for zone, rel, doc in bucket.iter_documents(root):
        total += 1
        auroras[doc.aurora or "—"] += 1
        types[doc.type or "—"] += 1
        if zone == "activities":
            activities[doc.status or "unset"] += 1
    entries = filter_since(ledger.read(root), since)
    return {
        "bucket": b.name or root.name,
        "documents": total,
        "auroras": dict(sorted(auroras.items())),
        "types": dict(sorted(types.items())),
        "activities": dict(sorted(activities.items())),
        "ledger": [asdict(e) for e in entries[-10:]],
    }


def _hub_buckets():
    """Yield (bucket_name, root) for every readable hub bucket — read means
    a BUCKET.md exists, not that the bucket holds any documents yet."""
    for entry in hub.load():
        root = hub.resolve(entry)
        if not (root / "BUCKET.md").is_file():
            continue
        b = bucket.load(root)
        yield (b.name or entry.name), root


def _hub_documents():
    """Yield (bucket_name, zone, rel, doc) across every readable hub bucket."""
    for name, root in _hub_buckets():
        for zone, rel, doc in bucket.iter_documents(root):
            yield name, zone, rel, doc


def _item(name: str, zone: str, rel, doc, date=None) -> dict:
    return {
        "bucket": name,
        "title": doc.title or rel.stem,
        "path": f"{zone}/{rel.as_posix()}",
        "type": doc.type,
        "aurora": doc.aurora,
        "status": doc.status,
        "date": date,
    }


def today() -> dict:
    groups: dict[str, list] = {}
    buckets: list[str] = []
    for name, root in _hub_buckets():
        buckets.append(name)
        for zone, rel, doc in bucket.iter_documents(root):
            if "archive" in rel.parts or doc.aurora == "archive":
                continue
            is_active_activity = zone == "activities" and doc.status == "active"
            is_commitment = doc.aurora == "commitments"
            if is_active_activity or is_commitment:
                groups.setdefault(doc.aurora or "—", []).append(
                    _item(name, zone, rel, doc)
                )
    ordered = {a: groups[a] for a in AURORAS if a in groups}
    for aurora, items in groups.items():
        if aurora not in ordered:
            ordered[aurora] = items
    return {"buckets": buckets, "groups": ordered}


def agenda() -> dict:
    dated: list[dict] = []
    active: list[dict] = []
    for name, zone, rel, doc in _hub_documents():
        if "archive" in rel.parts or doc.aurora == "archive":
            continue
        fm = doc.frontmatter or {}
        raw = fm.get("due") or fm.get("date")
        if raw is not None:
            dated.append(_item(name, zone, rel, doc, date=str(raw)[:10]))
        elif zone == "activities" and doc.status == "active":
            active.append(_item(name, zone, rel, doc))
    dated.sort(key=lambda i: i["date"])
    return {"dated": dated, "active": active}
