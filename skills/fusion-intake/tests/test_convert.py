"""Stage-1 engine: admit -> MANIFEST, extractive conversion, vision prep,
link, cleanup. The lossless contract, tested."""
import shutil
import zipfile

import pytest
import yaml
from conftest import bucket, seed_source  # noqa: F401 (fixture)

import convert
import make_fixtures as fx


def admit(root, name, category="records", actor="claude"):
    return convert.admit(root, name, category=category, actor=actor)


def put_inbox(root, name, maker):
    p = root / "inbox" / name
    maker(p)
    return p


# ── admit ────────────────────────────────────────────────────────────────

def test_admit_moves_and_registers(bucket):
    put_inbox(bucket, "scores.xlsx", fx.make_xlsx)
    rec = admit(bucket, "scores.xlsx")
    assert rec["source"] == "records/scores.xlsx"
    assert len(rec["sha256"]) == 64
    assert not (bucket / "inbox" / "scores.xlsx").exists()
    assert (bucket / "sources" / "records" / "scores.xlsx").is_file()
    manifest = (bucket / "sources" / "MANIFEST.md").read_text(encoding="utf-8")
    row = manifest.strip().splitlines()[-1]
    cells = [c.strip() for c in row.strip("|").split("|")]
    assert cells[0] == "records/scores.xlsx"
    assert cells[2] == "claude"
    assert cells[3] == rec["sha256"]
    assert cells[4] == "—"


def test_admit_refuses_source_collision(bucket):
    put_inbox(bucket, "scores.xlsx", fx.make_xlsx)
    admit(bucket, "scores.xlsx")
    put_inbox(bucket, "scores.xlsx", fx.make_xlsx)
    with pytest.raises(convert.IntakeError, match="immutable"):
        admit(bucket, "scores.xlsx")


def test_admit_missing_file(bucket):
    with pytest.raises(convert.IntakeError, match="inbox"):
        admit(bucket, "ghost.xlsx")


def test_admit_refuses_unsupported_format(bucket):
    (bucket / "inbox" / "mystery.xyz").write_text("???", encoding="utf-8")
    with pytest.raises(convert.IntakeError, match="unsupported"):
        admit(bucket, "mystery.xyz")
    # nothing moved, nothing registered — the file stays in inbox
    assert (bucket / "inbox" / "mystery.xyz").is_file()
    manifest = (bucket / "sources" / "MANIFEST.md").read_text(encoding="utf-8")
    assert "mystery.xyz" not in manifest


def test_admit_refuses_manifest_breaking_chars(bucket):
    manifest_before = (bucket / "sources" / "MANIFEST.md").read_text(encoding="utf-8")
    put_inbox(bucket, "weird | name.csv", fx.make_csv)
    with pytest.raises(convert.IntakeError, match="manifest grammar"):
        admit(bucket, "weird | name.csv")
    # nothing moved, nothing registered — the file stays in inbox
    assert (bucket / "inbox" / "weird | name.csv").is_file()
    manifest_after = (bucket / "sources" / "MANIFEST.md").read_text(encoding="utf-8")
    assert manifest_after == manifest_before


def test_admit_refuses_traversal_inbox_path(bucket, tmp_path):
    # leak.csv sits OUTSIDE the bucket entirely — inbox/../../leak.csv from
    # bucket/inbox/ climbs out of "scratch" into tmp_path itself, mirroring
    # test_unpack_refuses_traversal_crafted_file_argument's fixture layout.
    leak = tmp_path / "leak.csv"
    leak.write_text("sensitive,data\n1,2\n", encoding="utf-8")
    manifest_before = (bucket / "sources" / "MANIFEST.md").read_text(encoding="utf-8")
    with pytest.raises(convert.IntakeError, match="escapes"):
        admit(bucket, "../../leak.csv")
    # shutil.move would have deleted the original — it must still be there,
    # byte-for-byte untouched, and nothing registered
    assert leak.is_file()
    assert leak.read_text(encoding="utf-8") == "sensitive,data\n1,2\n"
    manifest_after = (bucket / "sources" / "MANIFEST.md").read_text(encoding="utf-8")
    assert manifest_after == manifest_before


# ── extractive paths ─────────────────────────────────────────────────────

def test_xlsx_extractive_is_born_conformant(bucket):
    put_inbox(bucket, "Q1 Scores.xlsx", fx.make_xlsx)
    rec = admit(bucket, "Q1 Scores.xlsx")
    out = convert.prepare(bucket, rec["source"])
    assert out["done"] is True
    doc = (bucket / out["output_file"]).read_text(encoding="utf-8")
    # frontmatter
    assert doc.startswith("---\n")
    assert "title:" in doc and "type:" in doc and "aurora: library" in doc
    assert "source: sources/records/Q1 Scores.xlsx" in doc
    # summary-first
    body = doc.split("---\n", 2)[2]
    assert body.lstrip().startswith("## Summary")
    assert "\n---\n" in body
    # lossless table facts: exact numbers, pipe escaped, empty col pruned
    assert "78.5" in doc and "| 91 |" in doc
    assert "steady \\| improving" in doc
    assert "| supplier | score | notes |" in doc   # all-empty column pruned
    assert "## Scores" in doc and "## Meta" in doc
    # slug filename
    assert out["output_file"].endswith("library/records/q1-scores.md")


def test_csv_extractive_bom_and_numbers(bucket):
    put_inbox(bucket, "inventory.csv", fx.make_csv)
    rec = admit(bucket, "inventory.csv")
    out = convert.prepare(bucket, rec["source"])
    doc = (bucket / out["output_file"]).read_text(encoding="utf-8")
    assert "12500.50" in doc          # verbatim, never rounded
    assert "﻿" not in doc      # BOM consumed
    assert "Jazzmaster 1962" in doc


def test_invalid_aurora_refused(bucket):
    put_inbox(bucket, "inventory.csv", fx.make_csv)
    rec = admit(bucket, "inventory.csv")
    with pytest.raises(convert.IntakeError, match="aurora"):
        convert.prepare(bucket, rec["source"], aurora="vibes")


def test_prepare_refuses_slug_collision(bucket):
    put_inbox(bucket, "inventory.csv", fx.make_csv)
    rec = admit(bucket, "inventory.csv")
    convert.prepare(bucket, rec["source"])
    put_inbox(bucket, "inventory-2.csv", fx.make_csv)
    rec2 = admit(bucket, "inventory-2.csv")
    with pytest.raises(convert.IntakeError, match="exists"):
        convert.prepare(bucket, rec2["source"], slug="inventory")


def test_prepare_reconcile_merges_frontmatter(bucket):
    # a librarian-curated document already sits in the library: an old
    # created: date and an unknown key that must survive untouched
    existing = bucket / "library" / "records" / "inventory.md"
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing_fm = {"title": "Inventory (curated)", "type": "record",
                   "aurora": "library",
                   "source": "sources/records/inventory-old.csv",
                   "created": "2020-01-01", "flavor": "umami"}
    existing.write_text(convert.render_document(
        existing_fm, "Old summary.", "Old body."), encoding="utf-8")

    put_inbox(bucket, "inventory-v2.csv", fx.make_csv)
    rec = admit(bucket, "inventory-v2.csv")
    out = convert.prepare(bucket, rec["source"], slug="inventory",
                          reconcile=True)
    assert out["reconcile"] is True
    doc = existing.read_text(encoding="utf-8")
    fm = yaml.safe_load(doc.split("---\n", 2)[1])
    assert fm["created"] == "2020-01-01"          # original preserved
    assert fm["flavor"] == "umami"                # unknown key preserved
    assert fm["updated"] == convert.TODAY         # bumped
    assert fm["title"] == "Inventory (curated)"   # existing value wins
    assert fm["source"] == "sources/records/inventory-v2.csv"  # repointed
    assert "12500.50" in doc                      # new content written


def test_dest_and_type_overrides(bucket):
    put_inbox(bucket, "inventory.csv", fx.make_csv)
    rec = admit(bucket, "inventory.csv", category="gear")
    out = convert.prepare(bucket, rec["source"], dest="library/instruments",
                          doc_type="inventory", slug="pedal-inventory")
    assert out["output_file"] == "library/instruments/pedal-inventory.md"
    doc = (bucket / out["output_file"]).read_text(encoding="utf-8")
    assert "type: inventory" in doc


# ── vision prep paths ────────────────────────────────────────────────────

def test_text_pdf_spotcheck(bucket):
    put_inbox(bucket, "audit.pdf", fx.make_text_pdf)
    rec = admit(bucket, "audit.pdf")
    out = convert.prepare(bucket, rec["source"])
    assert out["done"] is False and out["path"] == "pdf_text"
    assert out["page_count"] == 2 == len(out["pages"])
    assert all(not p["needs_vision"] for p in out["pages"])
    assert out["images"] == []        # nothing to spot-check
    assert out["front_matter_seed"]["aurora"] == "library"
    assert out["front_matter_seed"]["source"] == "sources/records/audit.pdf"
    assert (bucket / out["manifest"]).is_file()


def test_scanned_pdf_all_pages_rendered(bucket):
    put_inbox(bucket, "scan.pdf", fx.make_scanned_pdf)
    rec = admit(bucket, "scan.pdf")
    out = convert.prepare(bucket, rec["source"])
    assert out["path"] == "pdf_scanned"
    assert out["pages"][0]["needs_vision"] is True
    assert len(out["images"]) == out["page_count"] == 1


def test_image_path(bucket):
    put_inbox(bucket, "photo.png", fx.make_png)
    rec = admit(bucket, "photo.png")
    assert "converted" not in rec and "note" not in rec   # tiff-only fields
    out = convert.prepare(bucket, rec["source"])
    assert out["path"] == "image"
    assert out["pages"] == [{"page": 1, "text": "", "text_chars": 0,
                             "needs_vision": True}]
    assert len(out["images"]) == 1


# ── tiff -> png at admit (2026-07-12 ruling: no large tiffs) ─────────────

def test_tiff_admits_as_png_with_note(bucket):
    put_inbox(bucket, "scan.tiff", fx.make_tiff)
    rec = admit(bucket, "scan.tiff")

    # the PNG is the admitted original — not the tiff
    assert rec["source"] == "records/scan.png"
    assert not (bucket / "inbox" / "scan.tiff").exists()
    assert not (bucket / "sources" / "records" / "scan.tiff").exists()
    png_path = bucket / "sources" / "records" / "scan.png"
    assert png_path.is_file()
    assert png_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"   # real PNG bytes
    assert rec["sha256"] == convert.sha256_of(png_path)

    # MANIFEST row names the PNG, keyed to the PNG's own sha256
    manifest = (bucket / "sources" / "MANIFEST.md").read_text(encoding="utf-8")
    row = manifest.strip().splitlines()[-1]
    cells = [c.strip() for c in row.strip("|").split("|")]
    assert cells[0] == "records/scan.png"
    assert cells[3] == rec["sha256"]

    # the source tiff's identity is carried honestly, for the ledger
    assert rec["converted"]["from_format"] == "tiff"
    assert rec["converted"]["to_format"] == "png"
    assert rec["converted"]["original_name"] == "scan.tiff"
    assert len(rec["converted"]["original_sha256"]) == 64
    assert rec["converted"]["original_sha256"] != rec["sha256"]
    assert "scan.tiff" in rec["note"] and rec["converted"]["original_sha256"] in rec["note"]
    assert "scan.png" in rec["note"] and rec["sha256"] in rec["note"]


def test_tiff_png_flows_through_the_image_route(bucket):
    put_inbox(bucket, "scan.tiff", fx.make_tiff)
    rec = admit(bucket, "scan.tiff")
    out = convert.prepare(bucket, rec["source"])
    # admitted as a PNG, so Stage 2 sees it exactly like any other image —
    # no tiff-specific branch downstream of admit
    assert out["path"] == "image"
    assert out["pages"] == [{"page": 1, "text": "", "text_chars": 0,
                             "needs_vision": True}]
    assert len(out["images"]) == 1
    assert out["images"][0].endswith(".png")


def test_multiframe_tiff_refused(bucket):
    put_inbox(bucket, "stack.tiff", lambda p: fx.make_tiff(p, frames=3))
    with pytest.raises(convert.IntakeError, match="multi-frame"):
        admit(bucket, "stack.tiff")
    # conservative refusal: nothing moved, nothing registered, nothing
    # half-written into sources/
    assert (bucket / "inbox" / "stack.tiff").is_file()
    assert not (bucket / "sources" / "records").exists()
    manifest = (bucket / "sources" / "MANIFEST.md").read_text(encoding="utf-8")
    assert "stack" not in manifest


def test_tiff_uppercase_extension_also_converts(bucket):
    # case-insensitive suffix match, same as every other extension check
    src = put_inbox(bucket, "SCAN.TIFF", fx.make_tiff)
    rec = admit(bucket, "SCAN.TIFF")
    assert rec["source"] == "records/SCAN.png"
    assert not src.exists()


def test_eml_path_extracts_text_and_attachments(bucket):
    put_inbox(bucket, "mail.eml", fx.make_eml)
    rec = admit(bucket, "mail.eml")
    out = convert.prepare(bucket, rec["source"])
    assert out["path"] == "mail"
    text = out["pages"][0]["text"]
    assert "Subject: Re: rehearsal schedule" in text
    assert "Bring the Jazzmaster" in text
    assert out["attachments"] == ["setlist.csv"]
    assert (bucket / out["run_dir"] / "setlist.csv").is_file()


def test_markdown_passthrough(bucket):
    (bucket / "inbox" / "note.md").write_text(
        "# A note\n\nJust words.\n", encoding="utf-8")
    rec = admit(bucket, "note.md")
    out = convert.prepare(bucket, rec["source"])
    assert out["path"] == "text"
    assert out["pages"][0]["text"] == "# A note\n\nJust words.\n"
    assert out["pages"][0]["needs_vision"] is False


@pytest.mark.skipif(shutil.which("soffice") is None,
                    reason="LibreOffice not on PATH")
def test_docx_libreoffice_path(bucket):
    put_inbox(bucket, "procedure.docx", fx.make_docx)
    rec = admit(bucket, "procedure.docx")
    out = convert.prepare(bucket, rec["source"])
    assert out["path"] == "libreoffice"
    assert out["intermediate_pdf"].endswith(".pdf")
    assert out["page_count"] == len(out["pages"]) >= 1
    assert len(out["images"]) == out["page_count"]   # ALL pages rendered
    joined = " ".join(p["text"] for p in out["pages"])
    assert "Onboarding procedure" in joined


def test_docx_fails_fast_without_soffice(bucket, monkeypatch):
    put_inbox(bucket, "procedure.docx", fx.make_docx)
    rec = admit(bucket, "procedure.docx")
    monkeypatch.setattr(shutil, "which", lambda _: None)
    with pytest.raises(convert.IntakeError, match="LibreOffice"):
        convert.prepare(bucket, rec["source"])


# ── link + cleanup ───────────────────────────────────────────────────────

def test_link_sets_library_column(bucket):
    put_inbox(bucket, "inventory.csv", fx.make_csv)
    rec = admit(bucket, "inventory.csv")
    convert.link(bucket, rec["source"], "library/records/inventory.md")
    manifest = (bucket / "sources" / "MANIFEST.md").read_text(encoding="utf-8")
    row = manifest.strip().splitlines()[-1]
    assert row.split("|")[-2].strip() == "library/records/inventory.md"
    # a second link comma-appends
    convert.link(bucket, rec["source"], "library/records/inventory-2.md")
    manifest = (bucket / "sources" / "MANIFEST.md").read_text(encoding="utf-8")
    assert manifest.count("inventory.md, library/records/inventory-2.md") == 1


def test_link_unknown_source_refused(bucket):
    with pytest.raises(convert.IntakeError, match="manifest"):
        convert.link(bucket, "records/ghost.csv", "library/x.md")


def test_cleanup_removes_only_the_run_dir(bucket):
    put_inbox(bucket, "photo.png", fx.make_png)
    rec = admit(bucket, "photo.png")
    out = convert.prepare(bucket, rec["source"])
    run_dir = bucket / out["run_dir"]
    assert run_dir.is_dir()
    convert.cleanup(run_dir)
    assert not run_dir.exists()
    assert (bucket / "workbench" / ".intake").is_dir()


def test_cleanup_refuses_outside_workbench_intake(tmp_path):
    stray = tmp_path / "not-a-run-dir"
    stray.mkdir()
    with pytest.raises(convert.IntakeError, match="refusing"):
        convert.cleanup(stray)
    assert stray.exists()


def test_slugify():
    assert convert.slugify("Q1 Scores (FINAL).xlsx") == "q1-scores-final"
    assert len(convert.slugify("x" * 200)) <= 60


def test_slugify_strips_html_extensions():
    assert convert.slugify("Q3 Channel Report.html") == "q3-channel-report"
    assert convert.slugify("client-portal.htm") == "client-portal"


# ── fidelity hardening: merged cells, html mail, colliding attachments ────

def test_html_only_mail_reads_clean(bucket):
    put_inbox(bucket, "quote.eml", fx.make_html_eml)
    rec = admit(bucket, "quote.eml")
    record = convert.prepare(bucket, rec["source"])
    # decoded entities, no tags, no script/style payload
    text = record["pages"][0]["text"]
    assert "Dupont & Fils" in text
    assert "alert(" not in text
    assert "color:red" not in text
    assert "<p>" not in text


def test_mail_attachments_never_collide(bucket):
    put_inbox(bucket, "riders.eml", fx.make_eml_colliding_attachments)
    rec = admit(bucket, "riders.eml")
    record = convert.prepare(bucket, rec["source"])
    assert sorted(record["attachments"]) == ["rider-2.txt", "rider.txt"]
    # and both files exist with their own content in the run dir
    run_dir = bucket / record["run_dir"]
    assert (run_dir / "rider.txt").read_bytes() == b"rider one\n"
    assert (run_dir / "rider-2.txt").read_bytes() == b"rider two\n"


def test_mail_attachments_never_collide_case_insensitively(bucket):
    put_inbox(bucket, "riders-case.eml", fx.make_eml_casefold_colliding_attachments)
    rec = admit(bucket, "riders-case.eml")
    record = convert.prepare(bucket, rec["source"])
    assert len(set(record["attachments"])) == 2
    run_dir = bucket / record["run_dir"]
    # both files exist on disk with their own bytes — no macOS clobber
    names = record["attachments"]
    contents = {n: (run_dir / n).read_bytes() for n in names}
    assert set(contents.values()) == {b"rider upper\n", b"rider lower\n"}
    # both attachment files present on disk (plus manifest.json) — the
    # second name was disambiguated, not silently clobbered by the first
    assert {p.name for p in run_dir.iterdir()} == set(names) | {"manifest.json"}


def test_mail_hostile_dotdot_filename_defused(bucket):
    put_inbox(bucket, "hostile.eml", fx.make_eml_dotdot_attachment)
    rec = admit(bucket, "hostile.eml")
    record = convert.prepare(bucket, rec["source"])
    assert record["attachments"] == ["attachment.bin"]
    run_dir = bucket / record["run_dir"]
    assert (run_dir / "attachment.bin").read_bytes() == b"payload\n"


def test_merged_cells_keep_their_anchor_value(bucket):
    put_inbox(bucket, "forecast.xlsx", fx.make_merged_xlsx)
    rec = admit(bucket, "forecast.xlsx")
    record = convert.prepare(bucket, rec["source"])
    doc = (bucket / record["output_file"]).read_text(encoding="utf-8")
    body = doc.split("---\n", 2)[2]
    assert "Q3 forecast" in body
    assert "| strings | 42.5 |" in body
    assert "| item | amount |" in body          # column B survived pruning
    assert "| Q3 forecast | Q3 forecast |" in body   # anchor unfolds across the merge
    assert "| Wide title | Wide title |" in body     # merge-spanned column survives pruning


@pytest.mark.skipif(shutil.which("soffice") is None and shutil.which("libreoffice") is None,
                    reason="LibreOffice not installed")
def test_docx_page_break_yields_two_pages(bucket):
    put_inbox(bucket, "onboarding.docx", fx.make_docx_two_page)
    rec = admit(bucket, "onboarding.docx")
    record = convert.prepare(bucket, rec["source"])
    assert record["page_count"] >= 2
    assert len(record["images"]) == record["page_count"]


def test_html_to_text_direct():
    out = convert.html_to_text(
        "<style>x{}</style><script>bad()</script>"
        "<p>A &amp; B</p><p>C</p>")
    assert out == "A & B\nC"


def test_html_routes_to_libreoffice():
    assert convert._route(".html") == "libreoffice"
    assert convert._route(".htm") == "libreoffice"
    assert ".html" in convert.SUPPORTED_EXTS
    assert ".htm" in convert.SUPPORTED_EXTS


@pytest.mark.skipif(shutil.which("soffice") is None and shutil.which("libreoffice") is None,
                    reason="LibreOffice not installed")
def test_html_page_via_libreoffice(bucket):
    put_inbox(bucket, "report.html", fx.make_html_page)
    rec = admit(bucket, "report.html")
    record = convert.prepare(bucket, rec["source"])
    assert record["path"] == "libreoffice"
    assert record["page_count"] == len(record["pages"]) >= 1
    assert len(record["images"]) == record["page_count"]
    joined = " ".join(p["text"] for p in record["pages"])
    assert "412000" in joined


def test_cell_to_string_floats_verbatim():
    """The lossless contract: numbers verbatim, never rounded away."""
    assert convert.cell_to_string(78.5) == "78.5"
    assert convert.cell_to_string(91.0) == "91"
    assert convert.cell_to_string(78.123456789) == "78.123456789"
    assert convert.cell_to_string(0.00001) == "1e-05"
    assert convert.cell_to_string(-0.00001) == "-1e-05"


# ── containers are delivery vehicles, not originals ─────────────────────

def test_unpack_container_into_inbox_folder(bucket):
    zpath = bucket / "inbox" / "bundle.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.writestr("manifest.json", '{"a": 1}')
        zf.writestr("notes/a.md", "# note")
        zf.writestr("assets/b.pdf", "%PDF-1.4 fake")
    out = convert.unpack(bucket, "bundle.zip")
    dest = bucket / "inbox" / "bundle"
    assert (dest / "manifest.json").is_file()
    assert (dest / "notes" / "a.md").is_file()
    assert (dest / "assets" / "b.pdf").is_file()
    assert not zpath.exists()               # the vehicle is discarded
    assert out["unpacked"] == 3
    assert out["dir"] == "inbox/bundle"


def test_unpack_nested_container_stays_beside_parent(bucket):
    # A container that already lives inside an unpacked delivery's
    # sub-folder must unpack beside itself, not fly back up to inbox root
    # and lose its folder context.
    nested_dir = bucket / "inbox" / "delivery" / "assets"
    nested_dir.mkdir(parents=True)
    zpath = nested_dir / "inner.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.writestr("payload.txt", "nested contents")
    out = convert.unpack(bucket, "delivery/assets/inner.zip")
    dest = nested_dir / "inner"
    assert (dest / "payload.txt").is_file()
    assert not zpath.exists()
    assert out["unpacked"] == 1
    assert out["dir"] == "inbox/delivery/assets/inner"
    # sibling of the container, NOT flattened up to inbox root
    assert not (bucket / "inbox" / "inner").exists()


def test_unpack_refuses_zip_slip(bucket):
    zpath = bucket / "inbox" / "evil.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.writestr("../evil.txt", "pwned")
    with pytest.raises(convert.IntakeError, match="evil"):
        convert.unpack(bucket, "evil.zip")
    # nothing written outside inbox, destination folder not left behind
    assert not (bucket / "inbox" / "evil").exists()
    assert not (bucket.parent / "evil.txt").exists()
    assert zpath.exists()                   # the hostile zip itself is untouched


def test_unpack_refuses_traversal_crafted_file_argument(bucket, tmp_path):
    evil = tmp_path / "evil.zip"          # OUTSIDE the bucket
    import zipfile
    with zipfile.ZipFile(evil, "w") as z:
        z.writestr("payload.txt", "boo")
    with pytest.raises(convert.IntakeError, match="escapes"):
        convert.unpack(bucket, "../../evil.zip")
    assert not (tmp_path / "evil").exists()   # nothing written outside


def test_unpack_refuses_existing_destination(bucket):
    zpath = bucket / "inbox" / "bundle.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.writestr("a.txt", "hi")
    (bucket / "inbox" / "bundle").mkdir()
    with pytest.raises(convert.IntakeError, match="exists"):
        convert.unpack(bucket, "bundle.zip")


def test_admit_still_refuses_containers(bucket):
    (bucket / "inbox" / "bundle.athena").write_bytes(b"not admitted directly")
    with pytest.raises(convert.IntakeError, match="unsupported"):
        admit(bucket, "bundle.athena")


def test_json_rides_the_text_route():
    assert convert._route(".json") == "text"
    assert ".yaml" in convert.SUPPORTED_EXTS
    assert ".yml" in convert.SUPPORTED_EXTS


def test_slugify_strips_structured_text_extensions():
    assert convert.slugify("manifest.json") == "manifest"
    assert convert.slugify("Deploy Config.yaml") == "deploy-config"
    assert convert.slugify("ci.yml") == "ci"


# ── batch: one op-list, validated whole, then moved ─────────────────────

def write_doc(root, rel, title):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(convert.render_document(
        {"title": title, "type": "note", "aurora": "library"},
        f"{title}.", "Body."), encoding="utf-8")
    return p


def manifest_rows(bucket):
    text = (bucket / "sources" / "MANIFEST.md").read_text(encoding="utf-8")
    return [ln for ln in text.strip().splitlines() if ln.strip().startswith("|")][2:]


def test_batch_happy_path(bucket):
    put_inbox(bucket, "a.csv", fx.make_csv)
    put_inbox(bucket, "b.csv", fx.make_csv)
    write_doc(bucket, "library/records/a.md", "A")
    write_doc(bucket, "library/records/b.md", "B")
    ops = {
        "admits": [{"file": "a.csv", "category": "records"},
                   {"file": "b.csv", "category": "records"}],
        "links": [{"source": "records/a.csv", "doc": "library/records/a.md"},
                  {"source": "records/b.csv", "doc": "library/records/b.md"}],
    }
    out = convert.batch(bucket, ops, actor="claude")
    assert out == {"admitted": 2, "linked": 2}
    assert not (bucket / "inbox" / "a.csv").exists()
    assert not (bucket / "inbox" / "b.csv").exists()
    assert (bucket / "sources" / "records" / "a.csv").is_file()
    assert (bucket / "sources" / "records" / "b.csv").is_file()
    rows = manifest_rows(bucket)
    assert len(rows) == 2
    for row in rows:
        cells = [c.strip() for c in row.strip("|").split("|")]
        assert cells[2] == "claude"
        assert cells[4] in ("library/records/a.md", "library/records/b.md")


def test_batch_validation_before_damage(bucket):
    # 3 admits: two good, one referencing a file that isn't in inbox/ at
    # all — the whole batch must abort before the first mutation.
    put_inbox(bucket, "a.csv", fx.make_csv)
    put_inbox(bucket, "b.csv", fx.make_csv)
    manifest_before = (bucket / "sources" / "MANIFEST.md").read_text(encoding="utf-8")
    ops = {
        "admits": [{"file": "a.csv", "category": "records"},
                   {"file": "ghost.csv", "category": "records"},
                   {"file": "b.csv", "category": "records"}],
        "links": [],
    }
    with pytest.raises(convert.IntakeError, match="inbox"):
        convert.batch(bucket, ops, actor="claude")
    # nothing moved, nothing appended — even the two good admits
    assert (bucket / "inbox" / "a.csv").is_file()
    assert (bucket / "inbox" / "b.csv").is_file()
    assert not (bucket / "sources" / "records").exists()
    manifest_after = (bucket / "sources" / "MANIFEST.md").read_text(encoding="utf-8")
    assert manifest_after == manifest_before


def test_batch_validation_catches_bad_link_before_any_admit(bucket):
    put_inbox(bucket, "a.csv", fx.make_csv)
    ops = {
        "admits": [{"file": "a.csv", "category": "records"}],
        "links": [{"source": "records/nope.csv", "doc": "library/x.md"}],
    }
    with pytest.raises(convert.IntakeError, match="link source"):
        convert.batch(bucket, ops, actor="claude")
    assert (bucket / "inbox" / "a.csv").is_file()
    assert not (bucket / "sources" / "records").exists()


def test_batch_link_source_declared_in_same_batch_works(bucket):
    # the link's source isn't in sources/ yet — it's one of THIS batch's
    # own admits (forward reference within one call, no separate admit()
    # round trip needed).
    put_inbox(bucket, "a.csv", fx.make_csv)
    write_doc(bucket, "library/records/a.md", "A")
    ops = {
        "admits": [{"file": "a.csv", "category": "records"}],
        "links": [{"source": "records/a.csv", "doc": "library/records/a.md"}],
    }
    out = convert.batch(bucket, ops, actor="claude")
    assert out == {"admitted": 1, "linked": 1}
    row = manifest_rows(bucket)[0]
    assert row.split("|")[-2].strip() == "library/records/a.md"


def test_batch_link_source_already_admitted_before_batch(bucket):
    # the link's source was admitted in a PRIOR, separate admit() call —
    # not part of this batch's admits at all.
    put_inbox(bucket, "old.csv", fx.make_csv)
    admit(bucket, "old.csv")
    write_doc(bucket, "library/records/old.md", "Old")
    ops = {"admits": [], "links": [{"source": "records/old.csv",
                                    "doc": "library/records/old.md"}]}
    out = convert.batch(bucket, ops, actor="claude")
    assert out == {"admitted": 0, "linked": 1}


def test_batch_missing_link_doc_aborts_before_any_link_written(bucket):
    # admits succeed (the mechanical half is done); the doc for one link
    # was never written — nothing partial: NO link gets applied, not even
    # the one whose doc does exist.
    put_inbox(bucket, "a.csv", fx.make_csv)
    put_inbox(bucket, "b.csv", fx.make_csv)
    write_doc(bucket, "library/records/a.md", "A")
    # b.md deliberately not written
    ops = {
        "admits": [{"file": "a.csv", "category": "records"},
                   {"file": "b.csv", "category": "records"}],
        "links": [{"source": "records/a.csv", "doc": "library/records/a.md"},
                  {"source": "records/b.csv", "doc": "library/records/b.md"}],
    }
    with pytest.raises(convert.IntakeError, match="library/records/b.md"):
        convert.batch(bucket, ops, actor="claude")
    # both admits landed — the mechanical half is not rolled back
    assert (bucket / "sources" / "records" / "a.csv").is_file()
    assert (bucket / "sources" / "records" / "b.csv").is_file()
    # but NEITHER link was written — not even the one with a real doc
    for row in manifest_rows(bucket):
        cells = [c.strip() for c in row.strip("|").split("|")]
        assert cells[4] == "—"


def test_batch_rejects_duplicate_category_basename_within_batch(bucket):
    put_inbox(bucket, "dupe.csv", fx.make_csv)
    (bucket / "inbox" / "sub").mkdir()
    (bucket / "inbox" / "sub" / "dupe.csv").write_bytes(
        (bucket / "inbox" / "dupe.csv").read_bytes())
    ops = {"admits": [{"file": "dupe.csv", "category": "records"},
                      {"file": "sub/dupe.csv", "category": "records"}],
           "links": []}
    with pytest.raises(convert.IntakeError, match="duplicate"):
        convert.batch(bucket, ops, actor="claude")
    assert not (bucket / "sources" / "records").exists()


def test_batch_rejects_basename_collision_against_existing_manifest_row(bucket):
    put_inbox(bucket, "dupe.csv", fx.make_csv)
    admit(bucket, "dupe.csv")   # already a MANIFEST row for records/dupe.csv
    put_inbox(bucket, "dupe2.csv", fx.make_csv)
    (bucket / "inbox" / "dupe2.csv").rename(bucket / "inbox" / "dupe.csv")
    ops = {"admits": [{"file": "dupe.csv", "category": "records"}],
           "links": []}
    with pytest.raises(convert.IntakeError, match="immutable"):
        convert.batch(bucket, ops, actor="claude")


def test_batch_rejects_bad_actor(bucket):
    put_inbox(bucket, "a.csv", fx.make_csv)
    ops = {"admits": [{"file": "a.csv", "category": "records"}], "links": []}
    with pytest.raises(convert.IntakeError, match="actor"):
        convert.batch(bucket, ops, actor="two words")
    assert (bucket / "inbox" / "a.csv").is_file()


def test_batch_rejects_link_doc_not_zone_relative(bucket):
    put_inbox(bucket, "a.csv", fx.make_csv)
    ops = {"admits": [{"file": "a.csv", "category": "records"}],
           "links": [{"source": "records/a.csv", "doc": "inbox/sneaky.md"}]}
    with pytest.raises(convert.IntakeError, match="zone"):
        convert.batch(bucket, ops, actor="claude")
    assert (bucket / "inbox" / "a.csv").is_file()


def test_batch_rejects_duplicate_inbox_file_in_two_admits(bucket):
    put_inbox(bucket, "a.csv", fx.make_csv)
    ops = {"admits": [{"file": "a.csv", "category": "records"},
                      {"file": "a.csv", "category": "other"}],
           "links": []}
    with pytest.raises(convert.IntakeError, match="twice"):
        convert.batch(bucket, ops, actor="claude")
    assert (bucket / "inbox" / "a.csv").is_file()
    assert not (bucket / "sources" / "records").exists()
    assert not (bucket / "sources" / "other").exists()


def test_batch_empty_ops_is_a_noop(bucket):
    out = convert.batch(bucket, {"admits": [], "links": []}, actor="claude")
    assert out == {"admitted": 0, "linked": 0}


def test_batch_refuses_disk_only_collision_before_any_mutation(bucket):
    # z.pdf sits in sources/records/ with NO MANIFEST row — a hand-placed
    # file, not something admit() ever wrote. Checking existing_rels alone
    # would let a.csv's admit run before z.pdf's own dest.exists() refusal
    # fires mid-batch, with no rollback — the disk itself must be checked
    # in phase 1, before ANY mutation.
    put_inbox(bucket, "a.csv", fx.make_csv)
    seed_source(bucket, "records/z.pdf", "not a real pdf, just a placeholder")
    put_inbox(bucket, "z.pdf", lambda p: p.write_bytes(b"%PDF-1.4 fake"))
    manifest_before = (bucket / "sources" / "MANIFEST.md").read_text(encoding="utf-8")
    ops = {"admits": [{"file": "a.csv", "category": "records"},
                      {"file": "z.pdf", "category": "records"}],
           "links": []}
    with pytest.raises(convert.IntakeError, match="immutable"):
        convert.batch(bucket, ops, actor="claude")
    # a.csv (the good op, ordered first) is still in inbox — nothing moved
    assert (bucket / "inbox" / "a.csv").is_file()
    assert (bucket / "inbox" / "z.pdf").is_file()
    manifest_after = (bucket / "sources" / "MANIFEST.md").read_text(encoding="utf-8")
    assert manifest_after == manifest_before


def test_batch_rejects_traversal_doc_path(bucket):
    # "library/../inbox/evil.md" lexically starts with "library" (passes a
    # naive split-on-"/" zone check) but normalizes to "inbox/evil.md" —
    # not a doc zone at all.
    put_inbox(bucket, "a.csv", fx.make_csv)
    manifest_before = (bucket / "sources" / "MANIFEST.md").read_text(encoding="utf-8")
    ops = {"admits": [{"file": "a.csv", "category": "records"}],
           "links": [{"source": "records/a.csv",
                      "doc": "library/../inbox/evil.md"}]}
    with pytest.raises(convert.IntakeError, match="zone"):
        convert.batch(bucket, ops, actor="claude")
    assert (bucket / "inbox" / "a.csv").is_file()
    assert not (bucket / "sources" / "records").exists()
    manifest_after = (bucket / "sources" / "MANIFEST.md").read_text(encoding="utf-8")
    assert manifest_after == manifest_before
