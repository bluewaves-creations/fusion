"""Stage-1 gate: deterministic classification of inbox/ against sources/."""
import json
from pathlib import Path

from conftest import drop, seed_source

import gate


# Non-repeating texts: word shingles must be distinct enough that a prefix
# scores ~0.5 (update band) and a near-copy scores >0.85 (near-dup band).
LONG_A = (
    "the quarterly supplier scorecard for acme corporation shows steady "
    "delivery performance and improving quality metrics across twelve "
    "categories measured this period with lead times shrinking notably "
    "while defect rates fell under one percent and the audit team praised "
    "warehouse traceability packaging compliance and the newly digitised "
    "certificate register maintained by the procurement office in lyon"
)
LONG_B = (
    "annual brand review for northwind traders covering social reach "
    "engagement conversion and the ambassador program launched during the "
    "spring campaign window with television spend redirected toward short "
    "form video creators whose audiences overlap the target demographic "
    "according to the panel study commissioned from the media lab"
)


def run_gate(root):
    idx = gate.index_sources(root / "sources")
    return gate.classify_intake(root / "inbox", root / "sources", idx)


def test_exact_duplicate_auto_skips(bucket):
    seed_source(bucket, "reports/q1.csv", LONG_A)
    drop(bucket, "q1-copy.csv", LONG_A)
    result = run_gate(bucket)
    assert len(result["exact_dups"]) == 1
    entry = result["exact_dups"][0]
    assert entry["matched_source"] == "reports/q1.csv"
    assert entry["auto_skip"] is True


def test_clean_new_when_nothing_matches(bucket):
    seed_source(bucket, "reports/q1.csv", LONG_A)
    drop(bucket, "totally-else.csv", LONG_B)
    result = run_gate(bucket)
    assert [e["incoming"] for e in result["clean_new"]] == ["totally-else.csv"]


def test_near_dup_flagged_never_skipped(bucket):
    seed_source(bucket, "reports/q1.csv", LONG_A)
    drop(bucket, "renamed-thing.csv", LONG_A + " one extra trailing clause")
    result = run_gate(bucket)
    assert len(result["near_dups"]) == 1
    assert result["near_dups"][0]["auto_skip"] is False
    assert result["near_dups"][0]["similarity"] >= gate.NEAR_DUP_THRESHOLD


def test_update_candidate_needs_name_match(bucket):
    seed_source(bucket, "reports/q1-report.csv", LONG_A)
    # Same normalized name, ~half-overlapping content -> update band
    half = LONG_A[: len(LONG_A) // 2]
    drop(bucket, "2026-07-01_q1-report.csv", half)
    result = run_gate(bucket)
    assert len(result["update_candidates"]) == 1
    cand = result["update_candidates"][0]
    assert cand["matched_source"] == "reports/q1-report.csv"
    assert gate.UPDATE_SIM_FLOOR <= cand["similarity"] < gate.NEAR_DUP_THRESHOLD


def test_moderate_overlap_without_name_match_is_near_dup(bucket):
    seed_source(bucket, "reports/q1-report.csv", LONG_A)
    half = LONG_A[: len(LONG_A) // 2]
    drop(bucket, "different-name.csv", half)
    result = run_gate(bucket)
    assert len(result["near_dups"]) == 1
    assert not result["update_candidates"]


def test_manifest_and_dotfiles_ignored(bucket):
    drop(bucket, ".DS_Store", "junk")
    result = run_gate(bucket)
    assert all(not v for v in result.values())
    # MANIFEST.md in sources/ never appears as a match candidate
    seed_source(bucket, "notes/a.txt", LONG_A)
    idx = gate.index_sources(bucket / "sources")
    assert "MANIFEST.md" not in {p for paths in idx.by_hash.values() for p in paths}


def test_normalize_filename():
    assert gate.normalize_filename("2026-07-01_Q1 Report.xlsx") == "q1-report"
    assert gate.normalize_filename("Price__List--FINAL.csv") == "price-list-final"


def test_main_writes_manifest_into_workbench(bucket):
    seed_source(bucket, "reports/q1.csv", LONG_A)
    drop(bucket, "new-doc.csv", LONG_B)
    rc = gate.main(["--bucket", str(bucket)])
    assert rc == 0
    runs = list((bucket / "workbench" / ".intake").glob("gate-*.json"))
    assert len(runs) == 1
    data = json.loads(runs[0].read_text(encoding="utf-8"))
    assert data["counts"] == {"exact_dups": 0, "near_dups": 0,
                              "update_candidates": 0, "clean_new": 1}


def test_locked_lineage_thresholds():
    """The bands are lineage-locked (plan Global Constraints) — a changed
    constant is a spec break, not a tuning knob."""
    assert gate.NEAR_DUP_THRESHOLD == 0.85
    assert gate.UPDATE_SIM_FLOOR == 0.30
    assert gate.SHINGLE_K == 3


def test_similarity_no_evidence_is_zero():
    assert gate.similarity("", "") == 0.0
    assert gate.similarity("... !!! ---", "%%% ***") == 0.0


def test_sub_shingle_texts_score_zero_by_design():
    # below SHINGLE_K words there is no evidence — identity is sha256's job
    assert gate.similarity("hello world", "hello world") == 0.0
    assert gate.similarity("invoice 4521", "invoice 4522") == 0.0


def test_binary_pair_is_clean_new_not_near_dup(bucket):
    noise_a = b"\x89PNG\r\n\x1a\n" + b"\x00\x01\x02\xff\xfe" * 24
    noise_b = b"\x89PNG\r\n\x1a\n" + b"\x03\x04\x05\xfd\xfc" * 24
    (bucket / "sources" / "img-a.png").write_bytes(noise_a)
    (bucket / "inbox" / "img-b.png").write_bytes(noise_b)
    result = run_gate(bucket)
    assert result["near_dups"] == []
    assert [f["incoming"] for f in result["clean_new"]] == ["img-b.png"]


def test_git_history_survives_missing_cwd(tmp_path):
    assert gate.git_history(Path("sources/x.pdf"), tmp_path / "absent") == []
