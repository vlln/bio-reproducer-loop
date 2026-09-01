"""bio-reproducer loop workflow。

PHASES 注册表是所有 phase agent 调用的唯一事实来源：workflow run() 按序执行，
eval harness 从同一注册表取单 agent 调用的 prompt/agent_def
（loopflow ≥0.26.0 的 `--agent` 单 agent 运行入口）。

单元 03（ADR-0011 §3/§5，BL-016）：Data/Run 的 goal 从 01_plan/plan.md 派生
（删 RNA-seq 硬编码）。单元 0115（ADR-0058）：Validate 后的内部路由回环改用
框架层 `run_rerun_loop`——validate 回调从 Validate 结果 payload.route_to 读
路由决策，route_map 即 ROUTE_CHAINS，回环预算来自调用方参数 routing_budget
（系统内不写死）。routing.jsonl 保留为 validate 的可选交付记录（不依赖它
做回环，FC-003 自检随证据面切换移除）。
"""
import json
import sys
from pathlib import Path

# 同目录模块：workflow 可能以任意 CWD 被加载（loopflow runtime / pytest importlib）
sys.path.insert(0, str(Path(__file__).resolve().parent))
from artifact_checks import (  # noqa: E402
    check_data_phase,
    check_package_phase,
    check_provision_phase,
    check_reader_phase,
    check_run_phase,
)

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

# 路由目标 → 重跑链（含下游；Reader 重跑后 plan.md 变化，Bootstrap 起全部重跑）。
# ADR-0058 迁移：直接作为 run_rerun_loop 的 route_map（route_key → 重跑起始
# stage 名），由框架执行回退编排。
ROUTE_CHAINS = {
    "reader": "Reader",
    "provision": "Provision",
    "data": "Data",
    "run": "Run",
}


def _route_from_result(result):
    """从 Validate 阶段结果读路由决策（ADR-0058 迁移：取代 routing.jsonl）。

    Validate agent 的 goal 返回 payload.route_to（如 "data"/"run"/None）。
    返回 (route_key, message)：route_key None = 全部达标终止。
    """
    if result is None or result.value is None:
        return None, None
    payload = result.value.get("payload", {}) if isinstance(result.value, dict) else {}
    route_key = payload.get("route_to")
    if not route_key:
        return None, None
    reason = payload.get("reason") or ""
    return route_key, reason


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


def _require_parsable(log, check, *args):
    """fail-fast 升级：前置产物必须「存在 + 可被标准工具解析」（ADR-0011 §5）。

    check 为可调用，返回 (ok: bool, detail: str)，*args 透传（如 question_keys）。
    用于 Reader（01_plan）/Data（04_data）/Run（05_run）产物契约。
    """
    ok, detail = check(*args)
    if not ok:
        log(f"前置产物不可用: {detail}；请排查后开新 run 重跑")
        return False
    return True


def _execute_sequence(agent, common, log, phases, plan_text=None, question_keys=None):
    """顺序执行 phases（前置检查 + Data/Run goal 派生 + 产物契约检查）。

    question_keys：任务公开问题清单的 target_id 列表（由评测方经 args 传入；
    无问题清单的任务为 None/[]——lint 跳过键对齐，系统走 T 编号路径）。
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
            # Questions Mapping 对齐（BL-028）：任务注入段提供问题清单时 plan.md
            # 必须逐字覆盖问题清单键，否则在消耗 Provision/Data 算力前拦截
            if not _require_parsable(log, check_reader_phase, ".", question_keys):
                return None, plan_text
            plan_text = _read_plan_text()
        if name == "Provision" and not _require_parsable(log, check_provision_phase, "."):
            return None, plan_text
        if name == "Data" and not _require_parsable(log, check_data_phase, "."):
            return None, plan_text
        if name == "Run" and not _require_parsable(log, check_run_phase, ".", question_keys):
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
    # 任务公开问题清单键（评测方经 args 传入，见 benchmarks/harness/questions_inject.py；
    # 无问题清单的任务为 None/[] → lint 跳过键对齐，系统走 T 编号路径）
    question_keys = args.get("question_keys") or None
    reader_result, plan_text = _execute_sequence(
        agent, common, log, ["Reader"], question_keys=question_keys)
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
    # ADR-0058 迁移：路由回环由框架 run_rerun_loop 编排（取代手写 while +
    # routing.jsonl 读取）。stages = 主链 phase（含 Reader：route_to=reader
    # 时回退重读论文、Bootstrap 起全部重跑，与原 ROUTE_CHAINS.Reader 链语义
    # 一致）；stage_fn 执行单 phase 并做产物检查；validate 从 Validate 结果
    # payload.route_to 读决策。首轮 Reader + confirm_plan 门保留在上方。
    from loopflow.domain.rerun_loop import RouteDecision, RerunOutcome, Stage, run_rerun_loop

    main_chain = ["Reader", "Bootstrap", "Provision", "Data", "Run", "Validate"]
    routing_budget = int(args.get("routing_budget", 0) or 0)

    # 路由决策状态（stage_fn/validate 闭包共享）：最近一次 Validate 的结果
    routing_state = {
        "validate_result": None,
        "plan_text": plan_text,
        # 首轮 Reader 已在 run() 开头执行（含 confirm_plan 门）；run_rerun_loop
        # 从 Reader 开始的 stages 里，首轮 Reader 复用已有结果，回退重跑才
        # 真正重读论文。
        "reader_done": True,
    }

    def stage_fn(stage, context):
        name = stage.name
        # 首轮 Reader 复用 run() 开头的结果；回退重跑（reruns>0）才真正执行
        if name == "Reader" and context.get("reruns") == 0:
            return RerunOutcome(value=routing_state["validate_result"] or {"payload": {}},
                                session_id=None)
        # 前置产物检查（fail-fast）
        if name in PREREQ and not _require_files(log, *PREREQ[name]):
            raise RuntimeError(f"前置产物缺失: {PREREQ[name]}")
        goal = None
        if name in ("Data", "Run"):
            goal = derive_goal(name, routing_state["plan_text"] or "")
        result = _phase(agent, name, common, goal=goal)
        if result.status != "complete":
            log(f"{name}: {result.status} — {result.reason} (turns={result.turns}, tokens={result.tokens})")
            raise RuntimeError(f"{name} 阶段未完成: {result.reason}")
        # 各 phase 产物契约检查（ADR-0011 §5 fail-fast）
        if name == "Reader":
            if not _require_files(log, "01_plan/plan.md"):
                raise RuntimeError("Reader 未产出 plan.md")
            if not _require_parsable(log, check_reader_phase, ".", question_keys):
                raise RuntimeError("Reader plan.md 未通过契约检查")
            routing_state["plan_text"] = _read_plan_text()
        elif name == "Provision" and not _require_parsable(log, check_provision_phase, "."):
            raise RuntimeError("Provision 产物未通过契约检查")
        elif name == "Data" and not _require_parsable(log, check_data_phase, "."):
            raise RuntimeError("Data 产物未通过契约检查")
        elif name == "Run" and not _require_parsable(log, check_run_phase, ".", question_keys):
            raise RuntimeError("Run 产物未通过契约检查")
        elif name == "Validate":
            routing_state["validate_result"] = result
        return RerunOutcome(value=result, session_id=getattr(result, "session_id", None))

    def validate():
        """从最近一次 Validate 结果读 route_to → RouteDecision | None。"""
        result = routing_state["validate_result"]
        route_key, message = _route_from_result(result)
        if route_key is None:
            return None
        return RouteDecision(route_key, message)

    stages = [Stage(name=n, prompt=PHASES[n]["prompt"], agent_def=PHASES[n]["agent_def"],
                    label=PHASES[n]["label"], goal=PHASES[n]["goal"],
                    goal_max_iterations=PHASES[n]["goal_max_iterations"])
              for n in main_chain]

    try:
        rerun = run_rerun_loop(
            stages,
            validate=validate,
            route_map=ROUTE_CHAINS,   # route_key → 重跑起始 stage 名
            budget=routing_budget,
            stage_fn=stage_fn,
            emit_log=log,
        )
    except RuntimeError as exc:
        log(f"阶段执行失败: {exc}")
        return None

    if rerun.status == "exhausted":
        # 回退预算耗尽或路由未知：停止回环，用最近一次 Validate 结果收尾
        # （ADR-0058：耗尽如实记录，不掩盖；FC-007 预算来自调用方）
        log(f"路由回环终止（{rerun.status}）：{rerun.reason}")

    validate_result = routing_state["validate_result"]
    if validate_result is None:
        log("未获得 Validate 结果")
        return None

    # ── Phase 7: Package ─────────────────────────────────────────────
    verdict = _validation_verdict(validate_result)
    if verdict in ("REPRODUCED", "PARTIAL"):
        if not _require_files(log, "06_validate/report.md"):
            return validate_result.value
        package_result = _phase(agent, "Package", common)
        if package_result.status != "complete":
            log(f"Package: {package_result.status} — {package_result.reason} (turns={package_result.turns}, tokens={package_result.tokens})")
        # 07_package 契约（FC-008）：Package 声明 completed 必须有
        # run.sh check 的真实执行日志且退出码 0，否则不通过
        elif not _require_parsable(log, check_package_phase):
            return validate_result.value
    else:
        log(f"跳过 Package：verdict={verdict}")

    return validate_result.value
