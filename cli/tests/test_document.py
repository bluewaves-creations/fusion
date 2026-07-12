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


# ── code is not prose ───────────────────────────────────────────────────

def _doc(body: str) -> str:
    return ("---\ntitle: X\ntype: note\naurora: library\n---\n\n"
            "## Summary\n\nS.\n\n---\n\n" + body)


def test_links_ignores_fenced_block_only_link(tmp_path):
    body = "Text before.\n\n```\nSee [x](broken.md) for an example.\n```\n\nText after.\n"
    p = tmp_path / "x.md"
    p.write_text(_doc(body), encoding="utf-8")
    assert read_document(p).links == []


def test_links_ignores_inline_code_span(tmp_path):
    body = "Inline: `[x](gone.md)` is not a real link.\n"
    p = tmp_path / "x.md"
    p.write_text(_doc(body), encoding="utf-8")
    assert read_document(p).links == []


def test_links_ignores_double_backtick_span_with_inner_backtick(tmp_path):
    # CommonMark's literal-backtick idiom: `` `code with ` backtick` ``
    # opens and closes on a run of TWO backticks, so the single backtick
    # (and the link riding on it) in the middle is just content, not a
    # terminator — only real.md is a real link.
    body = "See `` [x](gone.md)` `` … then [real](real.md).\n"
    p = tmp_path / "x.md"
    p.write_text(_doc(body), encoding="utf-8")
    assert read_document(p).links == ["real.md"]


def test_links_finds_real_link_after_inline_code_span_same_line(tmp_path):
    body = "See `code` [x](real.md) right after the span.\n"
    p = tmp_path / "x.md"
    p.write_text(_doc(body), encoding="utf-8")
    assert read_document(p).links == ["real.md"]


def test_links_finds_real_link_between_two_fences(tmp_path):
    body = (
        "```\n[a](fenced-one.md)\n```\n\n"
        "See [real](real.md) here.\n\n"
        "```\n[b](fenced-two.md)\n```\n"
    )
    p = tmp_path / "x.md"
    p.write_text(_doc(body), encoding="utf-8")
    assert read_document(p).links == ["real.md"]


def test_links_unterminated_fence_swallows_to_eof(tmp_path):
    body = "Before [real](real.md).\n\n```\n[a](fenced.md)\nno closer here\n"
    p = tmp_path / "x.md"
    p.write_text(_doc(body), encoding="utf-8")
    assert read_document(p).links == ["real.md"]


def test_links_tilde_fence_also_blanked(tmp_path):
    body = "~~~\n[a](fenced.md)\n~~~\n\nSee [real](real.md).\n"
    p = tmp_path / "x.md"
    p.write_text(_doc(body), encoding="utf-8")
    assert read_document(p).links == ["real.md"]


def test_summary_only_field(tmp_path):
    p = tmp_path / "stub.md"
    p.write_text("---\ntitle: S\ntype: note\naurora: library\n---\n\n"
                 "## Summary\n\nOnly this.\n\n---\n", encoding="utf-8")
    assert read_document(p).summary_only is True
    p2 = tmp_path / "real.md"
    p2.write_text("---\ntitle: S\ntype: note\naurora: library\n---\n\n"
                  "## Summary\n\nLine.\n\n---\n\nBody.\n", encoding="utf-8")
    assert read_document(p2).summary_only is False
    p3 = tmp_path / "loose.md"
    p3.write_text("---\ntitle: S\ntype: note\naurora: library\n---\n\nProse.\n",
                  encoding="utf-8")
    assert read_document(p3).summary_only is False
