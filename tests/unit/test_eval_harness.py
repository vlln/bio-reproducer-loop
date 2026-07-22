import importlib.util
from pathlib import Path
from types import SimpleNamespace

from evals.runner.loopflow import assert_text_checks


ROOT = Path(__file__).parents[2]


def _load_workflow_module():
    path = ROOT / "loops" / "bio-reproducer" / "workflow.py"
    spec = importlib.util.spec_from_file_location("bio_reproducer_workflow", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_text_checks_accept_yaml_scalar_values():
    assert_text_checks("Recovered 11 rows and 8 columns", {"contains": [11, 8]})


def test_validation_verdict_falls_back_to_metrics_for_phase_resume(tmp_path):
    metrics = tmp_path / "06_validate" / "metrics.json"
    metrics.parent.mkdir()
    metrics.write_text('{"verdict": "REPRODUCED"}')

    workflow = _load_workflow_module()

    assert workflow._validation_verdict(SimpleNamespace(value=None), tmp_path) == "REPRODUCED"
