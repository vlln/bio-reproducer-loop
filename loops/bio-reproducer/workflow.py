"""bio-reproducer loop workflow。

PHASES 注册表是所有 phase agent 调用的唯一事实来源：workflow run() 按序执行，
eval harness 从同一注册表取单 agent 调用的 prompt/agent_def
（loopflow ≥0.26.0 的 `--agent` 单 agent 运行入口）。

单元 03（ADR-0011 §3/§5，BL-016）：Data/Run 的 goal 从 01_plan/plan.md 派生
（删 RNA-seq 硬编码）；Validate 后按 06_validate/routing.jsonl 做内部路由回环，
回环预算来自调用方参数 routing_budget（系统内不写死）。
"""
import json
import sys
from pathlib import Path

# 同目录模块：workflow 可能以任意 CWD 被加载（loopflow runtime / pytest importlib）
sys.path.insert(0, str(Path(__file__).resolve().parent))
from artifact_checks import check_data_phase, check_run_phase  # noqa: E402

# ── Phase agent 调用注册表（唯一事实来源）───────────────────────────────
# workflow run() 按序执行；eval harness 从同一注册表取单 agent 调用的
# prompt/agent_def（loopflow ≥0.26.0 的 `--agent` 单 agent 运行入口），
# 避免两处维护 phase prompt 造成漂移。
PHASES = {
    "Reader": {
        "prompt": "提取论文全部声明和资源。",
        "agent_def": "reader",
        "label": "Reader",
        "goal": "完整提取论文的所有方法声明、数据声明、工具声明和结果声明，创建完整的复现计划 plan.md。",
        "goal_max_iterations": 5,
    },
    "Bootstrap": {
        "prompt": "检查 Java 11+、Nextflow、容器运行时。",
        "agent_def": "bootstrap",
        "label": "Bootstrap",
        "goal": "完整检查所有系统运行时环境：Java、Nextflow、Docker，每个组件必须实际运行验证。",
        "goal_max_iterations": 3,
    },
    "Provision": {
        "prompt": "部署工具容器环境。",
        "agent_def": "provision",
        "label": "Provision",
        "goal": "成功部署所有必需的工具容器镜像，每个镜像必须拉取成功并通过验证。",
        "goal_max_iterations": 5,
    },
    "Data": {
        "prompt": "下载分析所需数据。",
        "agent_def": "data",
        "label": "Data",
        # 通用默认 goal；完整 workflow 运行时由 derive_goal 从 plan.md 派生覆盖（BL-016）
        "goal": "完整下载复现所需数据并验证完整性（每数据源落获取日志，已下载文件落 sha256sums.txt，按终态类别记录状态）。",
        "goal_max_iterations": 8,
    },
    "Run": {
        "prompt": "运行分析流水线。",
        "agent_def": "run",
        "label": "Run",
        "goal": "成功运行分析流水线复现论文目标，生成所有结果文件和图表（结果落 05_run/results/，数值声明写入 answers.csv）。",
        "goal_max_iterations": 5,
    },
    "Validate": {
        "prompt": "对比复现结果与论文声称。",
        "agent_def": "validate",
        "label": "Validate",
        "goal": "完整对比复现结果与论文声称，判定不达标目标应回到哪个 phase，并追加记录到 routing.jsonl。",
        "goal_max_iterations": 3,
    },
    "Package": {
        "prompt": "打包复现产物：生成 README、run.sh、.gitignore。",
        "agent_def": "package",
        "label": "Package",
        "goal": "创建完整的复现产物包：README.md、run.sh、.gitignore。",
        "goal_max_iterations": 3,
    },
}


# ── goal 从 plan.md 派生（BL-016，ADR-0011 §3 通用信号原则）────────────
def _section_text(plan_text, heading):
    """提取 plan.md 中指定标题（如 'Data Requirements'）下的段落文本。

    只做标题定位与文本摘取，不解析散文语义。
    """
    out, capture = [], False
    for line in plan_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            if capture:
                break
            if stripped.lstrip("#").strip() == heading:
                capture = True
        elif capture:
            out.append(line)
    return "\n".join(out).strip()


_GOAL_SECTIONS = {
    "Data": ("Data Requirements", "Reproduction Target"),
    "Run": ("Reproduction Target", "Analysis Steps"),
}
_GOAL_TEMPLATES = {
    "Data": "完整下载复现所需数据并验证完整性（每数据源落获取日志，已下载文件落 sha256sums.txt，按终态类别记录状态）。复现目标：{snippet}",
    "Run": "运行分析流水线复现论文目标，生成结果文件与图表（结果落 05_run/results/，数值声明写入 answers.csv）。复现目标：{snippet}",
}
# 摘取段落长度护栏（非评分阈值）：plan.md 段落可能很长，goal 只需要点
_SNIPPET_LIMIT = 500


def derive_goal(phase, plan_text):
    """从 plan.md 派生 phase goal（只搬运已有内容，不做论文语义判断）。

    无匹配段落时返回 None（调用方回退注册表默认 goal）。
    """
    template = _GOAL_TEMPLATES.get(phase)
    if template is None:
        return None
    for heading in _GOAL_SECTIONS.get(phase, ()):
        section = _section_text(plan_text, heading)
        if section:
            snippet = section.replace("\n", " ")[:_SNIPPET_LIMIT]
            return template.format(snippet=snippet)
    return None


def _read_plan_text(workdir="."):
    try:
        return (Path(workdir) / "01_plan" / "plan.md").read_text(encoding="utf-8")
    except OSError:
        return None


# ── 前置产物与路由 ──────────────────────────────────────────────────────
PREREQ = {
    "Provision": ("01_plan/plan.md",),
    "Data": ("01_plan/plan.md", "03_provision/provision.md"),
    "Run": ("01_plan/plan.md", "03_provision/provision.md", "04_data/data_manifest.md"),
    "Validate": ("01_plan/plan.md", "05_run/run_results.md"),
}

# 路由目标 → 重跑链（含下游；Reader 重跑后 plan.md 变化，Bootstrap 起全部重跑）
ROUTE_CHAINS = {
    "Reader": ["Reader", "Bootstrap", "Provision", "Data", "Run", "Validate"],
    "Provision": ["Provision", "Data", "Run", "Validate"],
    "Data": ["Data", "Run", "Validate"],
    "Run": ["Run", "Validate"],
}


def _read_routing(workdir="."):
    """读 06_validate/routing.jsonl（追加式，一行一事件）。"""
    path = Path(workdir) / "06_validate" / "routing.jsonl"
    events = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def _routing_route(events):
    """取**最后一个事件**的 route_to 决定回环目标（最近一次 Validate 的决策）。

    routing.jsonl 为追加式，历史事件不代表当前状态；最后一次 Validate 的
    route_to 为空（null）即终止。无事件返回 None。
    """
    if not events:
        return None
    return events[-1].get("route_to") or None


def _phase(agent, name, common, goal=None):
    """按 PHASES 注册表发起一个 phase agent 调用；goal 可覆盖注册表默认。"""
    spec = PHASES[name]
    return agent(
        spec["prompt"],
        agent_def=spec["agent_def"],
        label=spec["label"],
        goal=goal or spec["goal"],
        goal_max_iterations=spec["goal_max_iterations"],
        **common,
    )


def _validation_verdict(validate_result, workdir=Path(".")):
    if validate_result.value:
        verdict = validate_result.value.get("payload", {}).get("verdict")
        if verdict:
            return verdict

    metrics_path = Path(workdir) / "06_validate" / "metrics.json"
    try:
        metrics = json.loads(metrics_path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    return metrics.get("verdict")


def _require_files(log, *paths):
    """fail-fast：上一阶段幻觉完成（返回 complete 但没写产物）时立即暴露。"""
    missing = [p for p in paths if not Path(p).exists()]
    if missing:
        log(f"前置产物缺失: {', '.join(missing)}；请排查后开新 run 重跑（recover 会 replay 缓存的旧结果，会在同一检查点再次失败）")
        return False
    return True


def _require_parsable(log, check):
    """fail-fast 升级：前置产物必须「存在 + 可被标准工具解析」（ADR-0011 §5）。

    check 为无参可调用，返回 (ok: bool, detail: str)。用于 Data（04_data）与
    Run（05_run）产物契约。
    """
    ok, detail = check()
    if not ok:
        log(f"前置产物不可用: {detail}；请排查后开新 run 重跑")
        return False
    return True


def _execute_sequence(agent, common, log, phases, plan_text=None):
    """顺序执行 phases（前置检查 + Data/Run goal 派生 + 产物契约检查）。

    返回 (result, plan_text)：result 为最后一个 phase 的 result 或 None（fail-fast）；
    plan_text 在 Reader 完成后刷新（plan.md 可能被重写）。
    """
    result = None
    for name in phases:
        if name in PREREQ and not _require_files(log, *PREREQ[name]):
            return None, plan_text
        goal = None
        if name in ("Data", "Run"):
            if plan_text is None:
                plan_text = _read_plan_text()
            goal = derive_goal(name, plan_text or "")
        result = _phase(agent, name, common, goal=goal)
        if result.status != "complete":
            log(f"{name}: {result.status} — {result.reason} (turns={result.turns}, tokens={result.tokens})")
            return None, plan_text
        if name == "Reader":
            # Reader 幻觉完成（返回 complete 但没写 plan.md）立即暴露，停在确认门之前
            if not _require_files(log, "01_plan/plan.md"):
                return None, plan_text
            plan_text = _read_plan_text()
        if name == "Data" and not _require_parsable(log, check_data_phase):
            return None, plan_text
        if name == "Run" and not _require_parsable(log, check_run_phase):
            return None, plan_text
    return result, plan_text


def run(agent, parallel, pipeline, log, args, workflow, intervene, state):
    paper_path = args.get("paper_path")
    paper_doi = args.get("paper_doi")
    language = args.get("language", "zh")

    if not paper_path and not paper_doi:
        log("Error: paper_path or paper_doi is required")
        return None

    common = dict(
        paper_path=paper_path or "",
        paper_doi=paper_doi or "",
        language=language,
        consent=args.get("consent", "ask"),
        scope=args.get("scope", ""),
    )

    # ── Phase 1: Reader ──────────────────────────────────────────────
    reader_result, plan_text = _execute_sequence(agent, common, log, ["Reader"])
    if reader_result is None:
        return None

    # 人工确认复现计划后再进入高成本阶段（Provision/Data）；
    # 无人值守运行（benchmark/沙箱）传 confirm_plan=false 跳过此门
    if args.get("confirm_plan", True):
        answer = intervene(
            "confirm-plan",
            "Reader 已生成 01_plan/plan.md，请审查复现计划。确认后将继续部署环境和下载数据。",
            options=["继续", "终止"],
            allow_custom=False,
        )
        if answer != "继续":
            log(f"用户终止：plan.md 未通过审查（{answer}）")
            return None

    # ── Phase 2-6: Bootstrap → Provision → Data → Run → Validate ────
    validate_result, plan_text = _execute_sequence(
        agent, common, log,
        ["Bootstrap", "Provision", "Data", "Run", "Validate"],
        plan_text,
    )
    if validate_result is None:
        return None

    # ── 内部路由回环（ADR-0011 §3；FC-007：预算来自调用方参数）────────
    # routing_budget：允许的回环轮数；0 = 线性执行（默认）。benchmark
    # envelope 按 deadline 派生传入，系统内不写死上限。
    routing_budget = int(args.get("routing_budget", 0) or 0)
    while routing_budget > 0:
        route = _routing_route(_read_routing())
        if route is None:
            break
        chain = ROUTE_CHAINS.get(route)
        if chain is None:
            log(f"Validate 路由目标未知: {route}；终止回环")
            break
        log(f"Validate 路由回 {route}（回环预算剩余 {routing_budget - 1}）")
        validate_result, plan_text = _execute_sequence(agent, common, log, chain, plan_text)
        if validate_result is None:
            return None
        routing_budget -= 1

    # ── Phase 7: Package ─────────────────────────────────────────────
    verdict = _validation_verdict(validate_result)
    if verdict in ("REPRODUCED", "PARTIAL"):
        if not _require_files(log, "06_validate/report.md"):
            return validate_result.value
        package_result = _phase(agent, "Package", common)
        if package_result.status != "complete":
            log(f"Package: {package_result.status} — {package_result.reason} (turns={package_result.turns}, tokens={package_result.tokens})")
    else:
        log(f"跳过 Package：verdict={verdict}")

    return validate_result.value
