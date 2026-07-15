"""Shared test fixtures for L1 and L2 tests.

Uses loopflow to run individual Phase agents with real LLM calls.
"""

import pytest
import json
from pathlib import Path


BENCHMARKS_DIR = Path(__file__).parent.parent / "benchmarks" / "entries"
LOOP_DIR = Path(__file__).parent.parent / "loops" / "bio-reproducer"


def load_golden(bench_id: str, phase: str) -> dict:
    """Load the golden fixture for a specific benchmark and phase."""
    golden_path = BENCHMARKS_DIR / bench_id / "golden" / f"{phase}.md"
    if not golden_path.exists():
        pytest.skip(f"Golden fixture not found: {golden_path}")
    return {"path": str(golden_path), "content": golden_path.read_text()}


def load_expected(bench_id: str) -> dict:
    """Load expected.yaml for a benchmark entry."""
    import yaml
    expected_path = BENCHMARKS_DIR / bench_id / "expected.yaml"
    if not expected_path.exists():
        pytest.skip(f"Expected file not found: {expected_path}")
    with open(expected_path) as f:
        return yaml.safe_load(f)


@pytest.fixture
def bench_001():
    """Fixture for bench-001 (basic figure reproduction)."""
    return {
        "id": "bench-001",
        "paper_pdf": str(BENCHMARKS_DIR / "bench-001" / "paper.pdf"),
        "data_dir": str(BENCHMARKS_DIR / "bench-001" / "data"),
        "expected": load_expected("bench-001"),
    }


@pytest.fixture
def golden_plan():
    """Golden Reader output for bench-001."""
    return load_golden("bench-001", "plan")


@pytest.fixture
def golden_provision():
    """Golden Provision output for bench-001."""
    return load_golden("bench-001", "provision")