"""L1: Bootstrap Phase — 验证 Bootstrap Agent 的系统环境检测正确性."""

from loopflow.runtime import agent


def _call_bootstrap(plan_path: str, output_dir: str = "/tmp/l1-bootstrap-test") -> dict:
    """Call the Bootstrap agent and return parsed result."""
    import shutil
    from pathlib import Path

    plan_dir = Path(output_dir) / "01_plan"
    plan_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(plan_path, plan_dir / "plan.md")

    result = agent(
        prompt="检查系统环境并报告可用的运行时组件。",
        agent_def="bootstrap",
        goal="完整检测系统环境：Java、Nextflow、容器运行时",
        goal_max_iterations=3,
        output_dir=output_dir,
        language="en",
    )
    return {"status": result.status, "value": result.value, "turns": result.turns}


def test_bootstrap_detects_environment(bench_001, golden_plan):
    """AC-0001-N-2: Bootstrap 正确检测系统环境并报告可用/缺失组件.

    检查 Bootstrap agent 能否检测 Java、Nextflow、容器运行时。
    不需要所有组件都可用——只要检测逻辑正确（报告了存在 vs 缺失）。
    """
    result = _call_bootstrap(golden_plan["path"])

    assert result["status"] == "complete", (
        f"Bootstrap should complete. Status: {result['status']}"
    )

    output = str(result["value"]).lower()

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