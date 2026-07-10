#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "openpyxl>=3.1.0",
#   "PyYAML>=6.0",
#   "pymupdf>=1.24.0",
# ]
# ///
"""fusion-intake Stage-1 engine: admit / prepare / link / cleanup.

Deterministic, no LLM. `admit` is the ONLY writer of sources/MANIFEST.md in
the whole Fusion reference implementation. `prepare` routes by format:
extractive files (xlsx/csv) become conformant documents directly; everything
else gets a work dir under workbench/.intake/ with page text + images +
manifest.json for the Stage-2 agent (references/convert.md). The page-
coverage invariant — every page recorded, low-text pages flagged
needs_vision — makes silent-empty output structurally impossible.
"""
import argparse
import csv as csv_mod
import hashlib
import json
import re
import shutil
import subprocess
import sys
import uuid
from datetime import datetime
from email import policy
from email.parser import BytesParser
from html.parser import HTMLParser
from pathlib import Path

import yaml

AURORAS = ("commitments", "focus", "ops", "collab", "life", "explore",
           "archive", "library")

EXTRACTIVE_EXTS = {".xlsx", ".csv"}
LIBREOFFICE_EXTS = {".docx", ".pptx", ".doc", ".odt", ".rtf", ".key",
                    ".pages", ".ppt", ".xls", ".html", ".htm"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
MAIL_EXTS = {".eml"}
TEXT_EXTS = {".md", ".txt"}
SUPPORTED_EXTS = (EXTRACTIVE_EXTS | LIBREOFFICE_EXTS | IMAGE_EXTS
                  | MAIL_EXTS | TEXT_EXTS | {".pdf"})

TEXT_COVERAGE_MIN_CHARS = 100   # below this a page is scanned/figure
RENDER_DPI = 150
EXCEL_ERRORS = {"#REF!", "#N/A", "#VALUE!", "#DIV/0!", "#NAME?", "#NULL!",
                "#NUM!"}

TODAY = datetime.now().strftime("%Y-%m-%d")


class IntakeError(Exception):
    """Strict-writer refusal — named loudly, never silently skipped."""


# ── shared helpers ───────────────────────────────────────────────────────

def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def slugify(name: str) -> str:
    """SPEC §4 filename: lowercase, hyphen-separated, stem <=60 chars."""
    stem = re.sub(r"\.(xlsx|docx|pptx|csv|pdf|eml|md|txt|png|jpe?g|webp|gif|html?)$",
                  "", name, flags=re.IGNORECASE)
    stem = stem.lower()
    stem = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")
    stem = re.sub(r"-+", "-", stem)
    return stem[:60].rstrip("-") or "document"


def cell_to_string(cell) -> str:
    if isinstance(cell, str) and cell.strip() in EXCEL_ERRORS:
        return ""
    if cell is None:
        return ""
    if isinstance(cell, bool):
        return str(cell)
    if isinstance(cell, float):
        if cell.is_integer():
            return str(int(cell))
        return repr(cell)   # shortest round-trippable form — verbatim, never rounded
    if isinstance(cell, int):
        return str(cell)
    if isinstance(cell, datetime):
        return cell.strftime("%Y-%m-%d")
    text = str(cell).replace("|", "\\|").replace("\n", "<br>")
    return text.strip()


def _row_empty(row) -> bool:
    return all(cell_to_string(c) == "" for c in row)


def prune_empty_columns(rows):
    if not rows:
        return rows
    width = max(len(r) for r in rows)
    padded = [list(r) + [None] * (width - len(r)) for r in rows]
    keep = [i for i in range(width)
            if any(cell_to_string(r[i]) != "" for r in padded)]
    return [[r[i] for i in keep] for r in padded] if keep else []


def rows_to_table(rows) -> str:
    """One markdown table. Every row, every column — no caps, no sampling."""
    rows = [r for r in rows if not _row_empty(r)]
    rows = prune_empty_columns(rows)
    if not rows or not rows[0]:
        return "*No data*"
    string_rows = [[cell_to_string(c) for c in r] for r in rows]
    lines = ["| " + " | ".join(string_rows[0]) + " |",
             "| " + " | ".join(["---"] * len(rows[0])) + " |"]
    lines += ["| " + " | ".join(r) + " |" for r in string_rows[1:]]
    return "\n".join(lines)


def render_document(fm: dict, summary: str, body: str) -> str:
    front = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True,
                           width=2**31 - 1)
    return f"---\n{front}---\n\n## Summary\n\n{summary}\n\n---\n\n{body}\n"


# ── MANIFEST (single writer lives here) ──────────────────────────────────

def _manifest_path(root: Path) -> Path:
    return root / "sources" / "MANIFEST.md"


def manifest_append(root: Path, rel: str, actor: str, sha: str) -> None:
    path = _manifest_path(root)
    if not path.is_file():
        path.write_text("# Manifest\n\n| file | added | by | sha256 | library |\n"
                        "|---|---|---|---|---|\n", encoding="utf-8")
    text = path.read_text(encoding="utf-8")
    if not text.endswith("\n"):
        text += "\n"
    text += f"| {rel} | {TODAY} | {actor} | {sha} | — |\n"
    path.write_text(text, encoding="utf-8")


def manifest_link(root: Path, rel: str, doc: str) -> None:
    path = _manifest_path(root)
    if not path.is_file():
        raise IntakeError(f"no manifest at {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    hit = False
    for i, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 5 and cells[0] == rel:
            cells[4] = doc if cells[4] in ("—", "") else f"{cells[4]}, {doc}"
            lines[i] = "| " + " | ".join(cells) + " |"
            hit = True
            break
    if not hit:
        raise IntakeError(f"source not in manifest: {rel}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ── admit ────────────────────────────────────────────────────────────────

def admit(root: Path, inbox_rel: str, category: str, actor: str) -> dict:
    root = Path(root)
    src = root / "inbox" / inbox_rel
    if not src.is_file():
        raise IntakeError(f"not in inbox/: {inbox_rel}")
    if src.suffix.lower() not in SUPPORTED_EXTS:
        raise IntakeError(
            f"unsupported format: {src.suffix.lower()} — the gate refuses "
            "what it cannot preserve; the file stays in inbox/")
    if not actor or any(c.isspace() for c in actor):
        raise IntakeError(f"actor must be a single token: {actor!r}")
    category = category.strip().strip("/")
    if not category:
        raise IntakeError("category required")
    if any(c in src.name for c in "|\n\r") or any(c in category for c in "|\n\r"):
        raise IntakeError(
            f"'|' and newlines break the manifest grammar: {src.name!r} — "
            "rename the incoming file before admitting it")
    dest = root / "sources" / category / src.name
    if dest.exists():
        raise IntakeError(
            f"sources/ is immutable and {category}/{src.name} already "
            "exists — rename the incoming file before admitting it")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dest))
    sha = sha256_of(dest)
    rel = f"{category}/{src.name}"
    manifest_append(root, rel, actor, sha)
    return {"source": rel, "sha256": sha, "manifest_row": True}


# ── prepare: routing + engines ───────────────────────────────────────────

def probe_pdf_text_layer(pdf_path: Path):
    import fitz
    records = []
    doc = fitz.open(str(pdf_path))
    try:
        for i, page in enumerate(doc, 1):
            text = page.get_text().strip()
            records.append({"page": i, "text": text, "text_chars": len(text),
                            "needs_vision": len(text) < TEXT_COVERAGE_MIN_CHARS})
    finally:
        doc.close()
    return records


def render_pdf_pages(pdf_path: Path, out_dir: Path, pages=None):
    import fitz
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    doc = fitz.open(str(pdf_path))
    try:
        targets = (list(range(1, doc.page_count + 1))
                   if pages is None else sorted(pages))
        for n in targets:
            if 1 <= n <= doc.page_count:
                pix = doc.load_page(n - 1).get_pixmap(dpi=RENDER_DPI)
                img = out_dir / f"page-{n:03d}.png"
                pix.save(str(img))
                written.append(img)
    finally:
        doc.close()
    return written


def require_soffice() -> str:
    exe = shutil.which("soffice") or shutil.which("libreoffice")
    if not exe:
        raise IntakeError(
            "LibreOffice not found: 'soffice' must be on PATH for "
            "docx/pptx/legacy office formats (declared in SKILL.md "
            "compatibility). Install it or add it to PATH. No fallback.")
    return exe


def soffice_to_pdf(src: Path, out_dir: Path) -> Path:
    exe = require_soffice()
    out_dir.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [exe, "--headless", "--convert-to", "pdf", "--outdir",
         str(out_dir), str(src)],
        capture_output=True, text=True, timeout=300)
    pdf = out_dir / (src.stem + ".pdf")
    if proc.returncode != 0 or not pdf.exists():
        raise IntakeError(
            f"soffice failed on {src.name} (rc={proc.returncode}): "
            f"{proc.stderr.strip()[:400]}")
    return pdf


class _HTMLText(HTMLParser):
    """Text of an HTML mail body: entities decoded (convert_charrefs),
    script/style dropped whole, block tags become line breaks."""
    _SKIP = {"script", "style"}
    _BREAK = {"p", "br", "div", "tr", "li", "table",
              "h1", "h2", "h3", "h4", "h5", "h6"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._chunks: list = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP:
            self._skip_depth += 1
        elif tag in self._BREAK:
            self._chunks.append("\n")

    def handle_endtag(self, tag):
        if tag in self._SKIP and self._skip_depth:
            self._skip_depth -= 1
        elif tag in self._BREAK:
            self._chunks.append("\n")

    def handle_data(self, data):
        if not self._skip_depth:
            self._chunks.append(data)


def html_to_text(html: str) -> str:
    parser = _HTMLText()
    parser.feed(html)
    parser.close()
    lines = [re.sub(r"[ \t]+", " ", ln).strip()
             for ln in "".join(parser._chunks).splitlines()]
    return "\n".join(ln for ln in lines if ln)


def eml_to_text(path: Path, work_dir: Path):
    msg = BytesParser(policy=policy.default).parse(open(path, "rb"))
    lines = [f"{h}: {msg[h]}" for h in ("From", "To", "Date", "Subject")
             if msg[h]]
    body = msg.get_body(preferencelist=("plain", "html"))
    content = body.get_content() if body else ""
    if body and body.get_content_subtype() == "html":
        content = html_to_text(content)
    attachments = []
    seen_lower = set()
    for part in msg.iter_attachments():
        name = Path(part.get_filename() or "attachment.bin").name
        if name in {"", ".", ".."}:
            name = "attachment.bin"
        stem, dot, ext = name.partition(".")
        n = 2
        while name.lower() in seen_lower:
            name = f"{stem}-{n}{dot}{ext}"
            n += 1
        (work_dir / name).write_bytes(part.get_payload(decode=True) or b"")
        attachments.append(name)
        seen_lower.add(name.lower())
    return "\n".join(lines) + "\n\n" + content, attachments


def _route(ext: str) -> str:
    ext = ext.lower()
    if ext in EXTRACTIVE_EXTS:
        return "extractive"
    if ext in LIBREOFFICE_EXTS:
        return "libreoffice"
    if ext == ".pdf":
        return "pdf"
    if ext in IMAGE_EXTS:
        return "image"
    if ext in MAIL_EXTS:
        return "mail"
    if ext in TEXT_EXTS:
        return "text"
    raise IntakeError(f"unsupported format: {ext} — the gate refuses "
                      "what it cannot preserve")


def _sheet_matrix(ws):
    """All cell values with merged ranges unfolded — every cell a merge
    spans carries the anchor's value, so pruning never eats merged data."""
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    for rng in ws.merged_cells.ranges:
        if rng.min_row - 1 >= len(rows):
            continue
        anchor_row = rows[rng.min_row - 1]
        anchor = (anchor_row[rng.min_col - 1]
                  if rng.min_col - 1 < len(anchor_row) else None)
        for r in range(rng.min_row, min(rng.max_row, len(rows)) + 1):
            row = rows[r - 1]
            for c in range(rng.min_col, min(rng.max_col, len(row)) + 1):
                row[c - 1] = anchor
    return rows


def _xlsx_body(path: Path):
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True)
    sections, sheets, rows_total = [], 0, 0
    for name in wb.sheetnames:
        rows = _sheet_matrix(wb[name])
        live = [r for r in rows if not _row_empty(r)]
        if live:
            sheets += 1
            rows_total += max(len(live) - 1, 0)
            sections.append(f"## {name}\n\n{rows_to_table(rows)}")
    return "\n\n".join(sections) or "*No data*", sheets, rows_total


def _csv_body(path: Path):
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv_mod.reader(fh))
    return rows_to_table(rows), 1, max(len(rows) - 1, 0)


def _work_dir(root: Path) -> Path:
    d = root / "workbench" / ".intake" / uuid.uuid4().hex[:12]
    d.mkdir(parents=True, exist_ok=True)
    return d


def _read_frontmatter(path: Path) -> dict:
    """Tolerant frontmatter reader: {} if the leading --- block is absent
    or unparsable — reconcile must never choke on a hand-edited document."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        return {}
    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return {}
    return fm if isinstance(fm, dict) else {}


def _merge_reconcile_fm(existing_fm: dict, seed: dict) -> dict:
    """The librarian curated the existing document — its values win.
    Existing keys come first (unknown keys preserved verbatim, including
    the original `created:`); title/type/aurora are filled from the seed
    only where the existing doc lacks them; `source:` always repoints to
    the new original; `updated:` is always bumped to today."""
    merged = dict(existing_fm)
    for key in ("title", "type", "aurora"):
        if not merged.get(key):
            merged[key] = seed[key]
    if "created" not in merged:
        merged["created"] = seed["created"]
    merged["source"] = seed["source"]
    merged["updated"] = TODAY
    return merged


def prepare(root: Path, source_rel: str, dest: str | None = None,
            slug: str | None = None, doc_type: str | None = None,
            aurora: str = "library", reconcile: bool = False) -> dict:
    root = Path(root)
    src = root / "sources" / source_rel
    if not src.is_file():
        raise IntakeError(f"not in sources/: {source_rel}")
    if aurora not in AURORAS:
        raise IntakeError(f"aurora must be one of the eight, got: {aurora!r}")
    category = Path(source_rel).parts[0] if "/" in source_rel else "reference"
    doc_type = doc_type or category.rstrip("s")
    dest = (dest or f"library/{category}").strip("/")
    slug = slug or slugify(src.name)
    out_rel = f"{dest}/{slug}.md"
    seed = {"title": src.stem, "type": doc_type, "aurora": aurora,
            "source": f"sources/{source_rel}", "created": TODAY}
    path = _route(src.suffix)

    if path == "extractive":
        if src.suffix.lower() == ".xlsx":
            body, sheets, nrows = _xlsx_body(src)
        else:
            body, sheets, nrows = _csv_body(src)
        summary = (f"Tabular data converted from {src.name}: "
                   f"{sheets} sheet(s), {nrows} data row(s).")
        out = root / out_rel
        if out.exists() and not reconcile:
            raise IntakeError(
                f"document exists: {out_rel} — pass --reconcile for a "
                "confirmed update, or choose --slug")
        if reconcile and out.exists():
            seed = _merge_reconcile_fm(_read_frontmatter(out), seed)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_document(seed, summary, body), encoding="utf-8")
        return {"path": "extractive", "done": True, "source": source_rel,
                "output_file": out_rel, "front_matter_seed": seed,
                "reconcile": reconcile}

    # vision / structured paths get a work dir + manifest for Stage 2
    out = root / out_rel
    if out.exists() and not reconcile:
        raise IntakeError(
            f"document exists: {out_rel} — pass --reconcile for a "
            "confirmed update, or choose --slug")
    if reconcile and out.exists():
        seed = _merge_reconcile_fm(_read_frontmatter(out), seed)

    work = _work_dir(root)
    record = {"path": path, "done": False, "source": source_rel,
              "run_dir": str(work.relative_to(root)),
              "output_file": out_rel, "front_matter_seed": seed,
              "reconcile": reconcile,
              "pages": [], "images": [], "attachments": [],
              "intermediate_pdf": None}

    if path == "libreoffice":
        pdf = soffice_to_pdf(src, work)
        record["intermediate_pdf"] = str(pdf.relative_to(root))
        record["pages"] = probe_pdf_text_layer(pdf)
        imgs = render_pdf_pages(pdf, work)                    # ALL pages
        record["images"] = [str(p.relative_to(root)) for p in imgs]
    elif path == "pdf":
        probe = probe_pdf_text_layer(src)
        record["pages"] = probe
        if all(p["needs_vision"] for p in probe):
            record["path"] = "pdf_scanned"
            imgs = render_pdf_pages(src, work)                # ALL pages
        else:
            record["path"] = "pdf_text"
            imgs = render_pdf_pages(
                src, work, pages=[p["page"] for p in probe if p["needs_vision"]])
        record["images"] = [str(p.relative_to(root)) for p in imgs]
    elif path == "image":
        copy = work / src.name
        shutil.copy2(src, copy)
        record["pages"] = [{"page": 1, "text": "", "text_chars": 0,
                            "needs_vision": True}]
        record["images"] = [str(copy.relative_to(root))]
    elif path == "mail":
        text, attachments = eml_to_text(src, work)
        record["pages"] = [{"page": 1, "text": text,
                            "text_chars": len(text), "needs_vision": False}]
        record["attachments"] = attachments
    else:  # text passthrough
        text = src.read_text(encoding="utf-8", errors="replace")
        record["pages"] = [{"page": 1, "text": text,
                            "text_chars": len(text), "needs_vision": False}]

    record["page_count"] = len(record["pages"])
    manifest = work / "manifest.json"
    manifest.write_text(json.dumps(record, indent=2), encoding="utf-8")
    record["manifest"] = str(manifest.relative_to(root))
    return record


def link(root: Path, source_rel: str, doc_rel: str) -> dict:
    manifest_link(Path(root), source_rel, doc_rel)
    return {"source": source_rel, "library": doc_rel}


def cleanup(run_dir: Path) -> None:
    run_dir = Path(run_dir).resolve()
    parts = run_dir.parts
    if ".intake" not in parts or "workbench" not in parts:
        raise IntakeError(f"refusing to delete outside workbench/.intake: {run_dir}")
    if run_dir.exists():
        shutil.rmtree(run_dir)


# ── CLI ──────────────────────────────────────────────────────────────────

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="fusion-intake Stage-1 engine")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("admit", help="inbox -> sources + MANIFEST row")
    p.add_argument("--bucket", required=True)
    p.add_argument("--file", required=True, help="path relative to inbox/")
    p.add_argument("--category", required=True)
    p.add_argument("--actor", required=True)

    p = sub.add_parser("prepare", help="route + convert / stage for vision")
    p.add_argument("--bucket", required=True)
    p.add_argument("--source", required=True, help="path relative to sources/")
    p.add_argument("--dest", help="zone-relative output dir "
                   "(default library/<category>)")
    p.add_argument("--slug")
    p.add_argument("--type", dest="doc_type")
    p.add_argument("--aurora", default="library")
    p.add_argument("--reconcile", action="store_true",
                   help="confirmed update: reconcile the existing document "
                   "in place instead of refusing the slug collision")

    p = sub.add_parser("link", help="set the MANIFEST library column")
    p.add_argument("--bucket", required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--doc", required=True)

    p = sub.add_parser("cleanup", help="delete one work dir")
    p.add_argument("--run-dir", required=True)

    args = ap.parse_args(argv)
    try:
        if args.cmd == "admit":
            out = admit(Path(args.bucket), args.file, args.category, args.actor)
        elif args.cmd == "prepare":
            out = prepare(Path(args.bucket), args.source, dest=args.dest,
                          slug=args.slug, doc_type=args.doc_type,
                          aurora=args.aurora, reconcile=args.reconcile)
        elif args.cmd == "link":
            out = link(Path(args.bucket), args.source, args.doc)
        else:
            cleanup(Path(args.run_dir))
            out = {"cleaned": args.run_dir}
    except IntakeError as exc:
        print(f"intake: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
