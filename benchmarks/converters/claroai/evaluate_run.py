"""Evaluate a completed calibration run against its entry oracle (BL-013).

Usage:
    PYTHONPATH=. python3.12 benchmarks/converters/claroai/evaluate_run.py \\
        /storeData/gs/claroai-calibration/runs/bench-220 benchmarks/entries/bench-220

Reads the run's repro-data/04_data/data_manifest.md + 03_provision/provision.md as
audit evidence, runs the entry's oracle verify.py via the independent evaluator,
and prints evaluator verdict/score/checks alongside the author calibration
(claims.yaml calibration section — author scores are calibration-only).
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path


def main(run_dir: str, entry_dir: str) -> dict:
    run, entry = Path(run_dir), Path(entry_dir)
    eid = entry.name
    tmp = Path(tempfile.mkdtemp(prefix=f"cal-{eid}-"))
    shutil.copytree(entry, tmp / eid)
    shutil.rmtree(tmp / eid / "input")
    shutil.copytree(entry / "input", tmp / eid / "input")

    art = tmp / eid / "artifacts"
    art.mkdir()
    dm = run / "repro-data" / "04_data" / "data_manifest.md"
    prov = run / "repro-data" / "03_provision" / "provision.md"
    found = []
    if dm.exists():
        shutil.copy(dm, art / "data_manifest.md")
        found.append("data_manifest")
    if prov.exists():
        shutil.copy(prov, art / "provision_report.md")
        found.append("provision_report")

    import yaml
    from benchmarks.runner.independent_evaluator import evaluate_submission
    from benchmarks.runner.bundle_validator import validate_entry
    validate_entry(entry)
    claims = yaml.safe_load((entry / "oracle" / "claims.yaml").read_text())

    sub = {
        "protocol_version": "2.0",
        "submission_id": f"{eid}-cal",
        "bench_id": eid,
        "system": {"name": "bio-reproducer", "version": "0.1.0"},
        "claimed_verdict": "REPRODUCED",
        "artifacts": [{"role": "data_manifest", "path": "artifacts/data_manifest.md"},
                      {"role": "provision_report", "path": "artifacts/provision_report.md"}],
        "execution": {"purpose": "validation-only", "isolation": "container",
                      "provider": "docker", "stages": []},
    }
    (tmp / eid / "submission.json").write_text(json.dumps(sub))
    r = evaluate_submission(tmp / eid, tmp / eid / "submission.json")
    result = {
        "entry": eid,
        "evaluator_verdict": r.get("verdict"),
        "evaluator_score": r.get("score"),
        "checks": [{"id": c.get("id"), "passed": c.get("passed"), "note": c.get("note")}
                   for c in r.get("checks", [])],
        "author_calibration": claims.get("calibration"),
        "artifacts_found": found,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: evaluate_run.py <run_dir> <entry_dir>", file=sys.stderr)
        sys.exit(2)
    main(sys.argv[1], sys.argv[2])
