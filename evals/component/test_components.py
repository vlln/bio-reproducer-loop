"""Capability-oriented real-LLM evaluations for individual phases."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.runner.loopflow import assert_text_checks, run_phase


def _evaluate_text_case(case: dict, output_dir: Path):
    result = run_phase(case, output_dir)
    assert result.returncode == 0, result.stderr[:500]
    output_path = output_dir / case["output"]
    assert output_path.is_file(), f"Phase produced no {case['output']}"
    assert_text_checks(output_path.read_text(), case["checks"])


def _evaluate_provision_case(case: dict, output_dir: Path):
    result = run_phase(case, output_dir)
    output_path = output_dir / case["output"]
    assert output_path.is_file(), f"Phase produced no {case['output']}"
    assert_text_checks(output_path.read_text(), case["checks"])
    assert result.returncode == 0 or output_path.stat().st_size > 50


@pytest.mark.eval_case("reader-basic-de")
def test_reader_basic_de(case, eval_run, tmp_path):
    _evaluate_text_case(case, tmp_path / "repro-data")


@pytest.mark.eval_case("reader-missing-paper")
def test_reader_missing_paper(case, eval_run, tmp_path):
    output_dir = tmp_path / "repro-data"
    result = run_phase(case, output_dir)
    plan = output_dir / "01_plan" / "plan.md"
    content = plan.read_text().lower() if plan.is_file() else ""
    assert result.returncode != 0 or "blocked" in content


@pytest.mark.eval_case("bootstrap-runtime-detection")
def test_bootstrap_runtime_detection(case, eval_run, tmp_path):
    _evaluate_text_case(case, tmp_path / "repro-data")


@pytest.mark.eval_case("provision-standard-de")
def test_provision_standard_de(case, eval_run, tmp_path):
    _evaluate_provision_case(case, tmp_path / "repro-data")


@pytest.mark.eval_case("provision-multi-language")
def test_provision_multi_language(case, eval_run, tmp_path):
    _evaluate_provision_case(case, tmp_path / "repro-data")


@pytest.mark.eval_case("data-local-counts")
def test_data_local_counts(case, eval_run, tmp_path):
    _evaluate_text_case(case, tmp_path / "repro-data")


@pytest.mark.eval_case("run-single-contrast")
def test_run_single_contrast(case, eval_run, tmp_path):
    _evaluate_text_case(case, tmp_path / "repro-data")


@pytest.mark.eval_case("run-multi-contrast")
def test_run_multi_contrast(case, eval_run, tmp_path):
    output_dir = tmp_path / "repro-data"
    _evaluate_text_case(case, output_dir)
    results_dir = output_dir / "05_run" / "results"
    tables = list(results_dir.rglob("*.csv")) + list(results_dir.rglob("*.tsv"))
    assert len(tables) >= case["checks"]["min_result_tables"], (
        f"Expected at least {case['checks']['min_result_tables']} result tables, found {len(tables)}"
    )


@pytest.mark.eval_case("validate-complete-result")
def test_validate_complete_result(case, eval_run, tmp_path):
    output_dir = tmp_path / "repro-data"
    _evaluate_text_case(case, output_dir)
    metrics_path = output_dir / case["checks"]["json_output"]
    assert metrics_path.is_file(), f"Phase produced no {metrics_path.name}"
    metrics = json.loads(metrics_path.read_text())
    missing = [field for field in case["checks"]["json_fields"] if field not in metrics]
    assert not missing, f"Missing JSON fields: {missing}"


@pytest.mark.eval_case("data-corrupted-input")
def test_data_corrupted_input(case, eval_run, tmp_path):
    _evaluate_text_case(case, tmp_path / "repro-data")


@pytest.mark.eval_case("validate-missing-result-table")
def test_validate_missing_result_table(case, eval_run, tmp_path):
    _evaluate_text_case(case, tmp_path / "repro-data")


@pytest.mark.eval_case("package-standard")
def test_package_standard(case, eval_run, tmp_path):
    output_dir = tmp_path / "repro-data"
    result = run_phase(case, output_dir)
    assert result.returncode == 0, result.stderr[:500]
    for relative in case["checks"]["files"]:
        assert (output_dir / relative).is_file(), f"Package produced no {relative}"
    for relative, values in case["checks"].get("contains", {}).items():
        content = (output_dir / relative).read_text().lower()
        missing = [value for value in values if value.lower() not in content]
        assert not missing, f"{relative} missing expected content: {missing}"
