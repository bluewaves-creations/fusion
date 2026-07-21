"""The repo's byte canon is LF. Python's text-mode writers translate
\\n -> \\r\\n on Windows unless newline="\\n" is pinned — that would break
byte-determinism for real, not just in CI's golden-fixture tests (a Windows
user running `fusion index` or `fusion log` would silently start writing
CRLF into their bucket's registers). This test pins the newline= parameter
by asserting the actual bytes on disk, and is meaningful on every OS."""

from fusion.cli import main


def test_index_writes_no_crlf(make_bucket, capsys):
    root = make_bucket()
    # Touch the tree so index has something to regenerate, then run it for real.
    (root / "library" / "extra.md").write_text(
        "---\ntitle: Extra\ntype: note\naurora: library\n---\n\n"
        "## Summary\n\nAnother note.\n\n---\n\nBody.\n",
        encoding="utf-8",
    )
    assert main(["index", str(root), "--as", "test"]) == 0
    capsys.readouterr()

    index_bytes = (root / "library" / "INDEX.md").read_bytes()
    assert b"\r" not in index_bytes
    assert index_bytes.endswith(b"\n")


def test_log_append_writes_no_crlf(make_bucket, capsys):
    root = make_bucket()
    assert (
        main(
            [
                "log",
                "noted",
                "library/notes.md",
                "--bucket",
                str(root),
                "--as",
                "test",
                "--note",
                "checked → clean",
            ]
        )
        == 0
    )
    capsys.readouterr()

    ledger_bytes = (root / "LEDGER.md").read_bytes()
    assert b"\r" not in ledger_bytes
    assert ledger_bytes.endswith(b"\n")
