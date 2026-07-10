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

def _fail(message: str, as_json: bool = False) -> int:
    if as_json:
        print(json.dumps({"ok": False, "error": message}, ensure_ascii=False))
    else:
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
        return _fail(str(exc), args.json)
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
            return _fail(f"not a bucket (no readable BUCKET.md): {root}", args.json)
        missing = [f for f in ("name", "kind", "description")
                   if not str(b.frontmatter.get(f) or "").strip()]
        if missing:
            return _fail(f"BUCKET.md missing: {', '.join(missing)}", args.json)
        try:
            hub.add(hub.HubEntry(b.name, b.kind, hub.display_path(root),
                                  b.description))
        except ValueError as exc:
            return _fail(str(exc), args.json)
        _emit({"registered": b.name}, args.json,
              f"'{b.name}' registered in the hub.")
        return 0
    if args.hub_cmd == "remove":
        if not hub.remove(args.name):
            return _fail(f"no bucket named '{args.name}' in the hub", args.json)
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
        given = getattr(args, "bucket", None)
        return _fail(f"no bucket at: {given}" if given else
                     "not inside a bucket (no BUCKET.md found) — use --bucket",
                     args.json)
    if args.verb is None:
        entries = views.filter_since(ledger.read(root), args.since)
        human = "\n".join(
            f"{e.date} {ledger.format_line(e)[2:]}" for e in entries
        ) or "the ledger is empty — nothing has happened yet."
        _emit([asdict(e) for e in entries], args.json, human)
        return 0
    if args.object is None:
        return _fail("log needs an object: fusion log <verb> <object>", args.json)
    actor = ledger.resolve_actor(args.as_)
    try:
        entry = ledger.append(root, actor, args.verb, args.object,
                              note=args.note, at=_parse_at(args.at))
    except ValueError as exc:
        return _fail(str(exc), args.json)
    _emit(asdict(entry), args.json,
          f"logged: {entry.date} {ledger.format_line(entry)[2:]}")
    return 0


def cmd_index(args) -> int:
    root = _root_from(args)
    if root is None or not (root / "BUCKET.md").is_file():
        given = getattr(args, "path", None)
        return _fail(f"no bucket at: {given}" if given else
                     "not inside a bucket (no BUCKET.md found)", args.json)
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
        given = getattr(args, "path", None)
        return _fail(f"no bucket at: {given}" if given else
                     "not inside a bucket and no path given", args.json)
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
        given = getattr(args, "path", None)
        return _fail(f"no bucket at: {given}" if given else
                     "not inside a bucket (no BUCKET.md found)", args.json)
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


def cmd_setup(args) -> int:
    from fusion import setup as setup_mod
    import os as _os
    home = Path.home()
    skills_dir = Path(
        args.skills_dir
        or _os.environ.get("FUSION_SKILLS_DIR")
        or home / ".agents" / "skills").expanduser()
    no_agents = args.no_agents or _os.environ.get("FUSION_NO_AGENTS") == "1"
    try:
        report = setup_mod.run_setup(home, skills_dir, args.force,
                                     no_agents, args.remove)
    except setup_mod.SetupError as exc:
        return _fail(str(exc), args.json)
    lines = _render_setup(report)
    _emit(report, args.json, "\n".join(lines))
    return 0


def _render_setup(report: dict) -> list[str]:
    lines = []
    if "removed" in report:
        for r in report["removed"]:
            lines.append(f"  {r['action']:>10}  {r['skill']}  ({r['agent']})")
        lines.append("done. final step: " + report["next"][0])
        return lines
    lines.append(f"fusion-cli {report['cli']['version']}")
    lines.append(f"skills → {report['skills']['dir']}")
    for r in report["skills"]["results"]:
        lines.append(f"  {r['action']:>10}  {r['skill']}")
    for a in report["agents"]:
        lines.append(f"  {a['agent']}: {a['action']} — {a['detail']}")
    for adv in report["advice"]:
        lines.append(f"  advice: {adv['text']}")
    lines.append("next: " + " · ".join(report["next"]))
    return lines


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

    p = sub.add_parser("new", help="scaffold a bucket and register it", description="Scaffold a conformant bucket at PATH — six zones, BUCKET.md, an opened ledger — and register it in the hub.")
    p.add_argument("path", help="directory to create (missing or empty)")
    p.add_argument("--name", help="bucket name (default: directory name)")
    p.add_argument("--kind", default="personal",
                   help="personal · company · studio · club · …")
    p.add_argument("--description",
                   help="one line on what this bucket is for (lands in "
                        "BUCKET.md and the hub)")
    flag_as(p); flag_json(p)
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("hub", help="list, register, or retire buckets", description="The registry at ~/.fusion/hub.md (override: FUSION_HUB) — the agent's map of your buckets. No subcommand: list.")
    hub_sub = p.add_subparsers(dest="hub_cmd")
    flag_json(p)
    pa = hub_sub.add_parser("add", help="register an existing bucket", description="Register an existing bucket (reads its BUCKET.md).")
    pa.add_argument("path", help="bucket root to register")
    flag_json(pa)
    pr = hub_sub.add_parser("remove", help="retire a bucket from the hub", description="Retire a bucket from the hub. Files stay where they are.")
    pr.add_argument("name", help="registered bucket name")
    flag_json(pr)
    p.set_defaults(func=cmd_hub, hub_cmd=None)
    pa.set_defaults(func=cmd_hub, hub_cmd="add")
    pr.set_defaults(func=cmd_hub, hub_cmd="remove")

    p = sub.add_parser("log", help="append to the ledger, or read it", description="Append one signed entry to the append-only ledger — or, with no arguments, read it.", epilog="Read mode: 'fusion log' alone prints the ledger; --since DATE or --since last-reflection narrows it. The bucket resolves from --bucket, else by walking up from the current directory.")
    p.add_argument("verb", nargs="?",
                   help=f"one of: {', '.join(ledger.VERBS)}")
    p.add_argument("object", nargs="?", help="what was acted on — a path, or 'a → b' for a move")
    p.add_argument("--note")
    p.add_argument("--at", metavar="'YYYY-MM-DD HH:MM'",
                   help="entry timestamp (default: now)")
    p.add_argument("--since", metavar="DATE|last-reflection",
                   help="read mode: entries since a date or the last reflection")
    p.add_argument("--bucket", help="bucket root (default: walk up from cwd)")
    flag_as(p); flag_json(p)
    p.set_defaults(func=cmd_log)

    p = sub.add_parser("index", help="regenerate INDEX.md in library/ and activities/", description="Regenerate library/INDEX.md and activities/INDEX.md from the documents on disk. Deterministic: same tree, same bytes.")
    p.add_argument("path", nargs="?", help="bucket root (default: walk up from the current directory)")
    flag_as(p); flag_json(p)
    p.set_defaults(func=cmd_index)

    p = sub.add_parser("check", help="audit a bucket against the convention", description="Audit a bucket against the convention (SPEC §11). Exit 1 on errors; warnings never fail the check.")
    p.add_argument("path", nargs="?", help="bucket root (default: walk up from the current directory)")
    flag_json(p)
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("status", help="one bucket at a glance", description="One bucket at a glance: documents per zone, active work, the ledger's recent tail.")
    p.add_argument("path", nargs="?", help="bucket root (default: walk up from the current directory)")
    p.add_argument("--since", metavar="DATE|last-reflection")
    flag_json(p)
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("today", help="the composed day, across the hub", description="The composed morning across every hub bucket: commitments and active work, grouped by aurora.")
    flag_json(p)
    p.set_defaults(func=cmd_today)

    p = sub.add_parser("agenda", help="the wider horizon, across the hub", description="The wider horizon across the hub: dated items first (due:/date:), then active work.")
    flag_json(p)
    p.set_defaults(func=cmd_agenda)

    p = sub.add_parser("setup", help="install skills into agents; --remove undoes it",
                       description="Install the bundled skills to the canonical "
                       "skills directory and link them into every detected agent. "
                       "Idempotent; never destroys what it did not create.")
    p.add_argument("--force", action="store_true",
                   help="replace foreign entries setup would otherwise leave")
    p.add_argument("--remove", action="store_true",
                   help="undo setup (attribution-checked), print the uninstall closer")
    p.add_argument("--skills-dir", help="canonical destination (default ~/.agents/skills; env FUSION_SKILLS_DIR)")
    p.add_argument("--no-agents", action="store_true",
                   help="skip agent fan-out (env FUSION_NO_AGENTS=1)")
    flag_json(p)
    p.set_defaults(func=cmd_setup)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    try:
        return args.func(args)
    except SystemExit:
        raise
    except Exception as exc:  # the notary reports surprises, never crashes bare
        return _fail(f"unexpected: {type(exc).__name__}: {exc}",
                    getattr(args, "json", False))


def main_entry() -> None:  # console-script shim
    sys.exit(main())
