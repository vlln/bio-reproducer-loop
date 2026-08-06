"""Evaluate a completed ClaroAI calibration run against the entry oracle.

Usage:
    python3.12 benchmarks/converters/claroai/evaluate_run.py <run_dir> <entry_dir>

Consumes the agent's actual audit artifacts (data_manifest.md / provision_report.md)
from a completed loopflow run, builds a submission, and runs the independent
evaluator (python_verify against oracle/verify.py + claims.yaml ground truth).

Works both for remote runs (pass the /storeData/gs/claroai-calibration/runs/...
path after fetching, or run on the remote host) and local runs.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

import yaml

ARTIFACT_ROLES = (
    ("data_manifest", ("04_data", "data_manifest.md")),
    ("provision_report", ("03_provision", "provision.md")),
)


def evaluate_run(run_dir: str | Path, entry_dir: str | Path) -> dict:
    from benchmarks.runner.independent_evaluator import evaluate_submission

    run = Path(run_dir)
    entry = Path(entry_dir)
    eid = entry.name
    tmp = Path(tempfile.mkdtemp(prefix=f"eval-{eid}-"))
    shutil.copytree(entry, tmp / eid)
    shutil.rmtree(tmp / eid / "input")
    shutil.copytree(entry / "input", tmp / eid / "input")

    repro = run / "repro-data"
    artifacts = []
    for role, (subdir, name) in ARTIFACT_ROLES:
        src = repro / subdir / name
        if not src.exists():
            cands = list(repro.rglob(name))
            src = cands[0] if cands else None
        if src is not None:
            dst = tmp / eid / "artifacts" / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)
            artifacts.append({"role": role, "path": f"artifacts/{name}"})

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
    (tmp / eid / "submission.json").write_text(json.dumps(sub, indent=2))
    result = evaluate_submission(tmp / eid, tmp / eid / "submission.json")

    claims = yaml.safe_load((entry / "oracle" / "claims.yaml").read_text())
    return {
        "entry": eid,
        "verdict": result.get("verdict"),
        "score": result.get("score"),
        "checks": [
            {"id": c.get("id"), "passed": c.get("passed"), "note": c.get("note")}
            for c in result.get("checks", [])
        ],
        "author_calibration": claims.get("calibration"),
        "artifacts_found": [a.get("role") for a in artifacts],
    }


def main(argv: list[str] | None = None) -> None:
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    out = evaluate_run(sys.argv[1], sys.argv[2])
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
