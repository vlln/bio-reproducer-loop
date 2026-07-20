import json
from pathlib import Path

import yaml

from evals.runner.config import (
    CASES_DIR,
    EVALS_DIR,
    load_cases,
    profile_runs,
    write_evaluation_result,
)


ROOT = Path(__file__).parents[2]


def test_eval_profiles_control_sampling_counts():
    assert profile_runs("smoke") == 1
    assert profile_runs("regression") == 3
    assert profile_runs("release") == 5


def test_eval_cases_reference_existing_inputs_and_fixtures():
    cases = load_cases()

    assert len(cases) == 14
    for case_id, case in cases.items():
        assert case["id"] == case_id
        assert case["level"] in {"L1", "L2"}
        assert case["capabilities"]
        entry_input = ROOT / "benchmarks" / "entries" / case["input"]["benchmark"] / "input"
        assert entry_input.is_dir(), case_id
        for declaration in case.get("upstream", {}).values():
            if isinstance(declaration, dict):
                source = entry_input / declaration["input"]
            else:
                source = EVALS_DIR / "fixtures" / declaration
            assert source.is_file(), (case_id, declaration)


def test_coverage_references_known_cases_and_capabilities():
    cases = load_cases()
    coverage = yaml.safe_load((EVALS_DIR / "coverage.yaml").read_text())

    covered_cases = set()
    for capability, declaration in coverage["capabilities"].items():
        for case_id in declaration["cases"]:
            assert case_id in cases, (capability, case_id)
            assert capability in cases[case_id]["capabilities"]
            covered_cases.add(case_id)
    assert covered_cases == set(cases)


def test_eval_code_does_not_hardcode_repeat_ranges():
    sources = [
        *sorted((EVALS_DIR / "component").glob("test_*.py")),
        *sorted((EVALS_DIR / "handoff").glob("test_*.py")),
    ]

    assert sources
    for path in sources:
        content = path.read_text()
        assert "parametrize" not in content
        assert "range(" not in content


def test_eval_results_record_profile_environment_and_distribution(tmp_path, monkeypatch):
    monkeypatch.setenv("BIO_REPRODUCER_MODEL", "model-test")
    monkeypatch.setenv("BIO_REPRODUCER_PROMPT_VERSION", "prompt-test")
    outcomes = [
        {"case_id": "reader-basic-de", "run": 1, "outcome": "passed"},
        {"case_id": "reader-basic-de", "run": 2, "outcome": "failed"},
    ]

    path = write_evaluation_result(tmp_path, "regression", outcomes)
    result = json.loads(path.read_text())

    assert result["profile"] == "regression"
    assert result["system"]["model"] == "model-test"
    assert result["system"]["prompt_version"] == "prompt-test"
    assert result["cases"]["reader-basic-de"] == {
        "attempts": 2,
        "passed": 1,
        "failed": 1,
        "pass_rate": 0.5,
    }
    assert result["attempts"] == outcomes


def test_no_multi_purpose_exemplar_directory_remains():
    assert not (EVALS_DIR / "exemplars").exists()
    assert len(list(CASES_DIR.glob("**/case.yaml"))) == 14


def test_internal_eval_schemas_are_valid_json():
    schemas = sorted((EVALS_DIR / "schemas").glob("*.json"))

    assert {path.name for path in schemas} == {"case.schema.json", "result.schema.json"}
    for path in schemas:
        schema = json.loads(path.read_text())
        assert schema["$schema"].endswith("2020-12/schema")
        assert schema["required"]
