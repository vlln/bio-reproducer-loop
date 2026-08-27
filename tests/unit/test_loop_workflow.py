"""bio-reproducer workflow.py 的确定性 smoke 测试（fake agent，无 LLM）。

覆盖：
- 前置产物 fail-fast（幻觉完成的 phase 没写文件时立即停止）
- confirm_plan 确认门（继续/终止/无人值守跳过）
- Package 的 verdict 门控
- goal 从 plan.md 派生（BL-016）
- Validate 内部路由回环与预算（ADR-0011 §3，FC-007）
"""
import importlib.util
import json
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


def write_data_evidence(base):
    """04_data 标准格式证据（ADR-0011 §2）：可解析的 sha256sum 输出。"""
    p = Path(base) / "04_data" / "sha256sums.txt"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("0" * 64 + "  sample.fastq.gz\n")


def write_provision_evidence(base):
    """03_provision 标准格式证据（ADR-0011 §2）：docker images --digests 输出。"""
    p = Path(base) / "03_provision" / "digests.txt"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("REPOSITORY  TAG  DIGEST\nbio/x  latest  sha256:" + "a" * 64 + "\n")


def write_run_evidence(base):
    """05_run 标准格式证据（ADR-0011 §2）：结果 CSV + answers。"""
    results = Path(base) / "05_run" / "results"
    results.mkdir(parents=True, exist_ok=True)
    (results / "table1.csv").write_text("a,b\n1,2\n")
    answers = Path(base) / "05_run" / "answers.csv"
    answers.write_text("target_id,value,unit,source_file\nT1,1.63,HR,results/table1.csv\n")


def write_package_evidence(base):
    """07_package 标准格式证据（FC-008）：run.sh + check.log 退出码 0。"""
    root = Path(base)
    (root / "run.sh").write_text("#!/usr/bin/env bash\ncheck() { echo OK; }\n\"${@:-check}\"\n")
    p = root / "07_package" / "check.log"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("=== 检查前置条件 ===\nOK: 前置条件满足\nEXIT=0\n")


def write_full_evidence(base):
    write_files(base, *REQUIRED_FILES)
    write_provision_evidence(base)
    write_data_evidence(base)
    write_run_evidence(base)
    write_package_evidence(base)


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
    write_full_evidence(tmp_path)
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
    write_full_evidence(tmp_path)
    agent, intervene = FakeAgent(), FakeIntervene()
    result, _ = run_workflow(tmp_path, agent, intervene, {"confirm_plan": False})
    assert intervene.calls == []
    assert agent.calls == ALL_PHASES


def test_failed_verdict_skips_package(tmp_path):
    write_full_evidence(tmp_path)
    agent = FakeAgent(results={"Validate": make_result(verdict="FAILED")})
    result, logs = run_workflow(tmp_path, agent, FakeIntervene())
    assert "Package" not in agent.calls
    assert any("跳过 Package" in line for line in logs)
    assert result["payload"]["verdict"] == "FAILED"


def test_missing_data_manifest_stops_before_run(tmp_path):
    write_files(tmp_path, "01_plan/plan.md", "03_provision/provision.md")
    write_provision_evidence(tmp_path)
    write_data_evidence(tmp_path)
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
    write_full_evidence(tmp_path)
    agent, intervene = FakeAgent(), FakeIntervene()
    result, _ = run_workflow(tmp_path, agent, intervene)
    assert agent.calls == list(wf.PHASES)
    assert result["payload"]["verdict"] == "REPRODUCED"


class ScopeCapturingAgent(FakeAgent):
    def __init__(self):
        super().__init__()
        self.kwargs = []

    def __call__(self, prompt, **kwargs):
        self.kwargs.append(kwargs)
        return super().__call__(prompt, **kwargs)


def test_scope_arg_passes_through_to_all_agents(tmp_path):
    write_full_evidence(tmp_path)
    agent, intervene = ScopeCapturingAgent(), FakeIntervene()
    run_workflow(tmp_path, agent, intervene, {"scope": "figures=figure4,figure5"})
    assert len(agent.kwargs) == len(ALL_PHASES)
    assert all(kwargs.get("scope") == "figures=figure4,figure5" for kwargs in agent.kwargs)


def test_scope_defaults_to_empty(tmp_path):
    write_full_evidence(tmp_path)
    agent, intervene = ScopeCapturingAgent(), FakeIntervene()
    run_workflow(tmp_path, agent, intervene)
    assert len(agent.kwargs) == len(ALL_PHASES)
    assert all(kwargs.get("scope") == "" for kwargs in agent.kwargs)


def test_provision_prompt_contains_reuse_and_skill_rules():
    """provision/_base 必须含镜像复用、技能强制、构建纪律规则（内容无关断言）。"""
    provision = (WORKFLOW_PATH.parent / "agents" / "provision.md").read_text()
    for marker in ("镜像复用", "技能强制使用", "镜像构建纪律", "Image & Reuse Decisions"):
        assert marker in provision, f"provision.md missing: {marker}"
    base = (WORKFLOW_PATH.parent / "agents" / "_base.md").read_text()
    for marker in ("工具与技能纪律", "复用优先"):
        assert marker in base, f"_base.md missing: {marker}"


# ── 单元 03：goal 从 plan.md 派生（BL-016）──────────────────────────────

PLAN_WITH_TARGETS = """# Paper: NHANES lead mortality

## Paper Understanding

### Reproduction Target

| id | target | priority | source |
|----|--------|----------|--------|
| T1 | 血铅与全因死亡率的 Cox HR | high | Table 2 |
| T2 | 胫骨铅 HR | high | Table 2 |

### Data Requirements

| Database | Accession | Samples | Type |
|----------|-----------|---------|------|
| NHANES | nhanes-1999-2018 | 14847 | 流行病学调查数据 |
"""


def test_goal_derived_from_plan_for_data_and_run(tmp_path):
    write_full_evidence(tmp_path)
    (tmp_path / "01_plan" / "plan.md").write_text(PLAN_WITH_TARGETS)
    agent, intervene = ScopeCapturingAgent(), FakeIntervene()
    run_workflow(tmp_path, agent, intervene, {"confirm_plan": False})
    goals = {kw["label"]: kw.get("goal") for kw in agent.kwargs}
    # 派生 goal 必须包含该论文的实际内容，而非 RNA-seq 硬编码
    assert "NHANES" in goals["Data"]  # Data Requirements 段
    assert "血铅" in goals["Run"] and "T1" in goals["Run"]  # Reproduction Target 段
    assert "RNA-Seq" not in goals["Data"] and "RNA-Seq" not in goals["Run"]


def test_goal_falls_back_to_default_without_section(tmp_path):
    write_full_evidence(tmp_path)
    (tmp_path / "01_plan" / "plan.md").write_text("# Paper: X\n\nno targets here\n")
    agent, intervene = ScopeCapturingAgent(), FakeIntervene()
    run_workflow(tmp_path, agent, intervene, {"confirm_plan": False})
    goals = {kw["label"]: kw.get("goal") for kw in agent.kwargs}
    assert goals["Data"] == wf.PHASES["Data"]["goal"]
    assert goals["Run"] == wf.PHASES["Run"]["goal"]


def test_registry_goals_have_no_rnaseq_hardcode():
    """注册表默认 goal 无 RNA-seq/FASTQ 硬编码（BL-016）。"""
    assert "RNA-Seq" not in wf.PHASES["Data"]["goal"]
    assert "RNA-Seq" not in wf.PHASES["Run"]["goal"]
    assert "FASTQ" not in wf.PHASES["Data"]["goal"]


# ── 单元 03：Validate 内部路由回环（ADR-0011 §3，FC-007）────────────────

class RoutingAgent(FakeAgent):
    """Validate 调用时按预定序列写 routing.jsonl（None = 该轮写 route_to=null）。"""

    def __init__(self, routes):
        super().__init__()
        self.routes = list(routes)
        self.validate_calls = 0

    def __call__(self, prompt, **kwargs):
        label = kwargs.get("label")
        if label == "Validate":
            self.validate_calls += 1
            if self.routes:
                route = self.routes.pop(0)
                d = Path("06_validate")
                d.mkdir(exist_ok=True)
                with open(d / "routing.jsonl", "a", encoding="utf-8") as f:
                    f.write(json.dumps(
                        {"ts": "t", "target": "T1", "decision": "deviation" if route else "reproduced",
                         "route_to": route, "reason": "" if route is None else "test"}) + "\n")
        return super().__call__(prompt, **kwargs)


def test_routing_loop_reruns_run_chain(tmp_path):
    """route_to=Run → 重跑 Run+Validate 一次，预算 1 耗尽后线性收尾。"""
    write_full_evidence(tmp_path)
    agent, intervene = RoutingAgent(["Run", None]), FakeIntervene()
    result, logs = run_workflow(tmp_path, agent, intervene, {"confirm_plan": False, "routing_budget": 1})
    assert agent.validate_calls == 2
    # 初始链 + 回环链（Run, Validate）
    assert agent.calls == ["Reader", "Bootstrap", "Provision", "Data", "Run", "Validate",
                           "Run", "Validate", "Package"]
    assert any("路由回 Run" in line for line in logs)
    assert result["payload"]["verdict"] == "REPRODUCED"


def test_routing_loop_routes_to_data(tmp_path):
    write_full_evidence(tmp_path)
    agent, intervene = RoutingAgent(["Data", None]), FakeIntervene()
    result, logs = run_workflow(tmp_path, agent, intervene, {"confirm_plan": False, "routing_budget": 2})
    # 初始链 + 回环链（Data, Run, Validate）
    assert agent.calls == ["Reader", "Bootstrap", "Provision", "Data", "Run", "Validate",
                           "Data", "Run", "Validate", "Package"]
    assert any("路由回 Data" in line for line in logs)
    assert result is not None


def test_routing_budget_zero_is_linear(tmp_path):
    """默认 budget=0（调用方未给）→ 不回环，保持现行为。"""
    write_full_evidence(tmp_path)
    agent, intervene = RoutingAgent(["Run", None]), FakeIntervene()
    result, _ = run_workflow(tmp_path, agent, intervene, {"confirm_plan": False})
    assert agent.validate_calls == 1
    assert agent.calls == ALL_PHASES


def test_routing_budget_exhausted_stops_loop(tmp_path):
    """预算耗尽即终止（FC-007：上限来自调用方，耗尽如实结束）。"""
    write_full_evidence(tmp_path)
    agent, intervene = RoutingAgent(["Run", "Run", "Run", "Run", None]), FakeIntervene()
    result, logs = run_workflow(tmp_path, agent, intervene, {"confirm_plan": False, "routing_budget": 2})
    assert agent.validate_calls == 3  # 初始 + 2 轮回环
    assert agent.calls == ["Reader", "Bootstrap", "Provision", "Data", "Run", "Validate",
                           "Run", "Validate", "Run", "Validate", "Package"]
    assert result is not None


def test_routing_unknown_target_stops_loop(tmp_path):
    write_full_evidence(tmp_path)
    agent, intervene = RoutingAgent(["bogus"]), FakeIntervene()
    result, logs = run_workflow(tmp_path, agent, intervene, {"confirm_plan": False, "routing_budget": 3})
    assert agent.validate_calls == 1
    assert any("路由目标未知" in line for line in logs)
    assert result is not None


def test_routing_reader_chain_skips_confirm(tmp_path):
    """Reader 回环重跑全链，但不重新触发 confirm 门。"""
    write_full_evidence(tmp_path)
    agent, intervene = RoutingAgent(["Reader", None]), FakeIntervene()
    result, _ = run_workflow(tmp_path, agent, intervene, {"confirm_plan": False, "routing_budget": 1})
    assert agent.validate_calls == 2
    assert agent.calls == ["Reader", "Bootstrap", "Provision", "Data", "Run", "Validate",
                           "Reader", "Bootstrap", "Provision", "Data", "Run", "Validate", "Package"]
    assert intervene.calls == []  # confirm_plan=False 全程跳过；Reader 回环也不重触发
    assert result is not None


def test_validate_prompt_contains_routing_rules():
    """validate.md 必须含内部路由契约（routing.jsonl / 不对外 / 通用信号）。"""
    validate = (WORKFLOW_PATH.parent / "agents" / "validate.md").read_text()
    for marker in ("routing.jsonl", "route_to", "不对外", "内部自评"):
        assert marker in validate, f"validate.md missing: {marker}"


def test_run_prompt_contains_result_contract():
    """run.md 必须含结果契约（results/ + answers 表头 + 命令日志）。"""
    run = (WORKFLOW_PATH.parent / "agents" / "run.md").read_text()
    for marker in ("answers.csv", "target_id,value,unit,source_file", "results/"):
        assert marker in run, f"run.md missing: {marker}"
    assert "commands.log" in run or "命令日志" in run


def test_package_prompt_contains_self_contained_rules():
    """package.md 必须含自包含纪律（BL-025）与 FC-008 执行日志要求。"""
    package = (WORKFLOW_PATH.parent / "agents" / "package.md").read_text()
    for marker in ("只要求 Docker", "digests.txt", "check.log", "退出码"):
        assert marker in package, f"package.md missing: {marker}"
    # check 子命令不得再要求宿主 java/nextflow/R（自包含：分析环境在镜像内）
    check_section = package.split("check() {")[1].split("}")[0]
    assert "nextflow" not in check_section and "java" not in check_section.lower()


def test_package_fail_fast_without_check_log(tmp_path):
    """Package 返回 complete 但无 check.log → fail-fast（FC-008）。"""
    write_files(tmp_path, *REQUIRED_FILES)
    write_provision_evidence(tmp_path)
    write_data_evidence(tmp_path)
    write_run_evidence(tmp_path)
    (tmp_path / "run.sh").write_text("#!/usr/bin/env bash\necho hi\n")
    # 无 07_package/check.log
    agent, intervene = FakeAgent(), FakeIntervene()
    result, logs = run_workflow(tmp_path, agent, intervene)
    assert result is not None  # 返回 validate value（与既有 Package 失败语义一致）
    assert any("前置产物不可用" in line and "check.log" in line for line in logs)


def test_package_fail_fast_with_nonzero_check_log(tmp_path):
    """check.log 退出码非 0 → fail-fast（FC-008）。"""
    write_files(tmp_path, *REQUIRED_FILES)
    write_provision_evidence(tmp_path)
    write_data_evidence(tmp_path)
    write_run_evidence(tmp_path)
    (tmp_path / "run.sh").write_text("#!/usr/bin/env bash\necho hi\n")
    p = tmp_path / "07_package" / "check.log"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("ERROR: nextflow not found\nEXIT=1\n")
    agent, intervene = FakeAgent(), FakeIntervene()
    result, logs = run_workflow(tmp_path, agent, intervene)
    assert any("前置产物不可用" in line and "退出码 0" in line for line in logs)
