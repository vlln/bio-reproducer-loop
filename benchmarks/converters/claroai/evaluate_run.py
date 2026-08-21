"""Evaluate a completed calibration run against its entry oracle (BL-013 / Plan 0025).

Usage:
    PYTHONPATH=. python3.12 benchmarks/converters/claroai/evaluate_run.py \\
        /storeData/gs/claroai-calibration/runs/bench-220 benchmarks/entries/bench-220
    # with a hand-curated claims-evidence mapping for legacy runs:
    PYTHONPATH=. python3.12 benchmarks/converters/claroai/evaluate_run.py \\
        /storeData/gs/claroai-calibration/runs/bench-221 benchmarks/entries/bench-221 \\
        --claims-evidence claims_evidence_bench-221.json

Reads the run's repro-data/04_data/data_manifest.md + 03_provision/provision.md as
D1-D3 evidence and 06_validate/report.md as D5 claims evidence (role=validate_report),
runs the entry's oracle verify.py via the independent evaluator, and prints
evaluator verdict/score/checks alongside the author calibration
(claims.yaml calibration section — author scores are calibration-only).

`--claims-evidence` stages a JSON file of the form
{"claims": [{"metric": "<claim metric>", "actual": <value>, ...}, ...]}
as the validate_report artifact — used to feed legacy runs whose validate report
metrics cannot be matched to claims automatically (cross-language names).
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path


def main(run_dir: str, entry_dir: str, claims_evidence: str | None = None) -> dict:
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
    vr = run / "repro-data" / "06_validate" / "report.md"
    found = []
    if dm.exists():
        shutil.copy(dm, art / "data_manifest.md")
        found.append("data_manifest")
    if prov.exists():
        shutil.copy(prov, art / "provision_report.md")
        found.append("provision_report")
    artifacts = [{"role": "data_manifest", "path": "artifacts/data_manifest.md"},
                 {"role": "provision_report", "path": "artifacts/provision_report.md"}]
    if claims_evidence:
        shutil.copy(claims_evidence, art / "validate_report.md")
        found.append("claims_evidence")
        artifacts.append({"role": "validate_report", "path": "artifacts/validate_report.md"})
    elif vr.exists():
        shutil.copy(vr, art / "validate_report.md")
        found.append("validate_report")
        artifacts.append({"role": "validate_report", "path": "artifacts/validate_report.md"})

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
        "artifacts": artifacts,
        "execution": {"purpose": "validation-only", "isolation": "container",
                      "provider": "docker", "stages": []},
    }
    (tmp / eid / "submission.json").write_text(json.dumps(sub))
    r = evaluate_submission(tmp / eid, tmp / eid / "submission.json")
    result = {
        "entry": eid,
        "evaluator_verdict": r.get("verdict"),
        "evaluator_score": r.get("score"),
        "checks": [{"id": c.get("check_id") or c.get("id"), "passed": c.get("passed"), "note": c.get("note")}
                   for c in r.get("checks", [])],
        "author_calibration": claims.get("calibration"),
        "artifacts_found": found,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("entry_dir")
    ap.add_argument("--claims-evidence", default=None)
    args = ap.parse_args()
    main(args.run_dir, args.entry_dir, args.claims_evidence)
