import shutil

from fusion.checker import check


def errors(root):
    return [f for f in check(root) if f.level == "error"]


def codes(root):
    return {f.code for f in errors(root)}


def test_fixture_has_zero_errors(fixture_bucket):
    assert errors(fixture_bucket) == []


def test_scratch_bucket_is_clean(make_bucket):
    assert errors(make_bucket()) == []


def test_e1_missing_zone(make_bucket):
    root = make_bucket()
    shutil.rmtree(root / "workbench")
    found = errors(root)
    assert any(f.code == "E1" and "workbench" in f.message for f in found)


def test_e2_bucket_card_missing_and_missing_field(make_bucket):
    root = make_bucket()
    card = root / "BUCKET.md"
    text = card.read_text(encoding="utf-8").replace("kind: personal\n", "")
    card.write_text(text, encoding="utf-8")
    assert any(f.code == "E2" and "kind" in f.message for f in errors(root))
    card.unlink()
    assert "E2" in codes(root)


def test_e3_unparseable_and_missing_required_field(make_bucket):
    root = make_bucket()
    (root / "library" / "broken.md").write_text(
        "---\ntitle: [unclosed\n---\n\n## Summary\n\nx\n\n---\n\nBody.\n",
        encoding="utf-8",
    )
    (root / "output" / "untitled.md").write_text(
        "---\ntype: note\naurora: library\n---\n\n## Summary\n\nx\n\n---\n\nBody.\n",
        encoding="utf-8",
    )
    found = errors(root)
    assert any(f.code == "E3" and f.path == "library/broken.md" for f in found)
    assert any(f.code == "E3" and "title" in f.message for f in found)


def test_e4_unknown_aurora(make_bucket):
    root = make_bucket()
    (root / "library" / "weird.md").write_text(
        "---\ntitle: W\ntype: note\naurora: vibes\n---\n\n"
        "## Summary\n\nx\n\n---\n\nBody.\n",
        encoding="utf-8",
    )
    assert any(f.code == "E4" and "vibes" in f.message for f in errors(root))


def test_e5_not_summary_first(make_bucket):
    root = make_bucket()
    (root / "library" / "rushed.md").write_text(
        "---\ntitle: R\ntype: note\naurora: library\n---\n\nStraight to body.\n",
        encoding="utf-8",
    )
    assert any(f.code == "E5" and f.path == "library/rushed.md"
               for f in errors(root))


def test_e6_unknown_ledger_verb(make_bucket):
    root = make_bucket()
    with (root / "LEDGER.md").open("a", encoding="utf-8") as fh:
        fh.write("- 09:30 · test · yeeted · library/notes.md\n")
    assert any(f.code == "E6" and "yeeted" in f.message for f in errors(root))


def test_e7_both_directions(make_bucket):
    root = make_bucket()
    # a sources file with no manifest row
    (root / "sources" / "stray.csv").write_text("a,b\n", encoding="utf-8")
    assert any(f.code == "E7" and "stray.csv" in f.message for f in errors(root))
    # a manifest row whose file is gone
    with (root / "sources" / "MANIFEST.md").open("a", encoding="utf-8") as fh:
        fh.write("| ghost.pdf | 2026-07-10 | test | deadbeef00000000 | — |\n")
    assert any(f.code == "E7" and "ghost.pdf" in f.message for f in errors(root))


def test_e7_exemptions(make_bucket):
    root = make_bucket()
    (root / "sources" / ".gitkeep").write_text("", encoding="utf-8")
    assert "E7" not in codes(root)  # MANIFEST.md and dotfiles are invisible


def test_e8_filenames(make_bucket):
    root = make_bucket()
    valid_doc = (root / "library" / "notes.md").read_text(encoding="utf-8")
    (root / "library" / "Bad_Name.md").write_text(valid_doc, encoding="utf-8")
    (root / "library" / ("a" * 61 + ".md")).write_text(valid_doc, encoding="utf-8")
    (root / "activities" / "photo.png").write_text("", encoding="utf-8")
    found = [f for f in errors(root) if f.code == "E8"]
    paths = {f.path for f in found}
    assert "library/Bad_Name.md" in paths
    assert "library/" + "a" * 61 + ".md" in paths
    assert "activities/photo.png" in paths


def test_e8_exemptions(make_bucket):
    root = make_bucket()
    (root / "library" / ".gitkeep").write_text("", encoding="utf-8")
    assert "E8" not in codes(root)  # INDEX.md and dotfiles are invisible


def test_e8_output_export_conformant_slug_is_clean(make_bucket):
    root = make_bucket()
    exports = root / "output" / "exports"
    exports.mkdir(parents=True)
    (exports / "gear-export.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    assert "E8" not in codes(root)  # non-md deliverables MAY live in output/


def test_e8_output_export_bad_name_still_errors(make_bucket):
    root = make_bucket()
    exports = root / "output" / "exports"
    exports.mkdir(parents=True)
    (exports / "Bad Name.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    found = [f for f in errors(root) if f.code == "E8"]
    paths = {f.path for f in found}
    assert "output/exports/Bad Name.csv" in paths


def test_e8_non_md_outside_output_still_errors(make_bucket):
    root = make_bucket()
    (root / "library" / "gear").mkdir()
    (root / "library" / "gear" / "data.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    found = [f for f in errors(root) if f.code == "E8"]
    paths = {f.path for f in found}
    assert "library/gear/data.csv" in paths


def test_e3_null_or_blank_required_field(make_bucket):
    root = make_bucket()
    (root / "library" / "nulled.md").write_text(
        "---\ntitle: Nulled\ntype: note\naurora:\n---\n\n"
        "## Summary\n\nx\n\n---\n\nBody.\n",
        encoding="utf-8",
    )
    (root / "library" / "blank.md").write_text(
        '---\ntitle: ""\ntype: note\naurora: library\n---\n\n'
        "## Summary\n\nx\n\n---\n\nBody.\n",
        encoding="utf-8",
    )
    found = errors(root)
    assert any(f.code == "E3" and f.path == "library/nulled.md"
               and "aurora" in f.message for f in found)
    assert any(f.code == "E3" and f.path == "library/blank.md"
               and "title" in f.message for f in found)


def test_e2_unreadable_bucket_card(make_bucket):
    root = make_bucket()
    (root / "BUCKET.md").write_text("---\nname: [unclosed\n---\n\nBody.\n",
                                    encoding="utf-8")
    assert any(f.code == "E2" and "unreadable" in f.message
               for f in errors(root))


def test_dot_directories_are_invisible(make_bucket):
    root = make_bucket()
    trash = root / "library" / ".trash"
    trash.mkdir()
    (trash / "Not A Slug.md").write_text("no frontmatter at all",
                                         encoding="utf-8")
    cache = root / "sources" / ".cache"
    cache.mkdir()
    (cache / "junk file.pdf").write_bytes(b"%PDF-1.4")
    codes = {f.code for f in check(root)}
    assert not {"E3", "E5", "E7", "E8"} & codes


def test_blank_aurora_reports_e3_only(make_bucket):
    root = make_bucket()
    (root / "library" / "blank.md").write_text(
        '---\ntitle: Blank\ntype: note\naurora: ""\n---\n\n'
        "## Summary\n\nBlank aurora.\n\n---\n\nBody.\n",
        encoding="utf-8")
    findings = [f for f in check(root) if f.path.endswith("blank.md")]
    codes = [f.code for f in findings]
    assert "E3" in codes
    assert "E4" not in codes
