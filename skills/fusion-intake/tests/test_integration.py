"""End-to-end: real formats through gate -> admit -> prepare -> link,
with the fusion CLI as the conformance oracle. Requires the repo checkout
(uses uv --project cli); skipped outside it."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

import convert
import gate
import make_fixtures as fx

REPO = Path(__file__).resolve().parents[3]
CLI = REPO / "cli"
HAVE_CLI = (CLI / "pyproject.toml").is_file()


def fusion(*args, cwd):
    return subprocess.run(
        ["uv", "run", "--project", str(CLI), "fusion", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=120,
        env={**os.environ, "FUSION_ACTOR": "claude"},
    )


@pytest.mark.skipif(not HAVE_CLI, reason="fusion CLI checkout not found")
def test_real_formats_end_to_end(bucket):
    drops = {
        "scores.xlsx": fx.make_xlsx,
        "inventory.csv": fx.make_csv,
        "audit.pdf": fx.make_text_pdf,
        "mail.eml": fx.make_eml,
    }
    if shutil.which("soffice"):
        drops["procedure.docx"] = fx.make_docx
    for name, maker in drops.items():
        maker(bucket / "inbox" / name)

    # Stage-1 gate: all clean_new on an empty sources/
    idx = gate.index_sources(bucket / "sources")
    buckets = gate.classify_intake(bucket / "inbox", bucket / "sources", idx)
    assert len(buckets["clean_new"]) == len(drops)

    for name in drops:
        rec = convert.admit(bucket, name, category="records", actor="claude")
        out = convert.prepare(bucket, rec["source"])
        if out["done"]:
            doc_rel = out["output_file"]
        else:
            # Deterministic stand-in for the vision half: text pages only.
            body = "\n\n".join(p["text"] for p in out["pages"]) or "*(image content)*"
            doc_rel = out["output_file"]
            doc = bucket / doc_rel
            doc.parent.mkdir(parents=True, exist_ok=True)
            doc.write_text(
                convert.render_document(
                    out["front_matter_seed"], "Converted for the integration run.", body
                ),
                encoding="utf-8",
            )
            convert.cleanup(bucket / out["run_dir"])
        convert.link(bucket, rec["source"], doc_rel)
        r = fusion(
            "log", "converted", f"sources/{rec['source']} → {doc_rel}", cwd=bucket
        )
        assert r.returncode == 0, r.stderr

    r = fusion("index", cwd=bucket)
    assert r.returncode == 0, r.stderr
    r = fusion("check", str(bucket), "--json", cwd=bucket)
    assert r.returncode == 0, f"check not green:\n{r.stdout}\n{r.stderr}"
    report = json.loads(r.stdout)
    assert report["errors"] == [] and report["warnings"] == []

    # admit() moves (not copies) each file out of inbox/ into sources/, so
    # by now inbox is already empty — verify that, then confirm check is
    # still green with nothing left to process.
    for name in drops:
        assert not (bucket / "inbox" / name).exists()
    r = fusion("check", str(bucket), cwd=bucket)
    assert r.returncode == 0
