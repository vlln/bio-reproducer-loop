"""L1: Reader Phase — 验证 Reader Agent 的业务逻辑正确性。

需要: 真实 LLM 调用, bench-001 论文包, golden_plan.md fixture.
"""

from loopflow.runtime import agent


def _call_reader(paper_path: str, language: str = "en") -> dict:
    """Call the Reader agent and return parsed result."""
    result = agent(
        prompt=(
            f"Read the paper at {paper_path}. "
            "Your ONLY task is to extract information from THIS paper. "
            "Do NOT look at other papers or benchmark entries. "
            "Focus exclusively on the paper content at the given path."
        ),
        agent_def="reader",
        goal="Extract paper claims from the specified paper only",
        goal_max_iterations=3,
        paper_path=paper_path,
        language=language,
        output_dir="/tmp/l1-reader-test",
    )
    return {"status": result.status, "value": result.value, "turns": result.turns}


def test_reader_completes_with_valid_paper(bench_001):
    """AC-0001-N-1: 给定有效论文, Reader 产出 status=completed,
    关键字段 (tool list, gene list, data source) 正确提取."""
    result = _call_reader(bench_001["paper_path"])

    assert result["status"] == "complete", (
        f"Expected status=complete, got {result['status']}"
    )

    output = result["value"]
    assert isinstance(output, str) and len(output) > 100, (
        f"Reader output should be non-trivial markdown, got {len(output)} chars"
    )

    # Check that the output contains the paper's key claims
    # Use case-insensitive search for robustness
    lower = output.lower()

    # Must identify the analysis method
    assert "deseq2" in lower or "differential expression" in lower, (
        "Reader must identify differential expression analysis"
    )

    # Must identify the key genes
    assert "gene_a" in lower, "Reader must identify Gene_A"
    assert "gene_b" in lower, "Reader must identify Gene_B"

    # Must identify the data source
    assert "counts.csv" in lower or "count matrix" in lower, (
        "Reader must identify the count matrix data source"
    )

    # Must have a structured output with sections
    assert ("## " in output or "**" in output or "plan" in lower), (
        "Reader output should have some structure"
    )

    # Must identify the reproduction target
    assert "volcano" in lower or "figure" in lower, (
        "Reader must identify the figure reproduction target"
    )


def test_reader_blocks_on_missing_paper():
    """AC-0001-B-1: 论文路径不存在, Reader 应报告阻塞或失败."""
    result = _call_reader("/nonexistent/path/paper.pdf")

    output = result["value"].lower()
    # Agent should report the file is missing — either via status or message
    is_blocked = (
        result["status"] in ("blocked", "failed")
        or "blocked" in output
        or "不存在" in output
        or "does not exist" in output
        or "not found" in output
    )
    assert is_blocked, (
        f"Reader should report blocked/failed for missing paper. "
        f"Status: {result['status']}, Output: {result['value'][:200]}"
    )


def test_reader_stability(bench_001):
    """AC-0001-N-3: 同一输入跑 3 次, 关键决策点一致."""
    paper_path = bench_001["paper_path"]
    results = []

    for i in range(3):
        r = _call_reader(paper_path)
        results.append(r)
        assert r["status"] == "complete", f"Run {i}: expected complete, got {r['status']}"

    # All runs should produce non-trivial output
    for i, r in enumerate(results):
        assert len(r["value"]) > 100, f"Run {i}: output too short ({len(r['value'])} chars)"

    # Key genes should be identified in all runs (the most stable check)
    for i, r in enumerate(results):
        lower = r["value"].lower()
        assert "gene_a" in lower, f"Run {i}: must identify Gene_A"
        assert "gene_b" in lower, f"Run {i}: must identify Gene_B"