"""Run a single benchmark entry N times, collect results."""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from .adapters.loopflow import run as loopflow_run
from .bundle_validator import validate_entry

def run_entry(entry_path: str, runs: int = 5, output_dir: Optional[str] = None) -> list:
    """Run a protocol v2 benchmark entry N times and return submissions.

    Args:
        entry_path: Path to benchmark entry directory
        runs: Number of runs (default 5 for L3)
        output_dir: Where to store results (defaults to benchmarks/results/<entry_id>/)

    Returns:
        List of result.json dicts, one per completed run.
    """
    entry_dir = Path(entry_path)
    validate_entry(entry_dir)
    entry_id = entry_dir.name
    if output_dir is None:
        results_root = Path(__file__).parent.parent / "results"
    else:
        results_root = Path(output_dir)
    entry_results_dir = results_root / entry_id
    entry_results_dir.mkdir(parents=True, exist_ok=True)

    all_results = []

    for i in range(1, runs + 1):
        run_dir = entry_results_dir / f"run_{i:02d}"
        result_file = run_dir / "submission.json"

        # Skip already-completed runs (AC-0004-B-2)
        if result_file.exists():
            with open(result_file) as f:
                all_results.append(json.load(f))
            continue

        run_dir.mkdir(parents=True, exist_ok=True)

        try:
            result = loopflow_run(entry_path, run_dir=str(run_dir))
        except Exception as e:
            result = _make_error_submission(entry_id, i, str(e))

        with open(result_file, "w") as f:
            json.dump(result, f, indent=2)

        all_results.append(result)

    return all_results


def _make_error_submission(entry_id: str, run_num: int, error: str) -> dict:
    submission_id = f"{entry_id}-run-{run_num:02d}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    return {
        "submission_id": submission_id,
        "bench_id": entry_id,
        "system": {"name": "bio-reproducer", "version": "0.1.0"},
        "artifacts": [],
        "execution": {
            "duration_seconds": 0,
            "stages": [],
            "blocked_reason": "system",
            "error": error,
        },
    }
