"""Evaluate a completed calibration run against its entry oracle（新证据面，单元 04）。

Usage:
    PYTHONPATH=. python3.12 benchmarks/converters/claroai/evaluate_run.py \\
        /storeData/gs/claroai-calibration/runs/bench-220 benchmarks/entries/bench-220

Reads only the new-contract evidence: 05_run/answers.csv + 04_data sha256sums +
03_provision digests（ADR-0011 §4：06_validate/ 不在证据面），runs the entry's
oracle verify.py via the independent evaluator, and prints evaluator verdict/
score/checks alongside the author calibration（calibration-only）。

旧协议 run（pilot，无 answers/digests）不可用新口径重评——直接报错。
"""
from __future__ import annotations

import argparse
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
    # 证据面切换（ADR-0011 §4，单元 04）：只读标准格式真实产物；
    # 06_validate/ 不在证据面。旧 run（pilot）无 answers/digests → NO-EVIDENCE
    answers = run / "repro-data" / "05_run" / "answers.csv"
    digests = run / "repro-data" / "03_provision" / "digests.txt"
    checksums = run / "repro-data" / "04_data" / "sha256sums.txt"
    found = []
    artifacts = []
    if answers.exists():
        shutil.copy(answers, art / "answers.csv")
        found.append("answers")
        artifacts.append({"role": "answers", "path": "artifacts/answers.csv"})
        # answers 的 source_file 指向 05_run/results/（ADR-0011 §4/FC-005 交叉核对）：
        # 必须把 results/ 一并打包进 artifacts/，否则 verify 的
        # `answers_path.parent / source_file` 解析不到（2026-08-27 run4 实证：
        # 交叉核对失败 — source_file 不存在）。
        results_src = run / "repro-data" / "05_run" / "results"
        if results_src.is_dir():
            shutil.copytree(results_src, art / "results")
    if checksums.exists():
        shutil.copy(checksums, art / "sha256sums.txt")
        found.append("data_evidence")
        artifacts.append({"role": "data_evidence", "path": "artifacts/sha256sums.txt"})
    if digests.exists():
        shutil.copy(digests, art / "digests.txt")
        found.append("environment")
        artifacts.append({"role": "environment", "path": "artifacts/digests.txt"})
    if not artifacts:
        raise SystemExit(f"error: {eid} run 无新契约证据（answers/sha256sums/digests 均缺失）；"
                         f"该 run 属旧协议（pilot），不可用新口径重评")

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
    args = ap.parse_args()
    main(args.run_dir, args.entry_dir)
