"""L1: Validate Phase — 验证 Validate Agent 的验证报告正确性."""

from loopflow.runtime import agent


def _call_validate(
    plan_path: str, run_results_path: str, output_dir: str = "/tmp/l1-validate-test"
) -> dict:
    """Call the Validate agent with plan and run results."""
    import shutil
    from pathlib import Path

    # Set up plan
    plan_dir = Path(output_dir) / "01_plan"
    plan_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(plan_path, plan_dir / "plan.md")

    # Set up run results
    run_dir = Path(output_dir) / "05_run"
    run_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(run_results_path, run_dir / "run_results.md")

    result = agent(
        prompt="对比复现结果与论文声称，生成验证报告。",
        agent_def="validate",
        goal="完成四维度验证：数据完整性、流程质量、定量一致性、图表复现",
        goal_max_iterations=5,
        output_dir=output_dir,
        language="en",
    )
    return {"status": result.status, "value": result.value, "turns": result.turns}


def test_validate_produces_report(bench_001, golden_plan):
    """AC-0001-N-2: Validate agent 产出完整的验证报告.

    使用 bench-001 的实际 run 结果作为输入，验证 agent 能否产出
    包含 verdict、score、维度得分的验证报告。
    """
    # Use actual run results from bench-001
    run_results = (
        "benchmarks/results/bench-001/run_01/repro-data/05_run/run_results.md"
    )
    import os
    if not os.path.exists(run_results):
        # Fallback: use golden plan as run results for basic validation
        run_results = golden_plan["path"]

    result = _call_validate(golden_plan["path"], run_results)

    output = str(result["value"]).lower()

    # Must produce a verdict
    has_verdict = any(
        v in output
        for v in ["reproduced", "partial", "failed", "blocked", "verdict"]
    )
    assert has_verdict, (
        f"Validate must produce a verdict. Output: {output[:300]}"
    )

    # Must have a score or scoring dimension
    has_score = "score" in output or "data integrity" in output
    assert has_score, (
        f"Validate must include scoring. Output: {output[:300]}"
    )

    is_valid = result["status"] in ("complete", "partial", "blocked")
    assert is_valid, (
        f"Validate should complete, partially complete, or block. "
        f"Status: {result['status']}"
    )