"""Adapter: map benchmark entry → loopflow bio-reproducer call.

This is the ONLY engine-coupled module in the benchmark system.
It launches the `loop` CLI and waits for it to complete.
All information about the run comes from loopflow's own output — the adapter
does not reconstruct, guess, or fabricate.
"""

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
        Standardized result.json dict per the benchmark spec.
    """
    entry_dir = Path(entry_path)

    # 1. Read what the benchmark entry declares about itself
    metadata = _read_metadata(entry_dir)

    # 2. Where loopflow writes its output
    output_dir = str(Path(run_dir) / "repro-data") if run_dir else str(entry_dir / "repro-data")

    # 3. Resolve the paper file (benchmark declares what it has; adapter resolves)
    paper_path = _resolve_paper(entry_dir, metadata)

    # 4. Launch loopflow — no timeout, loopflow controls its own pace
    args = {
        "paper_path": str(paper_path),
        "output_dir": output_dir,
        "language": metadata.get("language", "en"),
    }
    start_time = time.time()

    # Find the loop CLI — prefer venv-local, fall back to PATH
    loop_bin = _find_loop_bin()
    proc = subprocess.Popen(
        [loop_bin, "run", "bio-reproducer", "--args", json.dumps(args)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # 5. Wait for loopflow to complete — no timeout, no stall detection
    try:
        proc.wait()
    except FileNotFoundError:
        return _make_blocked_result(
            metadata, "system",
            "loopflow CLI not found. Is 'loop' installed and on PATH?"
        )

    duration = int(time.time() - start_time)

    if proc.returncode != 0:
        return _make_blocked_result(
            metadata, "system",
            f"loopflow exited with code {proc.returncode}"
        )

    # 6. Read loopflow's own output — no reconstruction
    return _build_result(metadata, output_dir, duration)


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


def _resolve_paper(entry_dir: Path, metadata: dict) -> Path:
    """Resolve the paper file. Benchmark declares what it has; adapter resolves the path."""
    paper = entry_dir / metadata.get("paper_pdf", "paper.pdf")
    if paper.exists():
        return paper
    # Fallback: some entries provide Markdown instead of PDF
    paper_md = entry_dir / "paper.md"
    if paper_md.exists():
        return paper_md
    raise FileNotFoundError(
        f"Paper not found: {paper} (and no paper.md fallback)"
    )


def _build_result(metadata: dict, output_dir: str, duration: int) -> dict:
    """Build result.json from loopflow's own output files.

    All information comes from loopflow's output — the adapter does not
    reconstruct, guess, or fabricate any metric.
    """
    repro_dir = Path(output_dir)
    entry_id = metadata.get("id", "unknown")
    bench_version = metadata.get("version", "1.0.0")

    # Phases: check which output directories exist and have content
    stages = _read_stages(repro_dir)

    # Verdict and score: read from validate agent's structured output
    verdict, score = _read_verdict_and_score(repro_dir)

    run_id = f"{entry_id}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

    return {
        "run_id": run_id,
        "bench_id": entry_id,
        "bench_version": bench_version,
        "verdict": verdict,
        "score": score,
        "stages": stages,
        "duration_seconds": duration,
    }


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


def _make_blocked_result(metadata: dict, reason: str, error: str) -> dict:
    """Create a BLOCKED result when loopflow cannot be executed."""
    entry_id = metadata.get("id", "unknown")
    bench_version = metadata.get("version", "1.0.0")
    run_id = f"{entry_id}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

    return {
        "run_id": run_id,
        "bench_id": entry_id,
        "bench_version": bench_version,
        "verdict": "BLOCKED",
        "score": 0,
        "stages": [],
        "duration_seconds": 0,
        "blocked_reason": reason,
        "error": error,
    }