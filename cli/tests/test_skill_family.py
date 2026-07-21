"""The skill-family structure gate — duplication + agentskills.io compliance.

Dynamic discovery: validates every skills/<name>/ that exists, so the gate
holds from the first skill to the fourth without edits.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / "skills"
FRONTMATTER_WHITELIST = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def skill_dirs():
    if not SKILLS_DIR.is_dir():
        return []
    return sorted(
        p for p in SKILLS_DIR.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()
    )


def parse_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path}: no frontmatter block"
    end = text.index("\n---", 4)
    import yaml

    fm = yaml.safe_load(text[4:end])
    assert isinstance(fm, dict), f"{path}: frontmatter is not a mapping"
    return fm


def test_at_least_one_skill_exists():
    assert skill_dirs(), "skills/ holds no skill directories yet"


@pytest.mark.parametrize("skill", skill_dirs(), ids=lambda p: p.name)
def test_frontmatter_compliance(skill):
    fm = parse_frontmatter(skill / "SKILL.md")
    unknown = set(fm) - FRONTMATTER_WHITELIST
    assert not unknown, f"non-standard frontmatter fields: {unknown}"
    assert fm["name"] == skill.name, "name must equal directory name"
    assert NAME_RE.match(fm["name"]), "name must be lowercase-hyphenated"
    assert len(fm["name"]) <= 64
    assert fm["description"].strip(), "description required"
    assert len(fm["description"]) <= 1024
    if "compatibility" in fm:
        assert len(fm["compatibility"]) <= 500


@pytest.mark.parametrize("skill", skill_dirs(), ids=lambda p: p.name)
def test_body_size(skill):
    lines = (skill / "SKILL.md").read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 500, f"SKILL.md is {len(lines)} lines (limit 500)"


@pytest.mark.parametrize("skill", skill_dirs(), ids=lambda p: p.name)
def test_carries_conventions_card(skill):
    assert (skill / "references" / "fusion-conventions.md").is_file(), (
        "every skill carries references/fusion-conventions.md"
    )


def test_conventions_cards_byte_identical():
    # Discovered independently of SKILL.md so the gate holds from Task 1,
    # when the canonical card exists before any SKILL.md does.
    cards = sorted(SKILLS_DIR.glob("*/references/fusion-conventions.md"))
    assert cards, "no conventions cards found"
    reference = cards[0].read_bytes()
    for card in cards[1:]:
        assert card.read_bytes() == reference, (
            f"{card} differs from {cards[0]} — the convention travels "
            "byte-identical or not at all"
        )


@pytest.mark.parametrize("skill", skill_dirs(), ids=lambda p: p.name)
def test_no_personal_paths(skill):
    for path in sorted(skill.rglob("*")):
        if path.is_file() and path.suffix in (".md", ".py"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert "/Users/" not in text and "bertrand" not in text.lower(), (
                f"{path}: personal path or name leaked"
            )
