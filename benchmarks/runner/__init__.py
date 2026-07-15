"""Benchmark runner — 论文包执行、结果采集、期望对比、报告生成."""

from pathlib import Path
from . import runner, evaluator, reporter

BENCHMARKS_DIR = Path(__file__).parent.parent / "entries"