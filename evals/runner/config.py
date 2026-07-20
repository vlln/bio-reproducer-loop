"""Load internal evaluation cases and execution profiles."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


EVALS_DIR = Path(__file__).parents[1]
CASES_DIR = EVALS_DIR / "cases"


def load_profiles() -> dict[str, dict[str, Any]]:
    data = yaml.safe_load((EVALS_DIR / "profiles.yaml").read_text())
    return data["profiles"]


def profile_runs(profile: str) -> int:
    profiles = load_profiles()
    if profile not in profiles:
        raise ValueError(f"Unknown eval profile: {profile}")
    return int(profiles[profile]["runs"])


def load_cases() -> dict[str, dict[str, Any]]:
    cases = {}
    for path in sorted(CASES_DIR.glob("**/case.yaml")):
        case = yaml.safe_load(path.read_text())
        case_id = case["id"]
        if case_id in cases:
            raise ValueError(f"Duplicate eval case id: {case_id}")
        case["_path"] = str(path)
        cases[case_id] = case
    return cases


def load_case(case_id: str) -> dict[str, Any]:
    cases = load_cases()
    if case_id not in cases:
        raise KeyError(f"Unknown eval case: {case_id}")
    return cases[case_id]


def write_evaluation_result(
    output_root: Path,
    profile: str,
    outcomes: list[dict[str, Any]],
) -> Path:
    """Write raw case outcomes and a small distribution summary."""
    now = datetime.now(timezone.utc)
    run_id = now.strftime("%Y%m%dT%H%M%S%fZ")
    output_dir = output_root / run_id
    output_dir.mkdir(parents=True, exist_ok=False)

    by_case: dict[str, dict[str, Any]] = {}
    for outcome in outcomes:
        counts = by_case.setdefault(
            outcome["case_id"],
            {"attempts": 0, "passed": 0, "failed": 0, "pass_rate": 0.0},
        )
        counts["attempts"] += 1
        counts[outcome["outcome"]] = counts.get(outcome["outcome"], 0) + 1
    for counts in by_case.values():
        counts["pass_rate"] = round(counts["passed"] / counts["attempts"], 4)

    result = {
        "eval_run_id": run_id,
        "profile": profile,
        "recorded_at": now.isoformat(),
        "system": {
            "name": "bio-reproducer",
            "model": os.environ.get("BIO_REPRODUCER_MODEL", "unknown"),
            "prompt_version": os.environ.get("BIO_REPRODUCER_PROMPT_VERSION", "unknown"),
            "tool_environment": os.environ.get("BIO_REPRODUCER_TOOL_ENV", "unknown"),
        },
        "cases": by_case,
        "attempts": outcomes,
    }
    path = output_dir / "evaluation.json"
    path.write_text(json.dumps(result, indent=2))
    return path
