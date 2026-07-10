"""The wheel carries the four skills, byte-identical to the repo's."""
import subprocess
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
CLI = REPO / "cli"
SKILLS = REPO / "skills"
EXCLUDED_PARTS = {"tests", "__pycache__", ".pytest_cache"}


@pytest.fixture(scope="module")
def wheel(tmp_path_factory) -> zipfile.ZipFile:
    out = tmp_path_factory.mktemp("dist")
    subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(out)],
        cwd=CLI, check=True, capture_output=True,
    )
    whl = next(out.glob("fusion_cli-*.whl"))
    return zipfile.ZipFile(whl)


def _repo_skill_files() -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for skill in sorted(SKILLS.glob("fusion-*")):
        for f in sorted(skill.rglob("*")):
            if f.is_dir():
                continue
            rel = f.relative_to(SKILLS)
            if EXCLUDED_PARTS & set(rel.parts):
                continue
            files[f"fusion/_skills/{rel.as_posix()}"] = f.read_bytes()
    return files


def test_wheel_bundles_all_four_skills(wheel):
    names = {n for n in wheel.namelist() if n.startswith("fusion/_skills/")}
    tops = {n.split("/")[2] for n in names}
    assert tops == {"fusion-intake", "fusion-librarian",
                    "fusion-planner", "fusion-analyst"}


def test_bundled_tree_is_byte_identical(wheel):
    expected = _repo_skill_files()
    assert expected, "repo skills must exist"
    bundled = {n: wheel.read(n) for n in wheel.namelist()
               if n.startswith("fusion/_skills/")}
    assert bundled == expected


def test_no_test_dirs_in_wheel(wheel):
    assert not [n for n in wheel.namelist()
                if n.startswith("fusion/_skills/")
                and EXCLUDED_PARTS & set(n.split("/"))]


def test_conventions_card_x4_inside_wheel(wheel):
    cards = [wheel.read(f"fusion/_skills/fusion-{s}/references/fusion-conventions.md")
             for s in ("intake", "librarian", "planner", "analyst")]
    assert len({c for c in cards}) == 1
