"""Adapter: map benchmark entry → loopflow bio-reproducer call.

This is the ONLY engine-coupled module in the benchmark system.
It shells out to the `loop` CLI to run the bio-reproducer workflow.
"""

import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

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

    # 1. Read metadata
    metadata_path = entry_dir / "metadata.yaml"
    if not metadata_path.exists():
        raise FileNotFoundError(f"metadata.yaml not found in {entry_path}")
    with open(metadata_path) as f:
        metadata = yaml.safe_load(f)

    # 2. Determine output directory
    if run_dir is None:
        output_dir = str(entry_dir / "repro-data")
    else:
        output_dir = str(Path(run_dir) / "repro-data")

    # 3. Resolve paper path (prefer PDF, fall back to Markdown)
    paper_pdf = entry_dir / metadata.get("paper_pdf", "paper.pdf")
    if not paper_pdf.exists():
        # Fallback: try paper.md
        paper_md = entry_dir / "paper.md"
        if paper_md.exists():
            paper_pdf = paper_md
        else:
            return _make_blocked_result(
                metadata, "external",
                f"Paper file not found: {paper_pdf} (and no paper.md fallback)"
            )

    args = {
        "paper_path": str(paper_pdf),
        "output_dir": output_dir,
        "language": "en",
    }

    # 4. Execute loopflow
    start_time = time.time()
    try:
        result = subprocess.run(
            ["loop", "run", "bio-reproducer", "--args", json.dumps(args)],
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutes for L3
        )
        duration = int(time.time() - start_time)

        if result.returncode != 0:
            return _make_blocked_result(
                metadata, "system",
                f"loopflow exited with code {result.returncode}: {result.stderr[:500]}"
            )

    except subprocess.TimeoutExpired:
        return _make_blocked_result(metadata, "system", "loopflow execution timed out (10 min)")
    except FileNotFoundError:
        return _make_blocked_result(
            metadata, "system",
            "loopflow CLI not found. Is 'loop' installed and on PATH?"
        )

    # 5. Extract result from loopflow output
    return _extract_result(metadata, output_dir, duration)


def _extract_result(metadata: dict, output_dir: str, duration: int) -> dict:
    """Extract standardized result from loopflow phase output directories."""
    repro_dir = Path(output_dir)
    entry_id = metadata.get("id", "unknown")
    bench_version = metadata.get("version", "1.0.0")

    stages = _extract_stages(repro_dir)
    verdict, score = _extract_verdict_and_score(repro_dir)

    run_id = f"{entry_id}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

    return {
        "run_id": run_id,
        "bench_id": entry_id,
        "bench_version": bench_version,
        "verdict": verdict,
        "score": score,
        "stages": stages,
        "duration_seconds": duration,
        "llm_calls": len([s for s in stages if s["status"] != "blocked"]),
        "human_interventions": 0,
    }


def _extract_stages(repro_dir: Path) -> list[dict]:
    """Extract stage statuses from phase output directories."""
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
        "07_package": "README.md",
    }

    stages = []
    for dir_name, phase_name in phase_map.items():
        phase_dir = repro_dir / dir_name
        if not phase_dir.exists():
            stages.append({"name": phase_name, "status": "blocked"})
            continue

        main_file = main_files.get(dir_name)
        if main_file and (phase_dir / main_file).exists():
            content = (phase_dir / main_file).read_text()
            if "BLOCKED" in content[:500] or "FAILED" in content[:500]:
                stages.append({"name": phase_name, "status": "partial"})
            else:
                stages.append({"name": phase_name, "status": "completed"})
        else:
            stages.append({"name": phase_name, "status": "failed"})

    return stages


def _extract_verdict_and_score(repro_dir: Path) -> Tuple[str, int]:
    """Parse verdict and score from 06_validate/report.md."""
    report_path = repro_dir / "06_validate" / "report.md"
    if not report_path.exists():
        return "BLOCKED", 0

    content = report_path.read_text()
    verdict = "BLOCKED"
    score = 0

    # Look for verdict in table rows (e.g., "| REPRODUCED | 85/100 | ...")
    for line in content.split("\n"):
        line_stripped = line.strip()
        if not line_stripped.startswith("|"):
            continue
        if "REPRODUCED" in line_stripped:
            verdict = "REPRODUCED"
        elif "PARTIAL" in line_stripped:
            verdict = "PARTIAL"
        elif "FAILED" in line_stripped:
            verdict = "FAILED"
        elif "BLOCKED" in line_stripped:
            verdict = "BLOCKED"

    # Look for score pattern (e.g., "85/100" or "Score: 85")
    match = re.search(r"(\d+)\s*/\s*100", content)
    if match:
        score = int(match.group(1))
    else:
        match = re.search(r"[Ss]core\s*[:=]\s*(\d+)", content)
        if match:
            score = int(match.group(1))

    return verdict, score


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
        "llm_calls": 0,
        "human_interventions": 0,
        "blocked_reason": reason,
        "error": error,
    }