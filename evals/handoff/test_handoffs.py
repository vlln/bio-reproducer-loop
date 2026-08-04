"""Capability-oriented real-LLM evaluations for degraded upstream states."""

from pathlib import Path

import pytest

from evals.runner.loopflow import assert_text_checks, run_phase


def _evaluate_handoff(case: dict, output_dir: Path):
    result = run_phase(case, output_dir)
    assert result.returncode == 0, result.stderr[:500]
    output_path = output_dir / case["output"]
    assert output_path.is_file(), f"Phase produced no {case['output']}"
    assert_text_checks(output_path.read_text(), case["checks"])


@pytest.mark.eval_case("handoff-blocked-plan")
def test_blocked_plan_stops_data_phase(case, eval_run, tmp_path):
    _evaluate_handoff(case, tmp_path / "repro-data")


@pytest.mark.eval_case("handoff-failed-provision")
def test_failed_provision_prevents_successful_run(case, eval_run, tmp_path):
    _evaluate_handoff(case, tmp_path / "repro-data")
