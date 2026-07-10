"""Read Fusion documents — the liberal reader (SPEC §0, §4)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

AURORAS: tuple[str, ...] = (
    "commitments", "focus", "ops", "collab",
    "life", "explore", "archive", "library",
)

FILENAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
MAX_STEM = 60

_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
_EXTERNAL = ("http://", "https://", "mailto:", "#")
_FENCE_OPEN_RE = re.compile(r"^(\s*)(`{3,}|~{3,})")
_INLINE_CODE_RE = re.compile(r"`[^`\n]*?`")


def _blank_code(body: str) -> str:
    """Blank fenced blocks and inline code spans so link scanning never
    reads code as prose (SPEC's W4 is about prose links, not examples).
    Fenced blocks — a ``` or ~~~ opener to its closer inclusive — are
    replaced with equal-length whitespace, line by line; an unterminated
    fence is liberal by design and swallows to end of file rather than
    risk a false-positive broken link. Inline `` `...` `` spans on a
    single line are blanked the same way, non-greedy."""
    lines = body.split("\n")
    out = []
    i = 0
    n = len(lines)
    while i < n:
        opener = _FENCE_OPEN_RE.match(lines[i])
        if not opener:
            out.append(lines[i])
            i += 1
            continue
        fence_char, fence_len = opener.group(2)[0], len(opener.group(2))
        closer_re = re.compile(
            r"^\s*" + re.escape(fence_char) + "{" + str(fence_len) + ",}\\s*$"
        )
        out.append(" " * len(lines[i]))
        i += 1
        while i < n:
            out.append(" " * len(lines[i]))
            closed = bool(closer_re.match(lines[i]))
            i += 1
            if closed:
                break
    blanked = "\n".join(out)
    return _INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), blanked)


@dataclass
class Document:
    path: Path
    frontmatter: dict | None
    fm_error: str | None
    summary_first: bool
    summary_line: str | None
    links: list[str] = field(default_factory=list)

    def _get(self, key: str):
        return (self.frontmatter or {}).get(key)

    @property
    def title(self):
        return self._get("title")

    @property
    def type(self):
        return self._get("type")

    @property
    def aurora(self):
        return self._get("aurora")

    @property
    def status(self):
        return self._get("status")


def split_frontmatter(text: str) -> tuple[dict | None, str | None, str]:
    """Return (frontmatter, error, body). Liberal: never raises."""
    if not text.startswith("---\n"):
        return None, "no frontmatter block", text
    end = text.find("\n---\n", 3)
    if end == -1:
        return None, "unterminated frontmatter block", text
    raw, body = text[4 : end + 1], text[end + 5 :]
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        return None, f"invalid YAML: {exc}", body
    if not isinstance(data, dict):
        return None, "frontmatter is not a mapping", body
    return data, None, body


def _summary(body: str) -> tuple[bool, str | None]:
    """Summary-first per SPEC §4: '## Summary', ≥1 line, then a '---' line."""
    lines = body.split("\n")
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i == len(lines) or lines[i].strip() != "## Summary":
        return False, None
    first: str | None = None
    for line in lines[i + 1 :]:
        stripped = line.strip()
        if stripped == "---":
            return first is not None, first
        if stripped and first is None:
            first = line
    return False, first


def _links(body: str) -> list[str]:
    out = []
    for target in _LINK_RE.findall(_blank_code(body)):
        if not target.startswith(_EXTERNAL):
            out.append(target)
    return out


def read_document(path: Path) -> Document:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        return Document(
            path=path,
            frontmatter=None,
            fm_error=f"unreadable file: {exc}",
            summary_first=False,
            summary_line=None,
            links=[],
        )
    fm, fm_error, body = split_frontmatter(text)
    summary_first, summary_line = _summary(body)
    return Document(
        path=path,
        frontmatter=fm,
        fm_error=fm_error,
        summary_first=summary_first,
        summary_line=summary_line,
        links=_links(body),
    )
