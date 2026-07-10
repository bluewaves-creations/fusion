from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = REPO_ROOT / "examples" / "crazy-ones"


@pytest.fixture
def fixture_bucket() -> Path:
    assert FIXTURE.is_dir(), "examples/crazy-ones must exist — it is normative"
    return FIXTURE
