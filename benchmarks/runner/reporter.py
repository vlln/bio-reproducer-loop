"""Generate benchmark reports (summary.json)."""

from datetime import datetime, timezone


def generate_summary(results_by_entry: dict) -> dict:
    """Generate summary.json from evaluation results.

    Args:
        results_by_entry: Dict of entry_id -> evaluation dict

    Returns:
        Summary dict following the report schema.
    """
    entries = []
    total_passed = 0
    total_entries = 0

    for entry_id, evaluation in results_by_entry.items():
        total_entries += 1
        passed = evaluation.get("passed", False)
        if passed:
            total_passed += 1

        entries.append({
            "entry_id": entry_id,
            "passed": passed,
            "verdict_distribution": evaluation.get("verdict_distribution", {}),
            "verdict_match_rate": evaluation.get("verdict_match_rate", 0),
            "score_stats": evaluation.get("score_stats", {}),
            "notes": evaluation.get("notes", []),
            "total_runs": evaluation.get("total_runs", 0),
        })

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_entries": total_entries,
            "passed_entries": total_passed,
            "pass_rate": round(total_passed / total_entries, 2) if total_entries > 0 else 0,
        },
        "entries": entries,
    }