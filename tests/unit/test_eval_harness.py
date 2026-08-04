import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

from evals.runner.loopflow import assert_text_checks


ROOT = Path(__file__).parents[2]


def _workflow_bytecode_state():
    cache = ROOT / "loops" / "bio-reproducer" / "__pycache__"
    if not cache.exists():
        return {}
    return {
        path.name: (path.stat().st_size, path.stat().st_mtime_ns)
        for path in cache.iterdir()
        if path.is_file()
    }


def _load_workflow_module():
    path = ROOT / "loops" / "bio-reproducer" / "workflow.py"
    spec = importlib.util.spec_from_file_location("bio_reproducer_workflow", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def test_text_checks_accept_yaml_scalar_values():
    assert_text_checks("Recovered 11 rows and 8 columns", {"contains": [11, 8]})


def test_validation_verdict_falls_back_to_metrics_for_phase_resume(tmp_path):
    metrics = tmp_path / "06_validate" / "metrics.json"
    metrics.parent.mkdir()
    metrics.write_text('{"verdict": "REPRODUCED"}')

    bytecode_before = _workflow_bytecode_state()
    workflow = _load_workflow_module()

    assert workflow._validation_verdict(SimpleNamespace(value=None), tmp_path) == "REPRODUCED"
    assert _workflow_bytecode_state() == bytecode_before


def _run_phase_with_capture(monkeypatch, case, output_dir):
    import subprocess

    from evals.runner import loopflow as runner

    captured = {}

    def fake_run(command, capture_output, text):
        captured["command"] = command
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = runner.run_phase(case, output_dir)
    assert result.returncode == 0
    return captured["command"]


def test_run_phase_uses_loopflow_single_agent_mode(monkeypatch, tmp_path):
    """BL-001 修复：eval harness 不再使用已删除的 --only-phase。"""
    case = {
        "id": "reader-basic-de",
        "phase": "Reader",
        "input": {"benchmark": "bench-001"},
        "output": "01_plan/plan.md",
        "checks": {"min_chars": 100},
    }
    output_dir = tmp_path / "repro-data"
    command = _run_phase_with_capture(monkeypatch, case, output_dir)

    assert command[:2] == ["loop", "run"]
    assert "--only-phase" not in command
    assert "--from-phase" not in command

    agent_at = command.index("--agent")
    assert command[agent_at + 1] == "reader"
    work_at = command.index("--work-dir")
    assert Path(command[work_at + 1]) == output_dir
    params = [command[i + 1] for i, value in enumerate(command) if value == "--param"]
    assert any(param.startswith("language=") for param in params)
    assert any(param.startswith("consent=ask") for param in params)
    assert any(param.startswith("paper_path=") for param in params)
    paper_path = next(p for p in params if p.startswith("paper_path="))
    assert Path(paper_path.split("=", 1)[1]).is_file()


def test_run_phase_rejects_unknown_phase():
    from evals.runner.loopflow import phase_spec

    try:
        phase_spec("NotAPhase")
    except KeyError as error:
        assert "NotAPhase" in str(error)
    else:
        raise AssertionError("phase_spec must reject unknown phases")
