"""bio-reproducer workflow.py 的确定性 smoke 测试（fake agent，无 LLM）。

覆盖：
- 前置产物 fail-fast（幻觉完成的 phase 没写文件时立即停止）
- confirm_plan 确认门（继续/终止/无人值守跳过）
- Package 的 verdict 门控
"""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

WORKFLOW_PATH = Path(__file__).parents[2] / "loops" / "bio-reproducer" / "workflow.py"

spec = importlib.util.spec_from_file_location("bio_reproducer_workflow", WORKFLOW_PATH)
wf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wf)

ALL_PHASES = ["Reader", "Bootstrap", "Provision", "Data", "Run", "Validate", "Package"]
REQUIRED_FILES = [
    "01_plan/plan.md",
    "03_provision/provision.md",
    "04_data/data_manifest.md",
    "05_run/run_results.md",
    "06_validate/report.md",
]


def make_result(status="complete", verdict="REPRODUCED", reason=""):
    value = {"payload": {"verdict": verdict}} if verdict is not None else None
    return SimpleNamespace(status=status, reason=reason, value=value, turns=1, tokens=100)


class FakeAgent:
    def __init__(self, results=None):
        self.calls = []
        self.results = results or {}

    def __call__(self, prompt, **kwargs):
        label = kwargs.get("label")
        self.calls.append(label)
        return self.results.get(label, make_result())


class FakeIntervene:
    def __init__(self, answer="继续"):
        self.answer = answer
        self.calls = []

    def __call__(self, key, prompt, schema=None, *, options=None, allow_custom=True):
        self.calls.append(key)
        return self.answer


def write_files(base, *paths):
    for rel in paths:
        p = Path(base) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x")


def run_workflow(tmp_path, agent, intervene, args=None):
    logs = []
    base_args = {"paper_path": "paper.pdf"}
    base_args.update(args or {})
    import os
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = wf.run(
            agent, None, None, logs.append, base_args, None, intervene, None
        )
    finally:
        os.chdir(old_cwd)
    return result, logs


def test_happy_path(tmp_path):
    write_files(tmp_path, *REQUIRED_FILES)
    agent, intervene = FakeAgent(), FakeIntervene()
    result, _ = run_workflow(tmp_path, agent, intervene)
    assert agent.calls == ALL_PHASES
    assert intervene.calls == ["confirm-plan"]
    assert result["payload"]["verdict"] == "REPRODUCED"


def test_reader_hallucination_fail_fast(tmp_path):
    # Reader 返回 complete 但没写 plan.md → 停在确认门之前
    agent, intervene = FakeAgent(), FakeIntervene()
    result, logs = run_workflow(tmp_path, agent, intervene)
    assert agent.calls == ["Reader"]
    assert intervene.calls == []
    assert result is None
    assert any("前置产物缺失" in line and "plan.md" in line for line in logs)


def test_confirm_plan_abort(tmp_path):
    write_files(tmp_path, "01_plan/plan.md")
    agent, intervene = FakeAgent(), FakeIntervene(answer="终止")
    result, logs = run_workflow(tmp_path, agent, intervene)
    assert agent.calls == ["Reader"]
    assert result is None
    assert any("用户终止" in line for line in logs)


def test_confirm_plan_false_skips_intervene(tmp_path):
    write_files(tmp_path, *REQUIRED_FILES)
    agent, intervene = FakeAgent(), FakeIntervene()
    result, _ = run_workflow(tmp_path, agent, intervene, {"confirm_plan": False})
    assert intervene.calls == []
    assert agent.calls == ALL_PHASES


def test_failed_verdict_skips_package(tmp_path):
    write_files(tmp_path, *REQUIRED_FILES)
    agent = FakeAgent(results={"Validate": make_result(verdict="FAILED")})
    result, logs = run_workflow(tmp_path, agent, FakeIntervene())
    assert "Package" not in agent.calls
    assert any("跳过 Package" in line for line in logs)
    assert result["payload"]["verdict"] == "FAILED"


def test_missing_data_manifest_stops_before_run(tmp_path):
    write_files(tmp_path, "01_plan/plan.md", "03_provision/provision.md")
    agent, intervene = FakeAgent(), FakeIntervene()
    result, logs = run_workflow(tmp_path, agent, intervene)
    assert agent.calls == ["Reader", "Bootstrap", "Provision", "Data"]
    assert result is None
    assert any("data_manifest.md" in line for line in logs)


def test_phase_failure_returns_none(tmp_path):
    write_files(tmp_path, *REQUIRED_FILES)
    agent = FakeAgent(results={"Provision": make_result(status="blocked", verdict=None, reason="docker missing")})
    result, logs = run_workflow(tmp_path, agent, FakeIntervene())
    assert agent.calls == ["Reader", "Bootstrap", "Provision"]
    assert result is None
    assert any("docker missing" in line for line in logs)


def test_phases_registry_is_complete_and_consistent():
    """PHASES 注册表：完整覆盖全部 phase，且 agent_def 对应 agents/ 下真实定义。"""
    agents_dir = WORKFLOW_PATH.parent / "agents"
    agent_defs = {
        path.stem for path in agents_dir.glob("*.md") if not path.stem.startswith("_")
    }
    assert set(wf.PHASES) == set(ALL_PHASES)
    for name, spec in wf.PHASES.items():
        assert spec["label"] == name
        assert spec["agent_def"] in agent_defs, f"{name} -> {spec['agent_def']}"
        assert spec["prompt"].strip()
        assert spec["goal"].strip()
        assert spec["goal_max_iterations"] > 0


def test_phases_registry_drives_agent_calls(tmp_path):
    """workflow 的 agent 调用完全由 PHASES 注册表驱动（单一事实来源）。"""
    write_files(tmp_path, *REQUIRED_FILES)
    agent, intervene = FakeAgent(), FakeIntervene()
    result, _ = run_workflow(tmp_path, agent, intervene)
    assert agent.calls == list(wf.PHASES)
    assert result["payload"]["verdict"] == "REPRODUCED"
