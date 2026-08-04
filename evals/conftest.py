"""Pytest transport for real-LLM component and handoff evaluations."""

from __future__ import annotations

from pathlib import Path

import pytest

from evals.runner.config import load_case, profile_runs, write_evaluation_result


OUTCOMES: list[dict] = []


def pytest_addoption(parser):
    group = parser.getgroup("internal eval")
    group.addoption(
        "--eval-profile",
        default="smoke",
        help="Evaluation sampling profile from evals/profiles.yaml",
    )
    group.addoption(
        "--eval-results-dir",
        default="evals/results",
        help="Directory for raw internal evaluation results",
    )
    group.addoption(
        "--no-eval-results",
        action="store_true",
        help="Do not write an evaluation result file",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "eval_case(id): internal evaluation case id")


def pytest_generate_tests(metafunc):
    if "eval_run" not in metafunc.fixturenames:
        return
    profile = metafunc.config.getoption("--eval-profile")
    runs = profile_runs(profile)
    metafunc.parametrize("eval_run", range(1, runs + 1), ids=lambda value: f"run-{value:02d}")


def pytest_collection_modifyitems(items):
    for item in items:
        item.add_marker(pytest.mark.llm)


@pytest.fixture
def case(request) -> dict:
    marker = request.node.get_closest_marker("eval_case")
    if marker is None or not marker.args:
        raise RuntimeError("Real-LLM eval tests must declare @pytest.mark.eval_case")
    return load_case(str(marker.args[0]))


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call":
        return
    marker = item.get_closest_marker("eval_case")
    if marker is None:
        return
    run_number = None
    if hasattr(item, "callspec"):
        run_number = item.callspec.params.get("eval_run")
    OUTCOMES.append({
        "case_id": str(marker.args[0]),
        "run": run_number,
        "outcome": "passed" if report.passed else "failed",
        "duration_seconds": round(report.duration, 3),
        "nodeid": report.nodeid,
    })


def pytest_sessionfinish(session, exitstatus):
    config = session.config
    if config.option.collectonly or config.getoption("--no-eval-results") or not OUTCOMES:
        return
    path = write_evaluation_result(
        Path(config.getoption("--eval-results-dir")),
        config.getoption("--eval-profile"),
        OUTCOMES,
    )
    print(f"\nInternal evaluation written to {path}")
