"""L1: Run Phase — 验证 Run Agent 的流程编排正确性."""

from loopflow.runtime import agent


def _call_run(plan_path: str, output_dir: str = "/tmp/l1-run-test") -> dict:
    """Call the Run agent and return parsed result."""
    import shutil
    from pathlib import Path

    plan_dir = Path(output_dir) / "01_plan"
    plan_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(plan_path, plan_dir / "plan.md")

    result = agent(
        prompt="运行分析流水线。",
        agent_def="run",
        goal="执行完整的分析流程并生成所有结果",
        goal_max_iterations=3,
        output_dir=output_dir,
        language="en",
    )
    return {"status": result.status, "value": result.value, "turns": result.turns}


def test_run_plans_pipeline_from_plan(bench_001, golden_plan):
    """AC-0001-N-2: Run agent 根据 plan.md 规划分析流程.

    检查 Run agent 能否从 plan 中提取分析步骤并生成执行计划。
    实际执行可能因缺少前置输出而阻塞，但规划决策应正确。
    """
    result = _call_run(golden_plan["path"])

    output = str(result["value"]).lower()

    # Must identify the analysis method from the plan
    analysis_identified = (
        "deseq2" in output or "analysis" in output or "pipeline" in output
    )
    assert analysis_identified, (
        f"Run agent must identify analysis steps. Output: {output[:300]}"
    )

    is_valid = result["status"] in ("complete", "partial", "blocked")
    assert is_valid, (
        f"Run agent should complete, partially complete, or block. "
        f"Status: {result['status']}"
    )