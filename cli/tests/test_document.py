from fusion.document import (
    AURORAS,
    Document,
    read_document,
    split_frontmatter,
)


def test_auroras_are_the_eight_verbatim():
    assert AURORAS == (
        "commitments", "focus", "ops", "collab",
        "life", "explore", "archive", "library",
    )


def test_split_frontmatter_valid():
    fm, err, body = split_frontmatter("---\ntitle: X\ntype: note\n---\nbody\n")
    assert err is None
    assert fm == {"title": "X", "type": "note"}
    assert body == "body\n"


def test_split_frontmatter_absent():
    fm, err, body = split_frontmatter("just text\n")
    assert fm is None and "no frontmatter" in err and body == "just text\n"


def test_split_frontmatter_unterminated():
    fm, err, _ = split_frontmatter("---\ntitle: X\n")
    assert fm is None and "unterminated" in err


def test_split_frontmatter_not_a_mapping():
    fm, err, _ = split_frontmatter("---\n- a\n- b\n---\nbody\n")
    assert fm is None and "not a mapping" in err


def test_split_frontmatter_invalid_yaml():
    fm, err, _ = split_frontmatter("---\ntitle: [unclosed\n---\nbody\n")
    assert fm is None and "invalid YAML" in err


DOC = """---
title: Jazzmaster 1962
type: instrument
aurora: library
---

## Summary

A 1962 Fender Jazzmaster in sunburst — provenance, setup, and service
history for the studio's main guitar.

---

Body with a [link](pedalboard.md), an [up-link](../recipes/tape.md),
an [external](https://example.com/x), and an [anchor](#section).
"""


def test_read_document(tmp_path):
    p = tmp_path / "jazzmaster-1962.md"
    p.write_text(DOC, encoding="utf-8")
    doc = read_document(p)
    assert doc.title == "Jazzmaster 1962"
    assert doc.aurora == "library"
    assert doc.summary_first is True
    # first physical (non-blank) line of the Summary section, verbatim
    assert doc.summary_line == (
        "A 1962 Fender Jazzmaster in sunburst — provenance, setup, and service"
    )
    assert doc.links == ["pedalboard.md", "../recipes/tape.md"]


def test_read_document_not_summary_first(tmp_path):
    p = tmp_path / "x.md"
    p.write_text("---\ntitle: X\n---\n\n## Intro\n\ntext\n", encoding="utf-8")
    doc = read_document(p)
    assert doc.summary_first is False and doc.summary_line is None


def test_read_document_summary_without_separator(tmp_path):
    p = tmp_path / "x.md"
    p.write_text("---\ntitle: X\n---\n\n## Summary\n\ntext but no rule\n", encoding="utf-8")
    assert read_document(p).summary_first is False


def test_read_document_never_raises(tmp_path):
    p = tmp_path / "junk.md"
    p.write_text("no frontmatter, no summary", encoding="utf-8")
    doc = read_document(p)
    assert isinstance(doc, Document)
    assert doc.frontmatter is None and doc.title is None


def test_read_document_tolerates_undecodable_bytes(tmp_path):
    p = tmp_path / "binary.md"
    p.write_bytes(b"\xff\xfe\x00garbage")
    doc = read_document(p)
    assert doc.frontmatter is None
    assert "unreadable" in doc.fm_error


def test_summary_line_is_verbatim(tmp_path):
    p = tmp_path / "indented.md"
    p.write_text(
        "---\ntitle: I\n---\n\n## Summary\n\n  - an indented first line\n\n---\n\nBody.\n",
        encoding="utf-8",
    )
    assert read_document(p).summary_line == "  - an indented first line"


def test_read_document_strips_utf8_bom(tmp_path):
    body = ("---\ntitle: Bom Test\ntype: note\naurora: library\n---\n\n"
            "## Summary\n\nStill fine.\n\n---\n\nBody.\n")
    p = tmp_path / "doc.md"
    p.write_bytes(b"\xef\xbb\xbf" + body.encode("utf-8"))
    doc = read_document(p)
    assert doc.frontmatter is not None
    assert doc.title == "Bom Test"


def test_read_document_tolerates_crlf(tmp_path):
    body = ("---\ntitle: Crlf Test\ntype: note\naurora: library\n---\n\n"
            "## Summary\n\nStill fine.\n\n---\n\nBody.\n")
    p = tmp_path / "doc.md"
    p.write_bytes(body.replace("\n", "\r\n").encode("utf-8"))
    doc = read_document(p)
    assert doc.title == "Crlf Test"
    assert doc.summary_first
