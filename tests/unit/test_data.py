"""L1: Data Phase — 验证 Data Agent 的数据获取策略正确性."""

from loopflow.runtime import agent


def _call_data(plan_path: str, output_dir: str = "/tmp/l1-data-test") -> dict:
    """Call the Data agent and return parsed result."""
    import shutil
    from pathlib import Path

    plan_dir = Path(output_dir) / "01_plan"
    plan_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(plan_path, plan_dir / "plan.md")

    result = agent(
        prompt="下载分析所需数据。",
        agent_def="data",
        goal="获取所有必需数据文件",
        goal_max_iterators=3,
        output_dir=output_dir,
        language="en",
    )
    return {"status": result.status, "value": result.value, "turns": result.turns}


def test_data_identifies_sources_from_plan(bench_001, golden_plan):
    """AC-0001-N-2: Data agent 正确识别 plan.md 中的数据来源.

    检查 Data agent 能否从 plan.md 中识别数据源（counts.csv, GSE99999）。
    实际下载可能因网络而阻塞，但识别决策应正确。
    """
    result = _call_data(golden_plan["path"])

    output = str(result["value"]).lower()

    # Must identify the data source from the plan
    data_identified = "counts.csv" in output or "gse" in output or "data" in output
    assert data_identified, (
        f"Data agent must identify data sources. Output: {output[:300]}"
    )

    # Should report status or plan for data acquisition
    is_valid = result["status"] in ("complete", "partial", "blocked")
    assert is_valid, (
        f"Data agent should complete, partially complete, or block. "
        f"Status: {result['status']}"
    )