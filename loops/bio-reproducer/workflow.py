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
    "state": {
        "attempt": 0,
    },
}

def _check_phase(result, phase_name, log):
    """Check phase result and return (proceed, abort).

    Returns:
        (True, False)   — proceed to next phase
        (False, False)  — retry current loop
        (False, True)   — abort workflow entirely
    """
    if result is None:
        log(f"{phase_name}: no result returned")
        return False, False  # retry — may be transient

    status = result.get("status", "unknown")
    summary = result.get("summary", "")
    log(f"{phase_name}: [{status}] {summary}")

    if status == "blocked":
        for m in result.get("missing", []):
            log(f"  BLOCKED: {m.get('item')} — {m.get('reason')}")
        return False, True   # abort

    if status == "failed":
        return False, False  # retry

    if status == "partial":
        for m in result.get("missing", []):
            log(f"  MISSING: {m.get('item')} — {m.get('reason')} [{m.get('action', 'skip')}]")
        return True, False   # proceed with degradation

    # completed
    return True, False


def run(agent, parallel, pipeline, phase, log, args, workflow, state):
    paper_path = args.get("paper_path")
    paper_doi = args.get("paper_doi")
    out = args.get("output_dir", "repro-data")
    language = args.get("language", "zh")
    phase_retries = args.get("phase_retries", 3)

    if not paper_path and not paper_doi:
        log("Error: paper_path or paper_doi is required")
        return None

    # ── Phase 1: Reader ──────────────────────────────────────────────
    phase("Reader")
    log("提取论文信息，收集补充材料...")
    reader_result = agent(
        "提取论文全部声明和资源。",
        agent_def="reader",
        paper_path=paper_path or "",
        paper_doi=paper_doi or "",
        language=language,
        output_dir=out,
    )
    proceed, abort = _check_phase(reader_result, "Reader", log)
    if abort:
        return None

    # ── Phase 2: Bootstrap ───────────────────────────────────────────
    phase("Bootstrap")
    log("检查系统环境...")
    bootstrap_result = agent(
        "检查 Java 11+、Nextflow、容器运行时。",
        agent_def="bootstrap",
        language=language,
        output_dir=out,
    )
    proceed, abort = _check_phase(bootstrap_result, "Bootstrap", log)
    if abort:
        return None

    # ── Phase 3-6: Retry loop ────────────────────────────────────────
    report = None
    while state.attempt < phase_retries:
        if state.attempt > 0:
            log(f"重试第 {state.attempt} 轮...")

        # Phase 3: Provision
        phase("Provision")
        provision_result = agent(
            "部署工具容器环境。",
            agent_def="provision",
            language=language,
            output_dir=out,
        )
        proceed, abort = _check_phase(provision_result, "Provision", log)
        if abort:
            break
        if not proceed:
            state.attempt += 1
            continue

        # Phase 4: Data
        phase("Data")
        data_result = agent(
            "下载分析所需数据。",
            agent_def="data",
            language=language,
            output_dir=out,
        )
        proceed, abort = _check_phase(data_result, "Data", log)
        if abort:
            break
        if not proceed:
            state.attempt += 1
            continue

        # Phase 5: Run
        phase("Run")
        run_result = agent(
            "运行分析流水线。",
            agent_def="run",
            language=language,
            output_dir=out,
        )
        proceed, abort = _check_phase(run_result, "Run", log)
        if abort:
            break
        if not proceed:
            state.attempt += 1
            continue

        # Phase 6: Validate
        phase("Validate")
        report = agent(
            "对比复现结果与论文声称。",
            agent_def="validate",
            language=language,
            output_dir=out,
        )

        if report and report.get("payload", {}).get("verdict") not in ("FAILED", "BLOCKED"):
            break
        if report and report.get("payload", {}).get("verdict") == "BLOCKED":
            log("验证被阻塞，终止")
            break
        log(f"验证未通过，准备重试...")
        state.attempt += 1

    # ── Phase 7: Package ─────────────────────────────────────────────
    verdict = report.get("payload", {}).get("verdict") if report else None
    if verdict in ("REPRODUCED", "PARTIAL"):
        phase("Package")
        package_result = agent(
            "打包复现产物：生成 README、run.sh、.gitignore。",
            agent_def="package",
            language=language,
            output_dir=out,
        )
        if package_result:
            log(f"Package: {package_result.get('summary', 'done')}")
    else:
        log(f"跳过 Package：verdict={verdict}")

    return report