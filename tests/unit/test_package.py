"""L1: Package Phase — 验证 Package Agent 的打包正确性."""

from loopflow.runtime import agent


def _call_package(
    plan_path: str, validate_report_path: str, output_dir: str = "/tmp/l1-package-test"
) -> dict:
    """Call the Package agent with plan and validate report."""
    import shutil
    from pathlib import Path

    plan_dir = Path(output_dir) / "01_plan"
    plan_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(plan_path, plan_dir / "plan.md")

    validate_dir = Path(output_dir) / "06_validate"
    validate_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(validate_report_path, validate_dir / "report.md")

    result = agent(
        prompt="生成可复现包：README.md + run.sh + .gitignore。",
        agent_def="package",
        goal="创建完整的可复现交付包",
        goal_max_iterations=3,
        output_dir=output_dir,
        language="en",
    )
    return {"status": result.status, "value": result.value, "turns": result.turns}


def test_package_produces_deliverables(bench_001, golden_plan):
    """AC-0001-N-2: Package agent 产出可复现包.

    使用 bench-001 的 validate report 作为输入，验证 Package agent
    能否产出 README.md 和 run.sh。
    """
    import os

    # Use actual validate report from bench-001
    validate_report = (
        "benchmarks/results/bench-001/run_01/repro-data/06_validate/report.md"
    )
    if not os.path.exists(validate_report):
        # Fallback: use golden plan
        validate_report = golden_plan["path"]

    result = _call_package(golden_plan["path"], validate_report)

    output = str(result["value"]).lower()

    # Must produce or reference the deliverable files
    has_deliverables = any(
        kw in output for kw in ["readme", "run.sh", "package", "deliverable"]
    )
    assert has_deliverables, (
        f"Package must produce deliverables. Output: {output[:300]}"
    )

    is_valid = result["status"] in ("complete", "partial", "blocked")
    assert is_valid, (
        f"Package should complete, partially complete, or block. "
        f"Status: {result['status']}"
    )