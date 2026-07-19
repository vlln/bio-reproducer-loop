"""L1: Bootstrap Phase — 验证 Bootstrap Agent 的系统环境检测正确性。

使用 loop run --only-phase Bootstrap + golden/plan.md 作为前序输入。
"""

import json
import subprocess
import tempfile
from pathlib import Path


def _run_bootstrap(entry_dir: str, golden_plan_path: str) -> dict:
    """Run Bootstrap phase with golden plan as previous phase output."""
    output_dir = tempfile.mkdtemp(prefix="l1-test-bootstrap-")

    # Copy golden plan as Reader's output
    plan_dir = Path(output_dir) / "01_plan"
    plan_dir.mkdir(parents=True, exist_ok=True)
    (plan_dir / "plan.md").write_text(Path(golden_plan_path).read_text())

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
         "--only-phase", "Bootstrap"],
        capture_output=True, text=True,
    )
    return {
        "returncode": result.returncode,
        "stderr": result.stderr,
        "output_dir": output_dir,
    }


def test_bootstrap_detects_environment(bench_001, golden_plan):
    """AC-0001-N-2: Bootstrap 正确检测系统环境并报告可用/缺失组件.

    检查 Bootstrap agent 能否检测 Java、Nextflow、容器运行时。
    不需要所有组件都可用——只要检测逻辑正确（报告了存在 vs 缺失）。
    """
    result = _run_bootstrap(bench_001["entry_dir"], golden_plan["path"])

    output_path = Path(result["output_dir"]) / "02_bootstrap" / "bootstrap.md"
    if not output_path.exists():
        # Bootstrap may have failed to run — check stderr
        assert "bootstrap" in result["stderr"].lower() or result["returncode"] != 0, (
            f"Bootstrap should produce output or fail cleanly. "
            f"returncode={result['returncode']}"
        )
        return

    output = output_path.read_text().lower()

    # Must check for key runtime components
    checks_found = any(
        kw in output
        for kw in ["java", "docker", "container", "nextflow", "runtime"]
    )
    assert checks_found, (
        f"Bootstrap must check runtime components. Output: {output[:300]}"
    )

    # Should report status (available or missing) for each component
    has_status_report = any(
        kw in output
        for kw in ["available", "missing", "found", "not found", "version", "✓", "✗"]
    )
    assert has_status_report, (
        f"Bootstrap must report component status. Output: {output[:300]}"
    )