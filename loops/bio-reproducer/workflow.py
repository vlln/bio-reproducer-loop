from loopflow import GoalBlocked

meta = {
    "name": "bio-reproducer",
    "description": "复现生物信息学论文：7 阶段从论文提取到打包交付",
    "requires": {
        "environment": "pixi.toml",
    },
    "phases": [
        {"title": "Reader", "detail": "提取论文声明，创建复现计划 plan.md"},
        {"title": "Bootstrap", "detail": "检查系统环境：Java、Nextflow、容器运行时"},
        {"title": "Provision", "detail": "部署工具容器环境"},
        {"title": "Data", "detail": "下载分析所需数据"},
        {"title": "Run", "detail": "运行分析流水线"},
        {"title": "Validate", "detail": "对比复现结果与论文声称"},
        {"title": "Package", "detail": "生成 README 和 run.sh"},
    ],
}


def run(agent, parallel, pipeline, phase, log, args, workflow, state):
    paper_path = args.get("paper_path")
    paper_doi = args.get("paper_doi")
    out = args.get("output_dir", "repro-data")
    language = args.get("language", "zh")

    if not paper_path and not paper_doi:
        log("Error: paper_path or paper_doi is required")
        return None

    common = dict(
        paper_path=paper_path or "",
        paper_doi=paper_doi or "",
        language=language,
        output_dir=out,
    )

    # ── Phase 1: Reader ──────────────────────────────────────────────
    phase("Reader")
    try:
        reader_result = agent(
            "提取论文全部声明和资源。",
            agent_def="reader",
            goal="完整提取论文的所有方法声明、数据声明、工具声明和结果声明，创建完整的复现计划 plan.md。",
            goal_max_iterations=5,
            **common,
        )
    except GoalBlocked as e:
        log(f"Reader blocked: {e}")
        return None

    # ── Phase 2: Bootstrap ───────────────────────────────────────────
    phase("Bootstrap")
    try:
        bootstrap_result = agent(
            "检查 Java 11+、Nextflow、容器运行时。",
            agent_def="bootstrap",
            goal="完整检查所有系统运行时环境：Java、Nextflow、Docker，每个组件必须实际运行验证。",
            goal_max_iterations=3,
            **common,
        )
    except GoalBlocked as e:
        log(f"Bootstrap blocked: {e}")
        return None

    # ── Phase 3: Provision ───────────────────────────────────────────
    phase("Provision")
    try:
        provision_result = agent(
            "部署工具容器环境。",
            agent_def="provision",
            goal="成功部署所有必需的工具容器镜像，每个镜像必须拉取成功并通过验证。",
            goal_max_iterations=5,
            **common,
        )
    except GoalBlocked as e:
        log(f"Provision blocked: {e}")
        return None

    # ── Phase 4: Data ────────────────────────────────────────────────
    phase("Data")
    try:
        data_result = agent(
            "下载分析所需数据。",
            agent_def="data",
            goal="完整下载所有必需数据文件：FASTQ 样本、参考基因组、微阵列数据。验证每个文件的完整性和预期大小。",
            goal_max_iterations=8,
            **common,
        )
    except GoalBlocked as e:
        log(f"Data blocked: {e}")
        return None

    # ── Phase 5: Run ─────────────────────────────────────────────────
    phase("Run")
    try:
        run_result = agent(
            "运行分析流水线。",
            agent_def="run",
            goal="成功运行完整的 RNA-Seq 分析流水线，生成所有图表和结果文件。",
            goal_max_iterations=5,
            **common,
        )
    except GoalBlocked as e:
        log(f"Run blocked: {e}")
        return None

    # ── Phase 6: Validate ────────────────────────────────────────────
    phase("Validate")
    try:
        validate_result = agent(
            "对比复现结果与论文声称。",
            agent_def="validate",
            goal="完整验证所有可复现的图表和指标，给出最终评分和偏差分析。",
            goal_max_iterations=3,
            **common,
        )
    except GoalBlocked as e:
        log(f"Validate blocked: {e}")
        return None

    # ── Phase 7: Package ─────────────────────────────────────────────
    verdict = validate_result.get("payload", {}).get("verdict") if validate_result else None
    if verdict in ("REPRODUCED", "PARTIAL"):
        phase("Package")
        try:
            package_result = agent(
                "打包复现产物：生成 README、run.sh、.gitignore。",
                agent_def="package",
                goal="创建完整的复现产物包：README.md、run.sh、.gitignore。",
                goal_max_iterations=3,
                **common,
            )
        except GoalBlocked as e:
            log(f"Package blocked: {e}")
    else:
        log(f"跳过 Package：verdict={verdict}")

    return validate_result