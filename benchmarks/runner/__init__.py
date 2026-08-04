"""Benchmark runner: execution, independent evaluation, and reporting."""

from pathlib import Path
from . import independent_evaluator, reporter, runner

BENCHMARKS_DIR = Path(__file__).parent.parent / "entries"
