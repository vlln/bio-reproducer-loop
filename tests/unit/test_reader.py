"""L1: Reader Phase — 验证 Reader Agent 的业务逻辑正确性。

需要: 真实 LLM 调用, bench-001 论文包, golden_plan.md fixture.
"""


def test_reader_completes_with_valid_pdf(bench_001):
    """AC-0001-N-1: 给定有效 PDF, Reader 产出 status=completed, tool list 与 golden 一致."""
    pass  # TODO: 实现 — 需要 loopflow Python API 调用 Reader agent


def test_reader_blocks_on_missing_pdf():
    """AC-0001-B-1: PDF 路径不存在, Reader 产出 status=blocked."""
    pass


def test_reader_stability(bench_001):
    """AC-0001-N-3: 同一输入跑 5 次, 关键决策点一致."""
    pass