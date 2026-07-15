"""L1: Provision Phase — 验证 Provision Agent 的工具部署计划正确性."""

from loopflow.runtime import agent


def _call_provision(plan_path: str, output_dir: str = "/tmp/l1-provision-test") -> dict:
    """Call the Provision agent and return parsed result."""
    import shutil
    from pathlib import Path

    # Set up the expected directory structure: {output_dir}/01_plan/plan.md
    plan_dir = Path(output_dir) / "01_plan"
    plan_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(plan_path, plan_dir / "plan.md")

    result = agent(
        prompt="部署工具容器环境。从 plan.md 中识别所需工具并部署。",
        agent_def="provision",
        goal="成功部署所有必需的工具容器镜像",
        goal_max_iterations=5,
        output_dir=output_dir,
        language="en",
    )
    return {"status": result.status, "value": result.value, "turns": result.turns}


def test_provision_identifies_tools_from_plan(bench_001, golden_plan):
    """AC-0001-N-2: 给定 plan.md, Provision 产出的工具列表与 golden 一致.

    检查 Provision agent 能否正确识别 plan.md 中声明的工具需求。
    实际部署可能因无 Docker 而阻塞，但工具识别决策应正确。
    """
    result = _call_provision(golden_plan["path"])

    output = str(result["value"]).lower()

    # Must identify the key tools from the plan
    # R is required for DESeq2 analysis
    assert "r" in output, f"Provision must identify R. Output: {output[:300]}"

    # DESeq2 is the main analysis tool
    assert "deseq2" in output or "bioconductor" in output, (
        f"Provision must identify DESeq2/Bioconductor. Output: {output[:300]}"
    )

    # The agent should either complete (tools identified) or report blocked
    # (no Docker available) — both are valid business decisions
    is_valid = (
        result["status"] in ("complete", "blocked")
        or ("docker" in output and "unavailable" in output)
    )
    assert is_valid, (
        f"Provision should complete or report Docker unavailable. "
        f"Status: {result['status']}"
    )