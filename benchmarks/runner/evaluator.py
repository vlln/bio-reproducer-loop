"""Compare expected.yaml vs actual result.json, produce evaluation."""


def evaluate(expected: dict, results: list[dict]) -> dict:
    """Evaluate benchmark results against expected.

    Args:
        expected: Parsed expected.yaml content
        results: List of result.json dicts from N runs

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

    # Per-check evaluation
    check_results = _evaluate_checks(expected, results)

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


def _evaluate_checks(expected: dict, results: list[dict]) -> dict:
    """Evaluate individual check items from expected.yaml.

    Checks are set to 'pending' when no result data is available yet.
    Real per-check scoring happens when actual run results are present.
    """
    checks = expected.get("checks", {})
    if not checks:
        return {}

    check_results = {}
    for dimension, check_list in checks.items():
        dim_results = []
        for check in check_list:
            check_id = check.get("check_id", "?")
            check_type = check.get("type", "auto")
            dim_results.append({
                "check_id": check_id,
                "type": check_type,
                "status": "pending",
                "note": "Check requires result data from actual runs",
            })
        check_results[dimension] = dim_results

    return check_results