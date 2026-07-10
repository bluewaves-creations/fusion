"""fusion — the notary. Records, checks, composes; never judges."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from . import __version__, bucket, checker, hub, indexer, ledger, scaffold, views


# ── plumbing ─────────────────────────────────────────────────────────────

def _fail(message: str) -> int:
    print(f"fusion: {message}", file=sys.stderr)
    return 1


def _emit(payload, as_json: bool, human: str) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    elif human:
        print(human)


def _root_from(args, attr: str = "path") -> Path | None:
    """Resolve the bucket root from a positional path / --bucket / cwd."""
    explicit = getattr(args, attr, None)
    if explicit:
        root = Path(explicit).expanduser()
        return root if root.is_dir() else None
    return bucket.find_root(Path.cwd())


def _parse_at(raw: str | None) -> datetime | None:
    return datetime.strptime(raw, "%Y-%m-%d %H:%M") if raw else None


# ── commands ─────────────────────────────────────────────────────────────

def cmd_new(args) -> int:
    actor = ledger.resolve_actor(args.as_)
    try:
        root, warnings = scaffold.new_bucket(
            Path(args.path), name=args.name, kind=args.kind,
            description=args.description, actor=actor,
        )
    except scaffold.ScaffoldError as exc:
        return _fail(str(exc))
    name = args.name or root.name
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    _emit(
        {"bucket": name, "path": str(root), "warnings": warnings},
        args.json,
        f"bucket '{name}' born at {root} — registered in the hub. Go live in it.",
    )
    return 0


def cmd_hub(args) -> int:
    if args.hub_cmd == "add":
        root = Path(args.path).expanduser().resolve()
        b = bucket.load(root)
        if b.frontmatter is None:
            return _fail(f"not a bucket (no readable BUCKET.md): {root}")
        missing = [f for f in ("name", "kind", "description")
                   if not str(b.frontmatter.get(f) or "").strip()]
        if missing:
            return _fail(f"BUCKET.md missing: {', '.join(missing)}")
        try:
            hub.add(hub.HubEntry(b.name, b.kind, hub.display_path(root),
                                  b.description))
        except ValueError as exc:
            return _fail(str(exc))
        _emit({"registered": b.name}, args.json,
              f"'{b.name}' registered in the hub.")
        return 0
    if args.hub_cmd == "remove":
        if not hub.remove(args.name):
            return _fail(f"no bucket named '{args.name}' in the hub")
        _emit({"removed": args.name}, args.json,
              f"'{args.name}' retired from the hub. The files live on.")
        return 0
    entries = hub.load()
    human = "\n".join(
        f"- **{e.name}** · {e.kind} · {e.path} — {e.description}"
        for e in entries
    ) or "the hub is empty — `fusion new` a bucket."
    _emit([asdict(e) for e in entries], args.json, human)
    return 0


def cmd_log(args) -> int:
    root = _root_from(args, "bucket")
    if root is None or not (root / "BUCKET.md").is_file():
        return _fail("not inside a bucket (no BUCKET.md found) — use --bucket")
    if args.verb is None:
        entries = views.filter_since(ledger.read(root), args.since)
        human = "\n".join(
            f"{e.date} {ledger.format_line(e)[2:]}" for e in entries
        ) or "the ledger is empty — nothing has happened yet."
        _emit([asdict(e) for e in entries], args.json, human)
        return 0
    if args.object is None:
        return _fail("log needs an object: fusion log <verb> <object>")
    actor = ledger.resolve_actor(args.as_)
    try:
        entry = ledger.append(root, actor, args.verb, args.object,
                              note=args.note, at=_parse_at(args.at))
    except ValueError as exc:
        return _fail(str(exc))
    _emit(asdict(entry), args.json,
          f"logged: {entry.date} {ledger.format_line(entry)[2:]}")
    return 0


def cmd_index(args) -> int:
    root = _root_from(args)
    if root is None or not (root / "BUCKET.md").is_file():
        return _fail("not inside a bucket (no BUCKET.md found)")
    actor = ledger.resolve_actor(args.as_)
    results = indexer.write_indexes(root, actor=actor)
    human = "\n".join(
        f"{r['zone']}/ — {r['documents']} documents — "
        + ("regenerated" if r["changed"] else "unchanged")
        for r in results
    )
    _emit(results, args.json, human)
    return 0


def cmd_check(args) -> int:
    root = _root_from(args)
    if root is None:
        return _fail("no bucket here and no path given")
    findings = checker.check(root)
    errors = [f for f in findings if f.level == "error"]
    warnings = [f for f in findings if f.level == "warning"]
    name = bucket.load(root).name or root.name
    if args.json:
        _emit(
            {
                "bucket": name,
                "ok": not errors,
                "errors": [asdict(f) for f in errors],
                "warnings": [asdict(f) for f in warnings],
            },
            True, "",
        )
    else:
        for f in findings:
            print(f"  {f.code} · {f.path} — {f.message}")
        verdict = (
            "clean, carry on." if not findings
            else "the notary objects." if errors
            else "drift, not damage."
        )
        plural_e = "" if len(errors) == 1 else "s"
        plural_w = "" if len(warnings) == 1 else "s"
        print(f"{name}: {len(errors)} error{plural_e} · "
              f"{len(warnings)} warning{plural_w} — {verdict}")
    return 1 if errors else 0


def cmd_status(args) -> int:
    root = _root_from(args)
    if root is None or not (root / "BUCKET.md").is_file():
        return _fail("not inside a bucket (no BUCKET.md found)")
    s = views.status(root, since=args.since)
    lines = [f"{s['bucket']} — {s['documents']} documents"]
    for label in ("auroras", "types", "activities"):
        if s[label]:
            pairs = " · ".join(f"{k} {v}" for k, v in s[label].items())
            lines.append(f"  {label}: {pairs}")
    if s["ledger"]:
        lines.append("  recent:")
        lines += [
            f"    {e['date']} {e['time']} · {e['actor']} · {e['verb']} · {e['obj']}"
            for e in s["ledger"][-5:]
        ]
    _emit(s, args.json, "\n".join(lines))
    return 0


def _render_items(items) -> list[str]:
    return [
        f"    · [{i['bucket']}] {i['title']} — {i['path']}"
        + (f" ({i['status']})" if i["status"] else "")
        for i in items
    ]


def cmd_today(args) -> int:
    t = views.today()
    lines = [f"Today across {len(t['buckets'])} bucket"
             f"{'s' if len(t['buckets']) != 1 else ''}"]
    for aurora, items in t["groups"].items():
        lines.append(f"  {aurora}:")
        lines += _render_items(items)
    if not t["groups"]:
        lines.append("  nothing demands you — the wide-open day.")
    _emit(t, args.json, "\n".join(lines))
    return 0


def cmd_agenda(args) -> int:
    a = views.agenda()
    lines = []
    if a["dated"]:
        lines.append("dated:")
        lines += [
            f"    {i['date']} · [{i['bucket']}] {i['title']} — {i['path']}"
            for i in a["dated"]
        ]
    if a["active"]:
        lines.append("active, undated:")
        lines += _render_items(a["active"])
    if not lines:
        lines = ["the horizon is clear."]
    _emit(a, args.json, "\n".join(lines))
    return 0


# ── parser ───────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fusion",
        description="Fusion — the notary. Records, checks, composes; never judges.",
    )
    parser.add_argument("--version", action="version",
                        version=f"fusion {__version__}")
    sub = parser.add_subparsers(dest="command")

    def flag_json(p):
        p.add_argument("--json", action="store_true",
                       help="machine output — agents parse, never scrape")

    def flag_as(p):
        p.add_argument("--as", dest="as_", metavar="ACTOR",
                       help="who holds the pen (default: FUSION_ACTOR, then "
                            "the OS username)")

    p = sub.add_parser("new", help="scaffold a bucket and register it")
    p.add_argument("path")
    p.add_argument("--name", help="bucket name (default: directory name)")
    p.add_argument("--kind", default="personal",
                   help="personal · company · studio · club · …")
    p.add_argument("--description")
    flag_as(p); flag_json(p)
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("hub", help="list, register, or retire buckets")
    hub_sub = p.add_subparsers(dest="hub_cmd")
    flag_json(p)
    pa = hub_sub.add_parser("add", help="register an existing bucket")
    pa.add_argument("path")
    flag_json(pa)
    pr = hub_sub.add_parser("remove", help="retire a bucket from the hub")
    pr.add_argument("name")
    flag_json(pr)
    p.set_defaults(func=cmd_hub, hub_cmd=None)
    pa.set_defaults(func=cmd_hub, hub_cmd="add")
    pr.set_defaults(func=cmd_hub, hub_cmd="remove")

    p = sub.add_parser("log", help="append to the ledger, or read it")
    p.add_argument("verb", nargs="?",
                   help=f"one of: {', '.join(ledger.VERBS)}")
    p.add_argument("object", nargs="?")
    p.add_argument("--note")
    p.add_argument("--at", metavar="'YYYY-MM-DD HH:MM'",
                   help="entry timestamp (default: now)")
    p.add_argument("--since", metavar="DATE|last-reflection",
                   help="read mode: entries since a date or the last reflection")
    p.add_argument("--bucket", help="bucket root (default: walk up from cwd)")
    flag_as(p); flag_json(p)
    p.set_defaults(func=cmd_log)

    p = sub.add_parser("index", help="regenerate INDEX.md in library/ and activities/")
    p.add_argument("path", nargs="?")
    flag_as(p); flag_json(p)
    p.set_defaults(func=cmd_index)

    p = sub.add_parser("check", help="audit a bucket against the convention")
    p.add_argument("path", nargs="?")
    flag_json(p)
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("status", help="one bucket at a glance")
    p.add_argument("path", nargs="?")
    p.add_argument("--since", metavar="DATE|last-reflection")
    flag_json(p)
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("today", help="the composed day, across the hub")
    flag_json(p)
    p.set_defaults(func=cmd_today)

    p = sub.add_parser("agenda", help="the wider horizon, across the hub")
    flag_json(p)
    p.set_defaults(func=cmd_agenda)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    return args.func(args)


def main_entry() -> None:  # console-script shim
    sys.exit(main())
