"""link-repair: scan proposes, apply signs off — the human gate holds
in between (docs/dogfood/frictions.md row 7, today's two live sweeps)."""

import json

import pytest
import yaml
from conftest import seed_source, write_doc  # noqa: F401 (fixture import)

import link_repair as lr


# ── scan ─────────────────────────────────────────────────────────────────


def test_scan_proposes_exact_unique_basename_match(bucket):
    seed_source(bucket, "cat/x.pdf", "pdf bytes")
    write_doc(bucket, "library/notes/doc.md", "See [the file](assets/x.pdf).")

    result = lr.scan(bucket)

    assert result["proposals"] == [
        {
            "doc": "library/notes/doc.md",
            "link": "assets/x.pdf",
            "target": "../../sources/cat/x.pdf",
            "confidence": "exact",
        }
    ]
    assert result["unrepairable"] == []


def test_scan_normalized_match_is_fuzzy_not_exact(bucket):
    # amua-map.png vs a-mua-map.png: same letters once hyphens are
    # stripped and case is folded, but never the same basename — a fuzzy
    # proposal, never silently merged with an exact one.
    seed_source(bucket, "maps/a-mua-map.png", "png bytes")
    write_doc(bucket, "library/notes/doc.md", "See [the map](assets/amua-map.png).")

    result = lr.scan(bucket)

    assert result["proposals"] == [
        {
            "doc": "library/notes/doc.md",
            "link": "assets/amua-map.png",
            "target": "../../sources/maps/a-mua-map.png",
            "confidence": "fuzzy",
        }
    ]


def test_scan_two_candidates_never_guesses(bucket):
    seed_source(bucket, "cat-a/dup.pdf", "pdf bytes a")
    seed_source(bucket, "cat-b/dup.pdf", "pdf bytes b")
    write_doc(bucket, "library/notes/doc.md", "See [it](assets/dup.pdf).")

    result = lr.scan(bucket)

    assert result["proposals"] == []
    assert result["unrepairable"] == [
        {
            "doc": "library/notes/doc.md",
            "link": "assets/dup.pdf",
        }
    ]


def test_scan_ignores_http_mailto_and_anchor_links(bucket):
    write_doc(
        bucket,
        "library/notes/doc.md",
        "See [site](https://example.com/x), "
        "[mail](mailto:a@example.com), and [section](#heading).",
    )

    result = lr.scan(bucket)

    assert result["proposals"] == []
    assert result["unrepairable"] == []


def test_scan_working_link_is_not_reported(bucket):
    write_doc(bucket, "library/notes/other.md", "Sibling.")
    write_doc(bucket, "library/notes/doc.md", "See [sibling](other.md).")

    result = lr.scan(bucket)

    assert result["proposals"] == []
    assert result["unrepairable"] == []


def test_scan_notes_sibling_rename_pattern(bucket):
    # notes/X.md -> sibling X.md: the link nests into "notes/" a second
    # time but the real file sits beside the referring doc — the exact
    # shape from the live sweep.
    write_doc(bucket, "library/notes/old-name.md", "Sibling target.")
    write_doc(bucket, "library/notes/doc.md", "See [related](notes/old-name.md).")

    result = lr.scan(bucket)

    assert result["proposals"] == [
        {
            "doc": "library/notes/doc.md",
            "link": "notes/old-name.md",
            "target": "old-name.md",
            "confidence": "exact",
        }
    ]


def test_scan_ignores_fenced_placeholder_even_with_real_match(bucket):
    # The reviewer's named risk: a real file with a placeholder basename
    # must no longer be proposable from a fenced code example — code is
    # not prose, and a fence's contents were never a link.
    seed_source(bucket, "cat/x.pdf", "pdf bytes")
    write_doc(
        bucket,
        "library/notes/doc.md",
        "Example:\n\n```\nSee [the file](assets/x.pdf).\n```\n",
    )

    result = lr.scan(bucket)

    assert result["proposals"] == []
    assert result["unrepairable"] == []


def test_scan_ignores_inline_code_span(bucket):
    write_doc(
        bucket,
        "library/notes/doc.md",
        "Inline: `[x](assets/gone.md)` is not a real link.",
    )

    result = lr.scan(bucket)

    assert result["proposals"] == []
    assert result["unrepairable"] == []


def test_scan_ignores_double_backtick_span_real_link_still_proposed(bucket):
    # CommonMark's literal-backtick idiom: `` `code with ` backtick` ``
    # closes only on the matching TWO-backtick run, so the inner single
    # backtick (and the [x](gone.md) riding on it) is content, never a
    # terminator — gone.md must stay invisible while real.md still gets
    # scanned and proposed normally.
    write_doc(bucket, "library/notes/real.md", "Real target.")
    write_doc(
        bucket,
        "library/notes/sub/doc.md",
        "See `` [x](gone.md)` `` and then [real](real.md).",
    )

    result = lr.scan(bucket)

    assert result["proposals"] == [
        {
            "doc": "library/notes/sub/doc.md",
            "link": "real.md",
            "target": "../real.md",
            "confidence": "exact",
        }
    ]
    assert result["unrepairable"] == []


def test_scan_finds_real_link_after_inline_code_span_same_line(bucket):
    # The reviewer's named same-line case: a single-backtick span
    # followed immediately by a real link must not swallow the link.
    write_doc(bucket, "library/notes/real.md", "Real target.")
    write_doc(
        bucket,
        "library/notes/sub/doc.md",
        "`code` [real](real.md) right after the span.",
    )

    result = lr.scan(bucket)

    assert result["proposals"] == [
        {
            "doc": "library/notes/sub/doc.md",
            "link": "real.md",
            "target": "../real.md",
            "confidence": "exact",
        }
    ]
    assert result["unrepairable"] == []


def test_scan_real_broken_link_outside_fence_still_proposed(bucket):
    seed_source(bucket, "cat/x.pdf", "pdf bytes")
    write_doc(
        bucket,
        "library/notes/doc.md",
        "```\nSee [placeholder](assets/x.pdf).\n```\n\n"
        "Real: [the file](assets/x.pdf).\n",
    )

    result = lr.scan(bucket)

    assert result["proposals"] == [
        {
            "doc": "library/notes/doc.md",
            "link": "assets/x.pdf",
            "target": "../../sources/cat/x.pdf",
            "confidence": "exact",
        }
    ]
    assert result["unrepairable"] == []


def test_scan_activities_zone_is_walked_too(bucket):
    seed_source(bucket, "cat/y.pdf", "pdf bytes")
    write_doc(bucket, "activities/proj/doc.md", "See [it](assets/y.pdf).")

    result = lr.scan(bucket)

    assert result["proposals"][0]["doc"] == "activities/proj/doc.md"


# ── apply ────────────────────────────────────────────────────────────────


def _fm(text: str) -> dict:
    body = text.split("---\n", 2)[1]
    return yaml.safe_load(body)


def test_apply_rewrites_only_listed_pairs_and_bumps_updated(bucket):
    seed_source(bucket, "cat/x.pdf", "pdf bytes")
    doc = write_doc(
        bucket,
        "library/notes/doc.md",
        "Broken: [a](assets/x.pdf). Untouched: [b](https://example.com).",
    )
    proposals = [
        {
            "doc": "library/notes/doc.md",
            "link": "assets/x.pdf",
            "target": "../../sources/cat/x.pdf",
            "confidence": "exact",
        }
    ]

    changed = lr.apply_proposals(bucket, proposals)

    assert changed == 1
    text = doc.read_text(encoding="utf-8")
    assert "](../../sources/cat/x.pdf)" in text
    assert "](https://example.com)" in text  # untouched
    fm = _fm(text)
    assert fm["updated"] == lr.TODAY


def test_apply_adds_updated_when_absent(bucket):
    seed_source(bucket, "cat/x.pdf", "pdf bytes")
    doc = write_doc(bucket, "library/notes/doc.md", "Broken: [a](assets/x.pdf).")
    proposals = [
        {
            "doc": "library/notes/doc.md",
            "link": "assets/x.pdf",
            "target": "../../sources/cat/x.pdf",
            "confidence": "exact",
        }
    ]

    lr.apply_proposals(bucket, proposals)

    fm = _fm(doc.read_text(encoding="utf-8"))
    assert fm["updated"] == lr.TODAY
    assert fm["title"]  # existing keys preserved


def test_apply_refuses_doc_outside_doc_zones(bucket):
    (bucket / "workbench" / "scratch.md").write_text(
        "---\ntitle: x\ntype: note\naurora: library\n---\n\n## Summary\n\nx\n\n---\n\n"
        "[a](assets/x.pdf)\n",
        encoding="utf-8",
    )
    seed_source(bucket, "cat/x.pdf", "pdf bytes")
    proposals = [
        {
            "doc": "workbench/scratch.md",
            "link": "assets/x.pdf",
            "target": "../sources/cat/x.pdf",
            "confidence": "exact",
        }
    ]

    with pytest.raises(lr.RepairError, match="library/|activities/"):
        lr.apply_proposals(bucket, proposals)


def test_apply_refuses_when_target_missing_and_writes_nothing(bucket):
    doc = write_doc(
        bucket,
        "library/notes/doc.md",
        "Broken: [a](assets/x.pdf). Also: [b](assets/y.pdf).",
    )
    seed_source(bucket, "cat/y.pdf", "pdf bytes")
    proposals = [
        {
            "doc": "library/notes/doc.md",
            "link": "assets/x.pdf",
            "target": "../../sources/cat/ghost.pdf",
            "confidence": "exact",
        },
        {
            "doc": "library/notes/doc.md",
            "link": "assets/y.pdf",
            "target": "../../sources/cat/y.pdf",
            "confidence": "exact",
        },
    ]
    before = doc.read_text(encoding="utf-8")

    with pytest.raises(lr.RepairError, match="does not exist"):
        lr.apply_proposals(bucket, proposals)

    # validate-all-before-writing: the good pair in the same batch must
    # not have been applied either.
    assert doc.read_text(encoding="utf-8") == before


def test_apply_refuses_traversal_target_outside_bucket(bucket):
    doc = write_doc(bucket, "library/notes/doc.md", "Broken: [a](assets/x.pdf).")
    outside = bucket.parent / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    proposals = [
        {
            "doc": "library/notes/doc.md",
            "link": "assets/x.pdf",
            "target": "../../../outside.txt",
            "confidence": "exact",
        }
    ]
    before = doc.read_text(encoding="utf-8")

    with pytest.raises(lr.RepairError, match="escapes"):
        lr.apply_proposals(bucket, proposals)
    assert doc.read_text(encoding="utf-8") == before


def test_apply_all_or_nothing_across_documents(bucket):
    # Doc A has good frontmatter and a valid proposal; doc B has NO
    # frontmatter block at all and is listed AFTER doc A in the batch.
    # Phase 1 must catch B's malformed frontmatter before phase 2 ever
    # writes A — a later doc's defect must not let an earlier doc's write
    # through (contract: one bad proposal -> zero writes).
    seed_source(bucket, "cat/x.pdf", "pdf bytes")
    seed_source(bucket, "cat/y.pdf", "pdf bytes")
    doc_a = write_doc(bucket, "library/notes/a.md", "Broken: [a](assets/x.pdf).")
    doc_b = bucket / "library" / "notes" / "b.md"
    doc_b.write_text(
        "No frontmatter here.\n\nBroken: [b](assets/y.pdf).\n", encoding="utf-8"
    )
    before_a = doc_a.read_text(encoding="utf-8")
    before_b = doc_b.read_text(encoding="utf-8")
    proposals = [
        {
            "doc": "library/notes/a.md",
            "link": "assets/x.pdf",
            "target": "../../sources/cat/x.pdf",
            "confidence": "exact",
        },
        {
            "doc": "library/notes/b.md",
            "link": "assets/y.pdf",
            "target": "../../sources/cat/y.pdf",
            "confidence": "exact",
        },
    ]

    with pytest.raises(lr.RepairError, match="no frontmatter block"):
        lr.apply_proposals(bucket, proposals)

    assert doc_a.read_text(encoding="utf-8") == before_a
    assert doc_b.read_text(encoding="utf-8") == before_b


def test_apply_refuses_index_md(bucket):
    seed_source(bucket, "cat/x.pdf", "pdf bytes")
    index = write_doc(bucket, "library/INDEX.md", "Broken: [a](assets/x.pdf).")
    before = index.read_text(encoding="utf-8")
    proposals = [
        {
            "doc": "library/INDEX.md",
            "link": "assets/x.pdf",
            "target": "../sources/cat/x.pdf",
            "confidence": "exact",
        }
    ]

    with pytest.raises(lr.RepairError, match="INDEX|skip"):
        lr.apply_proposals(bucket, proposals)

    assert index.read_text(encoding="utf-8") == before


def test_apply_no_ledger_write(bucket):
    seed_source(bucket, "cat/x.pdf", "pdf bytes")
    write_doc(bucket, "library/notes/doc.md", "Broken: [a](assets/x.pdf).")
    proposals = [
        {
            "doc": "library/notes/doc.md",
            "link": "assets/x.pdf",
            "target": "../../sources/cat/x.pdf",
            "confidence": "exact",
        }
    ]
    ledger_before = (bucket / "LEDGER.md").read_text(encoding="utf-8")

    lr.apply_proposals(bucket, proposals)

    assert (bucket / "LEDGER.md").read_text(encoding="utf-8") == ledger_before


# ── CLI ──────────────────────────────────────────────────────────────────


def test_cli_scan_emits_json_on_stdout(bucket, capsys):
    seed_source(bucket, "cat/x.pdf", "pdf bytes")
    write_doc(bucket, "library/notes/doc.md", "Broken: [a](assets/x.pdf).")

    rc = lr.main(["scan", "--bucket", str(bucket)])

    assert rc == 0
    out = capsys.readouterr()
    payload = json.loads(out.out)
    assert payload["proposals"][0]["confidence"] == "exact"


def test_cli_apply_reads_proposals_file(bucket, tmp_path, capsys):
    seed_source(bucket, "cat/x.pdf", "pdf bytes")
    write_doc(bucket, "library/notes/doc.md", "Broken: [a](assets/x.pdf).")
    proposals_file = tmp_path / "proposals.json"
    proposals_file.write_text(
        json.dumps(
            {
                "proposals": [
                    {
                        "doc": "library/notes/doc.md",
                        "link": "assets/x.pdf",
                        "target": "../../sources/cat/x.pdf",
                        "confidence": "exact",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    rc = lr.main(["apply", "--bucket", str(bucket), "--proposals", str(proposals_file)])

    assert rc == 0
    out = capsys.readouterr()
    payload = json.loads(out.out)
    assert payload["changed"] == 1


def test_scan_working_titled_and_angled_links_not_reported(bucket):
    """CommonMark §6.3 titles / angle brackets are legal — a link whose
    file exists is never proposed and never unrepairable."""
    write_doc(bucket, "library/notes/other.md", "Body.")
    write_doc(
        bucket,
        "library/notes/doc.md",
        'A [t](other.md "The Other") and an [a](<other.md>) link.',
    )

    result = lr.scan(bucket)

    assert result["proposals"] == []
    assert result["unrepairable"] == []


def test_scan_and_apply_preserve_commonmark_title(bucket):
    """A broken titled link repairs to the new path with its title kept —
    repair fixes the path, never eats the prose."""
    seed_source(bucket, "cat/x.pdf", "pdf bytes")
    write_doc(bucket, "library/notes/doc.md", 'See [f](assets/x.pdf "The File").')

    result = lr.scan(bucket)

    assert result["proposals"] == [
        {
            "doc": "library/notes/doc.md",
            "link": 'assets/x.pdf "The File"',
            "target": '../../sources/cat/x.pdf "The File"',
            "confidence": "exact",
        }
    ]
    assert lr.apply_proposals(bucket, result["proposals"]) == 1
    text = (bucket / "library" / "notes" / "doc.md").read_text(encoding="utf-8")
    assert '[f](../../sources/cat/x.pdf "The File")' in text
