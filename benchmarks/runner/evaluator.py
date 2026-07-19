"""Compare expected.yaml vs actual result.json, produce evaluation."""

import json
from pathlib import Path


def evaluate(expected: dict, results: list[dict], results_dir: str | None = None) -> dict:
    """Evaluate benchmark results against expected.

    Args:
        expected: Parsed expected.yaml content
        results: List of result.json dicts from N runs
        results_dir: Path to results directory (e.g., benchmarks/results/bench-001/)

    Returns:
        dict with: passed, verdict_distribution, verdict_match_rate,
                   score_stats, notes
    """
    expected_verdict = expected.get("expected_verdict", "REPRODUCED")
    match_threshold = expected.get("verdict_match_threshold", 0.6)

    # Count verdicts
    verdict_counts = {"REPRODUCED": 0, "PARTIAL": 0, "FAILED": 0, "BLOCKED": 0}
    scores = []
    for r in results:
        v = r.get("verdict", "BLOCKED")
        verdict_counts[v] = verdict_counts.get(v, 0) + 1
        scores.append(r.get("score", 0))

    total = len(results)
    verdict_match_rate = verdict_counts.get(expected_verdict, 0) / total if total > 0 else 0
    passed = verdict_match_rate >= match_threshold

    # Score statistics
    score_stats = {
        "min": min(scores) if scores else 0,
        "max": max(scores) if scores else 0,
        "mean": round(sum(scores) / len(scores), 1) if scores else 0,
        "median": _median(scores) if scores else 0,
    }

    # Per-check evaluation — read actual run data from repro-data
    check_results = _evaluate_checks(expected, results_dir)

    notes = []
    if not passed:
        notes.append(
            f"Verdict match rate {verdict_match_rate:.0%} below threshold {match_threshold:.0%}"
        )
    blocked_system = sum(1 for r in results if r.get("blocked_reason") == "system")
    if blocked_system > 0:
        notes.append(f"{blocked_system}/{total} runs blocked due to system errors")

    return {
        "passed": passed,
        "verdict_distribution": verdict_counts,
        "verdict_match_rate": round(verdict_match_rate, 2),
        "score_stats": score_stats,
        "check_results": check_results,
        "notes": notes,
        "total_runs": total,
    }


def _median(values: list) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mid = n // 2
    if n % 2 == 0:
        return round((sorted_vals[mid - 1] + sorted_vals[mid]) / 2, 1)
    return round(sorted_vals[mid], 1)


def _evaluate_checks(expected: dict, results_dir: str | None) -> dict:
    """Evaluate individual check items from expected.yaml against actual run results.

    Reads the Validate agent's metrics.json from each run's repro-data directory.
    Handles two formats from the Validate agent:
      - Format 1 (flat): dimension_scores + deviations (no per-check scores)
      - Format 2 (nested): per-check {score, actual, ...} within each dimension
    """
    checks = expected.get("checks", {})
    if not checks:
        return {}

    # Collect check data from all runs
    run_metrics = _collect_run_metrics(results_dir)

    check_results = {}
    for dimension, check_list in checks.items():
        dim_results = []
        for check in check_list:
            check_id = check.get("check_id", "?")
            check_type = check.get("type", "auto")

            if not run_metrics:
                dim_results.append({
                    "check_id": check_id,
                    "type": check_type,
                    "status": "pending",
                    "note": "No run data available",
                })
                continue

            # Try per-check scoring (Format 2: top-level dimension dicts)
            # Also try Format 1b: dimension_scores → {dimension: {checks: {check_id: {score}}}}
            scores = []
            for metrics in run_metrics.values():
                # Format 2: top-level dimension key
                dim_data = metrics.get(dimension, {})
                if isinstance(dim_data, dict):
                    check_data = dim_data.get(check_id, {})
                    if isinstance(check_data, dict):
                        s = check_data.get("score")
                        if isinstance(s, (int, float)):
                            scores.append(s)
                            continue

                # Format 1b: dimension_scores → {dimension: {checks: {check_id: {score}}}}
                ds = metrics.get("dimension_scores", {})
                if isinstance(ds, dict):
                    dim_entry = ds.get(dimension, {})
                    if isinstance(dim_entry, dict):
                        checks = dim_entry.get("checks", {})
                        if isinstance(checks, dict):
                            check_data = checks.get(check_id, {})
                            if isinstance(check_data, dict):
                                s = check_data.get("score")
                                if isinstance(s, (int, float)):
                                    scores.append(s)

            if scores:
                avg_score = round(sum(scores) / len(scores), 2)
                dim_results.append({
                    "check_id": check_id,
                    "type": check_type,
                    "status": _score_status(avg_score),
                    "average_score": avg_score,
                    "runs_scored": len(scores),
                    "note": _check_note(check_id, avg_score, scores),
                })
                continue

            # Fall back to dimension-level summary (Format 1)
            dim_scores = []
            for metrics in run_metrics.values():
                ds = metrics.get("dimension_scores", {})
                if isinstance(ds, dict):
                    # Format 1a: {"dimension": float}
                    # Format 1b: {"dimension": {"score": float, "checks": {...}}}
                    s = ds.get(dimension)
                    if isinstance(s, (int, float)):
                        dim_scores.append(s)
                    elif isinstance(s, dict):
                        score_val = s.get("score")
                        if isinstance(score_val, (int, float)):
                            dim_scores.append(score_val)

            if dim_scores:
                avg_dim = round(sum(dim_scores) / len(dim_scores), 2)
                # Normalize: dimension score is out of its weight, convert to 0-1
                max_score = _get_dimension_max(dimension, expected)
                normalized = round(avg_dim / max_score, 2) if max_score > 0 else avg_dim
                dim_results.append({
                    "check_id": check_id,
                    "type": check_type,
                    "status": _score_status(normalized),
                    "dimension_average": avg_dim,
                    "dimension_max": max_score,
                    "runs_scored": len(dim_scores),
                    "note": f"Dimension-level score: {avg_dim}/{max_score} across {len(dim_scores)} runs",
                })
                continue

            dim_results.append({
                "check_id": check_id,
                "type": check_type,
                "status": "pending",
                "note": f"No scoring data for {check_id}",
            })

        check_results[dimension] = dim_results

    return check_results


def _score_status(avg_score: float) -> str:
    if avg_score >= 0.8:
        return "pass"
    elif avg_score >= 0.5:
        return "partial"
    return "fail"


def _check_note(check_id: str, avg: float, scores: list[float]) -> str:
    n = len(scores)
    if n <= 1:
        return f"score={avg:.2f}"
    return f"avg={avg:.2f} across {n} runs (min={min(scores):.2f}, max={max(scores):.2f})"


def _get_dimension_max(dimension: str, expected: dict) -> float:
    """Get the max score for a dimension from evaluation_design."""
    design = expected.get("evaluation_design", {})
    dims = design.get("dimensions", {})
    dim_config = dims.get(dimension, {})
    return float(dim_config.get("weight", 25))


def _collect_run_metrics(results_dir: str | None) -> dict:
    """Collect metrics.json from all run directories.

    Returns:
        dict mapping run_id -> metrics dict
    """
    if not results_dir:
        return {}

    results_path = Path(results_dir)
    run_metrics = {}

    for run_dir in sorted(results_path.glob("run_*")):
        metrics_path = run_dir / "repro-data" / "06_validate" / "metrics.json"
        if not metrics_path.exists():
            continue

        with open(metrics_path) as f:
            try:
                metrics = json.load(f)
            except json.JSONDecodeError:
                continue

        run_metrics[run_dir.name] = metrics

    return run_metrics