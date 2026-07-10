#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["openpyxl>=3.1.0"]
# ///
"""fusion-analyst export: stdin JSON {"headers": [...], "rows": [[...]]}
-> csv / json / xlsx on disk. Deterministic; the judgment (what to export)
happened before the pipe."""
import argparse
import csv
import json
import sys
from pathlib import Path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="fusion-analyst data export")
    ap.add_argument("--format", "-f", choices=("csv", "json", "xlsx"),
                    default="csv")
    ap.add_argument("--output", "-o", required=True)
    args = ap.parse_args(argv)

    payload = json.load(sys.stdin)
    headers = payload.get("headers") or []
    rows = payload.get("rows") or []

    if headers:
        bad = [i for i, r in enumerate(rows) if len(r) != len(headers)]
        if bad:
            print(f"export: row(s) {bad} have wrong length vs headers", file=sys.stderr)
            return 1

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    if args.format == "csv":
        with open(out, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            if headers:
                w.writerow(headers)
            w.writerows(rows)
    elif args.format == "json":
        records = ([dict(zip(headers, r)) for r in rows]
                   if headers else rows)
        out.write_text(json.dumps(records, indent=2, ensure_ascii=False),
                       encoding="utf-8", newline="\n")
    else:
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "export"
        if headers:
            ws.append(headers)
        for r in rows:
            ws.append(r)
        wb.save(out)

    print(json.dumps({"written": str(out), "rows": len(rows),
                      "format": args.format}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
