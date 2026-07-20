"""Adapter: map benchmark entry → loopflow bio-reproducer call.

This is the ONLY engine-coupled module in the benchmark system.
It launches the `loop` CLI and waits for it to complete.
All information about the run comes from loopflow's own output — the adapter
does not reconstruct, guess, or fabricate.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml


def run(entry_path: str, run_dir: Optional[str] = None) -> dict:
    """Run a benchmark entry via loopflow bio-reproducer.

    Args:
        entry_path: Path to benchmark entry directory (contains metadata.yaml)
        run_dir: Where to write loopflow output (defaults to entry_path/repro-data/)

    Returns:
        Standardized submission.json dict per the benchmark protocol.
    """
    entry_dir = Path(entry_path)

    # 1. Read what the benchmark entry declares about itself
    metadata = _read_metadata(entry_dir)

    if str(metadata.get("protocol_version")) != "2.0":
        raise ValueError("Only benchmark protocol 2.0 is supported")

    # 2. Where loopflow writes its output
    run_root = Path(run_dir) if run_dir else entry_dir
    output_dir = str((run_root / "repro-data").resolve())

    # 3. Stage only public input and resolve the paper inside that bundle
    input_dir = _stage_input(entry_dir, run_root)
    paper_path = _resolve_v2_paper(input_dir)

    # 4. Launch loopflow — no timeout, loopflow controls its own pace
    args = {
        "paper_path": str(paper_path),
        "output_dir": output_dir,
        "language": metadata.get("language", "en"),
    }
    start_time = time.time()

    # Find the loop CLI — prefer venv-local, fall back to PATH
    loop_bin = _find_loop_bin()
    workspace = run_root / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(
        [loop_bin, "run", "bio-reproducer", "--args", json.dumps(args)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=str(workspace),
    )

    # 5. Wait for loopflow to complete — no timeout, no stall detection
    try:
        proc.wait()
    except FileNotFoundError:
        return _make_blocked_output(
            metadata, run_root, "system",
            "loopflow CLI not found. Is 'loop' installed and on PATH?"
        )

    duration = int(time.time() - start_time)

    if proc.returncode != 0:
        return _make_blocked_output(
            metadata, run_root, "system",
            f"loopflow exited with code {proc.returncode}"
        )

    # 6. Describe loopflow's artifacts without assigning evaluator-owned scores
    return _build_submission(metadata, run_root, Path(output_dir), duration)


def _stage_input(entry_dir: Path, run_root: Path) -> Path:
    """Copy only the public input bundle into the system-visible run tree."""
    source = entry_dir / "input"
    if not source.is_dir():
        raise FileNotFoundError(f"InputBundle not found: {source}")
    staged = run_root / "input"
    shutil.copytree(source, staged, dirs_exist_ok=True)
    if (staged / "oracle").exists():
        raise ValueError("InputBundle must not contain an oracle directory")
    return staged.resolve()


def _resolve_v2_paper(input_dir: Path) -> Path:
    for name in ("paper.pdf", "paper.md"):
        paper = input_dir / name
        if paper.is_file():
            return paper
    raise FileNotFoundError(f"Paper not found in InputBundle: {input_dir}")


def _read_metadata(entry_dir: Path) -> dict:
    """Read metadata.yaml — the benchmark entry's declaration of itself."""
    metadata_path = entry_dir / "metadata.yaml"
    if not metadata_path.exists():
        raise FileNotFoundError(f"metadata.yaml not found in {entry_dir}")
    with open(metadata_path) as f:
        return yaml.safe_load(f)


def _find_loop_bin() -> str:
    """Find the loop CLI binary."""
    # Check common venv locations
    candidates = [
        Path(__file__).parent.parent.parent.parent / "loopflow" / ".venv" / "bin" / "loop",
        Path.home() / "Project" / "loopflow" / ".venv" / "bin" / "loop",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    # Fall back to PATH
    found = shutil.which("loop")
    if found:
        return found
    raise FileNotFoundError(
        "loopflow CLI not found. Is 'loop' installed and on PATH?"
    )


def build_submission_from_existing(
    entry_path: str | Path,
    run_dir: str | Path,
) -> dict:
    """Build a v2 submission manifest for an already completed loopflow run."""
    entry_dir = Path(entry_path)
    run_root = Path(run_dir)
    metadata = _read_metadata(entry_dir)
    if str(metadata.get("protocol_version")) != "2.0":
        raise ValueError("Existing-run submission import requires protocol v2")

    legacy_result = run_root / "result.json"
    duration = 0
    claimed_verdict = None
    stages = None
    if legacy_result.is_file():
        previous = json.loads(legacy_result.read_text())
        if "provenance" not in previous:
            duration = int(previous.get("duration_seconds", 0))
            claimed_verdict = previous.get("verdict")
            stages = previous.get("stages")

    return _build_submission(
        metadata,
        run_root,
        run_root / "repro-data",
        duration,
        submission_id=f"{metadata.get('id', entry_dir.name)}-{run_root.name}",
        claimed_verdict=claimed_verdict,
        stages=stages,
    )


def _build_submission(
    metadata: dict,
    run_root: Path,
    repro_dir: Path,
    duration: int,
    submission_id: str | None = None,
    claimed_verdict: str | None = None,
    stages: list[dict] | None = None,
) -> dict:
    """Describe actual artifacts; score and verdict remain evaluator-owned."""
    entry_id = metadata.get("id", "unknown")
    submission_id = submission_id or f"{entry_id}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    artifacts = []
    candidates = _artifact_candidates(entry_id, repro_dir)
    root = run_root.resolve()
    for role, artifact_id, paths in candidates:
        path = next((candidate for candidate in paths if candidate.is_file()), None)
        if path is None:
            continue
        item = {"role": role, "path": str(path.resolve().relative_to(root))}
        if artifact_id is not None:
            item["id"] = artifact_id
        artifacts.append(item)

    if claimed_verdict is None:
        claimed_verdict, _ = _read_verdict_and_score(repro_dir)
    return {
        "submission_id": submission_id,
        "bench_id": entry_id,
        "system": {"name": "bio-reproducer", "version": "0.1.0"},
        "claimed_verdict": claimed_verdict,
        "artifacts": artifacts,
        "execution": {
            "duration_seconds": duration,
            "stages": stages if stages is not None else _read_stages(repro_dir),
        },
    }


def _artifact_candidates(entry_id: str, repro_dir: Path) -> list[tuple[str, str | None, list[Path]]]:
    """Map loopflow output conventions to protocol-level artifact roles."""
    run = repro_dir / "05_run"
    results = run / "results"
    figures = run / "figures"

    result_tables = [
        results / "de_results.csv",
        results / "deseq_results.csv",
        results / "deseq2_results.csv",
        results / "deseq2" / "deseq2_results.csv",
        results / "differential_expression.csv",
    ]
    if entry_id == "bench-005":
        result_tables = [
            results / "results" / "results_DrugA_vs_DMSO.csv",
            results / "DE_DrugA_vs_DMSO.csv",
            results / "DrugA_vs_DMSO.csv",
            results / "DrugA_vs_DMSO_full.csv",
        ]

    candidates = [
        ("result_table", None, [
            *result_tables,
        ]),
        ("normalized_counts", None, [
            results / "normalized_counts.csv",
            results / "counts_filtered_norm.csv",
            results / "cleaned_counts.csv",
        ]),
        ("environment", None, [
            results / "sessionInfo.txt",
            results / "session_info.txt",
            results / "results" / "session_info.txt",
            results / "r_session_info.txt",
        ]),
        ("figure", "volcano", [
            figures / "volcano_plot.png",
            figures / "figure1_volcano.png",
            figures / "figures" / "figure1_volcano.png",
            results / "figures" / "figure1_volcano.png",
        ]),
        ("figure", "go_barplot", [
            figures / "figure2_go_barplot.png",
            figures / "go_barplot.png",
        ]),
        ("figure", "kegg_pathway", [
            figures / "figure3_kegg_pathway.png",
            figures / "kegg_pathway.png",
        ]),
        ("figure", "heatmap", [
            figures / "figure2_heatmap.png",
            figures / "heatmap.png",
        ]),
        ("figure", "pca", [
            figures / "figure2_pca.png",
            figures / "figures" / "figure2_pca.png",
            results / "figures" / "figure2_pca.png",
            figures / "pca.png",
        ]),
        ("go_enrichment", None, [
            results / "go_enrichment.csv",
        ]),
        ("run_report", None, [
            run / "run_results.md",
        ]),
        ("analysis_log", None, [
            results / "analysis.log",
            run / "reports" / "run_analysis.log",
            run / "p5_analysis.log",
        ]),
        ("run_log", None, [
            run / "reports" / "run_analysis.log",
        ]),
    ]

    if entry_id == "bench-004":
        candidates.extend([
            ("result_table", "cortex_vs_thalamus", [
                results / "de_results_cortex_vs_thalamus.csv",
                results / "cortex_vs_thalamus_de_results.csv",
            ]),
            ("result_table", "thalamus_vs_cortex", [
                results / "results" / "de_Thalamus_vs_Cortex.csv",
                results / "Thalamus_vs_Cortex.csv",
            ]),
            ("result_table", "hippocampus_vs_cortex", [
                results / "results" / "de_Hippocampus_vs_Cortex.csv",
                results / "Hippocampus_vs_Cortex.csv",
            ]),
            ("result_table", "striatum_vs_cortex", [
                results / "results" / "de_Striatum_vs_Cortex.csv",
                results / "Striatum_vs_Cortex.csv",
            ]),
            ("result_table", "all_contrasts", [
                results / "results" / "all_degs.csv",
                results / "de_results_all_contrasts.csv",
                results / "de_results.csv",
            ]),
        ])
    return candidates


def _read_stages(repro_dir: Path) -> list[dict]:
    """Read phase completion status from the output directory structure.

    The phase directories are loopflow's canonical output — each phase
    writes its main output file to a numbered subdirectory.
    """
    phase_map = {
        "01_plan": "Reader",
        "02_bootstrap": "Bootstrap",
        "03_provision": "Provision",
        "04_data": "Data",
        "05_run": "Run",
        "06_validate": "Validate",
        "07_package": "Package",
    }

    main_files = {
        "01_plan": "plan.md",
        "02_bootstrap": "bootstrap.md",
        "03_provision": "provision.md",
        "04_data": "data_manifest.md",
        "05_run": "run_results.md",
        "06_validate": "report.md",
        "07_package": "README.md",  # Package writes to repro_dir root
    }

    stages = []
    for dir_name, phase_name in phase_map.items():
        if dir_name == "07_package":
            # Package phase writes to the root of repro_dir
            if (repro_dir / "README.md").exists():
                stages.append({"name": phase_name, "status": "completed"})
            else:
                stages.append({"name": phase_name, "status": "blocked"})
            continue

        phase_dir = repro_dir / dir_name
        if not phase_dir.exists():
            stages.append({"name": phase_name, "status": "blocked"})
            continue

        main_file = main_files.get(dir_name)
        if main_file and (phase_dir / main_file).exists():
            stages.append({"name": phase_name, "status": "completed"})
        else:
            stages.append({"name": phase_name, "status": "failed"})

    return stages


def _read_verdict_and_score(repro_dir: Path) -> tuple:
    """Read verdict and score from the validate agent's metrics.json.

    The validate agent writes structured JSON — the adapter reads it directly
    instead of parsing Markdown tables. Handles both flat and nested formats.
    """
    metrics_path = repro_dir / "06_validate" / "metrics.json"
    if not metrics_path.exists():
        return "BLOCKED", 0

    with open(metrics_path) as f:
        metrics = json.load(f)

    # Format 1 (flat): {"verdict": "REPRODUCED", "total_score": 88, ...}
    verdict = metrics.get("verdict")
    score = metrics.get("total_score")

    if verdict is not None and score is not None:
        return verdict, int(score)

    # Format 2 (nested): dimensions contain scores, extract from report.md
    report_path = repro_dir / "06_validate" / "report.md"
    if report_path.exists():
        report = report_path.read_text()
        import re
        # Extract verdict from "| Status | REPRODUCED |"
        v_match = re.search(r"Status\s*\|\s*(\w+)", report)
        if v_match:
            verdict = v_match.group(1)
        # Extract total score from "| **Total** | **90.0** | **100** |"
        s_match = re.search(r"\*\*Total\*\*\s*\|\s*\*{0,2}([\d.]+)\*{0,2}\s*\|\s*\*{0,2}\d+\*{0,2}", report)
        if s_match:
            score = int(float(s_match.group(1)))
            return verdict or "BLOCKED", score

    return "BLOCKED", 0


def _make_blocked_output(metadata: dict, run_root: Path, reason: str, error: str) -> dict:
    entry_id = metadata.get("id", "unknown")
    submission_id = f"{entry_id}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    return {
        "submission_id": submission_id,
        "bench_id": entry_id,
        "system": {"name": "bio-reproducer", "version": "0.1.0"},
        "artifacts": [],
        "execution": {
            "duration_seconds": 0,
            "stages": [],
            "blocked_reason": reason,
            "error": error,
        },
    }
