"""Windows console default codepages (cp1252, etc.) can't encode the arrows
and mid-dots fusion's human-readable output uses. main_entry() reconfigures
stdout/stderr to UTF-8 before anything is printed — this proves that
reconfiguration actually takes effect, without needing a real Windows box."""

import io

from fusion.cli import _utf8_streams


def test_utf8_streams_reconfigures_cp1252_stdout(monkeypatch):
    buffer = io.BytesIO()
    cp1252_stdout = io.TextIOWrapper(buffer, encoding="cp1252")
    monkeypatch.setattr("sys.stdout", cp1252_stdout)

    _utf8_streams()

    # Before the fix this print would raise UnicodeEncodeError: cp1252
    # cannot encode U+2192 (→).
    print("→ setup complete")
    cp1252_stdout.flush()

    # _utf8_streams() only reconfigures encoding — it leaves newline
    # translation alone. On Windows, TextIOWrapper's default (universal)
    # newline mode still writes os.linesep, so '\n' becomes '\r\n' in the
    # buffer. That is ordinary console behavior, not part of fusion's
    # contract (the contract is: UTF-8 survives), so normalize it away here
    # rather than pinning newline="\n" in production stream setup.
    written = buffer.getvalue().decode("utf-8").replace("\r\n", "\n")
    assert written == "→ setup complete\n"


def test_utf8_streams_reconfigures_cp1252_stderr(monkeypatch):
    buffer = io.BytesIO()
    cp1252_stderr = io.TextIOWrapper(buffer, encoding="cp1252")
    monkeypatch.setattr("sys.stderr", cp1252_stderr)

    _utf8_streams()

    print("· drift, not damage", file=cp1252_stderr)
    cp1252_stderr.flush()

    # Same rationale as the stdout case above: normalize the platform's
    # newline translation, not the encoding under test.
    written = buffer.getvalue().decode("utf-8").replace("\r\n", "\n")
    assert written == "· drift, not damage\n"


def test_utf8_streams_never_raises_on_streams_without_reconfigure(monkeypatch):
    """Detached/odd streams (embedded contexts, some redirected pipes) may
    lack reconfigure() entirely, or raise when it's called. Either way the
    CLI must not crash on the way to doing real work."""

    class NoReconfigure:
        pass

    class RaisesOnReconfigure:
        def reconfigure(self, **kwargs):
            raise ValueError("nope")

    monkeypatch.setattr("sys.stdout", NoReconfigure())
    monkeypatch.setattr("sys.stderr", RaisesOnReconfigure())

    _utf8_streams()  # must not raise
