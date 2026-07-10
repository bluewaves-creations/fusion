"""Build hook: bundle the repo's skills/fusion-* into the wheel as
fusion/_skills/. The repo's skills/ directory is the single source of
truth; this hook re-stages it at every build, so the wheel cannot drift.

Source resolution order:
  1. <cli>/../skills   — normal repo build
  2. <cli>/skills      — building from an sdist (the sdist hook below
                         copies skills/ inside so wheel-from-sdist works)
"""
import shutil
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

EXCLUDE = ("tests", "__pycache__", ".pytest_cache")


def _skills_source(root: Path) -> Path:
    for candidate in (root.parent / "skills", root / "skills"):
        if sorted(candidate.glob("fusion-*")):
            return candidate
    raise RuntimeError(
        f"no fusion-* skills found beside {root} — cannot build fusion-cli"
    )


class SkillsBundleHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version, build_data):
        root = Path(self.root)
        src = _skills_source(root)
        if self.target_name == "sdist":
            # ship skills/ inside the sdist so a wheel built from it
            # finds them via resolution order #2
            build_data.setdefault("force_include", {})
            for skill in sorted(src.glob("fusion-*")):
                build_data["force_include"][str(skill)] = f"skills/{skill.name}"
            return
        staged = root / "src" / "fusion" / "_skills"
        if staged.exists():
            shutil.rmtree(staged)
        for skill in sorted(src.glob("fusion-*")):
            shutil.copytree(skill, staged / skill.name,
                            ignore=shutil.ignore_patterns(*EXCLUDE))

    def finalize(self, version, build_data, artifact_path):
        staged = Path(self.root) / "src" / "fusion" / "_skills"
        if staged.exists():
            shutil.rmtree(staged)
