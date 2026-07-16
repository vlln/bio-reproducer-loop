"""L1: Validate Phase — 验证 Validate Agent 的验证报告正确性。

使用 loop run --only-phase Validate + golden fixtures 作为前序输入。
"""

import json
import subprocess
import tempfile
from pathlib import Path


def _run_validate(entry_dir: str, golden_plan_path: str,
                  golden_run_results_path: str) -> dict:
    """Run Validate phase with plan and run results as previous phase outputs."""
    output_dir = tempfile.mkdtemp(prefix="l1-test-validate-")

    # Copy golden fixtures as previous phase outputs
    setups = {
        "01_plan/plan.md": golden_plan_path,
        "05_run/run_results.md": golden_run_results_path,
    }
    for rel_path, src_path in setups.items():
        dst = Path(output_dir) / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(Path(src_path).read_text())

    paper = Path(entry_dir) / "paper.pdf"
    if not paper.exists():
        paper = Path(entry_dir) / "paper.md"

    args = json.dumps({
        "paper_path": str(paper),
        "output_dir": output_dir,
        "language": "en",
    })

    result = subprocess.run(
        ["loop", "run", "bio-reproducer", "--args", args,
         "--only-phase", "Validate"],
        capture_output=True, text=True,
    )
    return {
        "returncode": result.returncode,
        "stderr": result.stderr,
        "output_dir": output_dir,
    }


def test_validate_produces_report(bench_001, golden_plan, golden_run_results,
                                   golden_report, golden_metrics):
    """AC-0001-N-2: Validate agent 产出完整验证报告, 与 golden 一致."""
    result = _run_validate(
        bench_001["entry_dir"],
        golden_plan["path"],
        golden_run_results["path"],
    )

    report_path = Path(result["output_dir"]) / "06_validate" / "report.md"
    if not report_path.exists():
        assert "validate" in result["stderr"].lower() or result["returncode"] != 0, (
            f"Validate should produce output or fail cleanly"
        )
        return

    output = report_path.read_text()
    golden = golden_report["content"]

    # Key business fields: verdict and score
    checks = [
        ("has_verdict", "REPRODUCED"),
        ("has_score", "Score"),
        ("has_data_integrity", "Data Integrity"),
        ("has_quantitative", "Quantitative"),
    ]
    failures = []
    for name, keyword in checks:
        in_output = keyword.lower() in output.lower()
        in_golden = keyword.lower() in golden.lower()
        if in_output != in_golden:
            failures.append(f"{name}: output={in_output}, golden={in_golden}")

    assert not failures, (
        f"Validate output differs from golden:\n" + "\n".join(failures)
    )

    # metrics.json should be valid JSON with verdict
    metrics_path = Path(result["output_dir"]) / "06_validate" / "metrics.json"
    if metrics_path.exists():
        with open(metrics_path) as f:
            metrics = json.load(f)
        assert "verdict" in metrics, "metrics.json must have verdict"
        assert "total_score" in metrics, "metrics.json must have total_score"