"""Stage-1 engine: admit -> MANIFEST, extractive conversion, vision prep,
link, cleanup. The lossless contract, tested."""
import shutil

import pytest
import yaml
from conftest import bucket  # noqa: F401 (fixture)

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
    out = convert.prepare(bucket, rec["source"])
    assert out["path"] == "image"
    assert out["pages"] == [{"page": 1, "text": "", "text_chars": 0,
                             "needs_vision": True}]
    assert len(out["images"]) == 1


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


def test_cell_to_string_floats_verbatim():
    """The lossless contract: numbers verbatim, never rounded away."""
    assert convert.cell_to_string(78.5) == "78.5"
    assert convert.cell_to_string(91.0) == "91"
    assert convert.cell_to_string(78.123456789) == "78.123456789"
    assert convert.cell_to_string(0.00001) == "1e-05"
    assert convert.cell_to_string(-0.00001) == "-1e-05"
