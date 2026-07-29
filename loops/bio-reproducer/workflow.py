import json
from pathlib import Path


def _validation_verdict(validate_result):
    if validate_result.value:
        verdict = validate_result.value.get("payload", {}).get("verdict")
        if verdict:
            return verdict

    metrics_path = Path("06_validate") / "metrics.json"
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
    )

    # ── Phase 1: Reader ──────────────────────────────────────────────
    reader_result = agent(
        "提取论文全部声明和资源。",
        agent_def="reader",
        label="Reader",
        goal="完整提取论文的所有方法声明、数据声明、工具声明和结果声明，创建完整的复现计划 plan.md。",
        goal_max_iterations=5,
        **common,
    )
    if reader_result.status != "complete":
        log(f"Reader: {reader_result.status} — {reader_result.reason} (turns={reader_result.turns}, tokens={reader_result.tokens})")
        return None
    if not _require_files(log, "01_plan/plan.md"):
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

    # ── Phase 2: Bootstrap ───────────────────────────────────────────
    bootstrap_result = agent(
        "检查 Java 11+、Nextflow、容器运行时。",
        agent_def="bootstrap",
        label="Bootstrap",
        goal="完整检查所有系统运行时环境：Java、Nextflow、Docker，每个组件必须实际运行验证。",
        goal_max_iterations=3,
        **common,
    )
    if bootstrap_result.status != "complete":
        log(f"Bootstrap: {bootstrap_result.status} — {bootstrap_result.reason} (turns={bootstrap_result.turns}, tokens={bootstrap_result.tokens})")
        return None

    # ── Phase 3: Provision ───────────────────────────────────────────
    if not _require_files(log, "01_plan/plan.md"):
        return None
    provision_result = agent(
        "部署工具容器环境。",
        agent_def="provision",
        label="Provision",
        goal="成功部署所有必需的工具容器镜像，每个镜像必须拉取成功并通过验证。",
        goal_max_iterations=5,
        **common,
    )
    if provision_result.status != "complete":
        log(f"Provision: {provision_result.status} — {provision_result.reason} (turns={provision_result.turns}, tokens={provision_result.tokens})")
        return None

    # ── Phase 4: Data ────────────────────────────────────────────────
    if not _require_files(log, "01_plan/plan.md", "03_provision/provision.md"):
        return None
    data_result = agent(
        "下载分析所需数据。",
        agent_def="data",
        label="Data",
        goal="完整下载所有必需数据文件：FASTQ 样本、参考基因组、微阵列数据。验证每个文件的完整性和预期大小。",
        goal_max_iterations=8,
        **common,
    )
    if data_result.status != "complete":
        log(f"Data: {data_result.status} — {data_result.reason} (turns={data_result.turns}, tokens={data_result.tokens})")
        return None

    # ── Phase 5: Run ─────────────────────────────────────────────────
    if not _require_files(log, "01_plan/plan.md", "03_provision/provision.md", "04_data/data_manifest.md"):
        return None
    run_result = agent(
        "运行分析流水线。",
        agent_def="run",
        label="Run",
        goal="成功运行完整的 RNA-Seq 分析流水线，生成所有图表和结果文件。",
        goal_max_iterations=5,
        **common,
    )
    if run_result.status != "complete":
        log(f"Run: {run_result.status} — {run_result.reason} (turns={run_result.turns}, tokens={run_result.tokens})")
        return None

    # ── Phase 6: Validate ────────────────────────────────────────────
    if not _require_files(log, "01_plan/plan.md", "05_run/run_results.md"):
        return None
    validate_result = agent(
        "对比复现结果与论文声称。",
        agent_def="validate",
        label="Validate",
        goal="完整验证所有可复现的图表和指标，给出最终评分和偏差分析。",
        goal_max_iterations=3,
        **common,
    )
    if validate_result.status != "complete":
        log(f"Validate: {validate_result.status} — {validate_result.reason} (turns={validate_result.turns}, tokens={validate_result.tokens})")
        return None

    # ── Phase 7: Package ─────────────────────────────────────────────
    verdict = _validation_verdict(validate_result)
    if verdict in ("REPRODUCED", "PARTIAL"):
        if not _require_files(log, "06_validate/report.md"):
            return validate_result.value
        package_result = agent(
            "打包复现产物：生成 README、run.sh、.gitignore。",
            agent_def="package",
            label="Package",
            goal="创建完整的复现产物包：README.md、run.sh、.gitignore。",
            goal_max_iterations=3,
            **common,
        )
        if package_result.status != "complete":
            log(f"Package: {package_result.status} — {package_result.reason} (turns={package_result.turns}, tokens={package_result.tokens})")
    else:
        log(f"跳过 Package：verdict={verdict}")

    return validate_result.value
