"""Run one isolated loopflow phase for an internal evaluation case."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).parents[2]
ENTRIES_DIR = ROOT / "benchmarks" / "entries"
FIXTURES_DIR = ROOT / "evals" / "fixtures"


def run_phase(case: dict, output_dir: Path) -> subprocess.CompletedProcess:
    input_dir = ENTRIES_DIR / case["input"]["benchmark"] / "input"
    output_dir.mkdir(parents=True, exist_ok=True)
    for relative, declaration in case.get("upstream", {}).items():
        if isinstance(declaration, dict) and "input" in declaration:
            source = input_dir / declaration["input"]
        else:
            source = FIXTURES_DIR / declaration
        target = output_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)

    override_paper = case["input"].get("override_paper")
    paper = Path(override_paper) if override_paper else input_dir / "paper.pdf"
    if not override_paper and not paper.is_file():
        paper = input_dir / "paper.md"
    args = json.dumps({
        "paper_path": str(paper),
        "output_dir": str(output_dir),
        "language": case.get("language", "en"),
    })
    return subprocess.run(
        [
            "loop", "run", "bio-reproducer", "--args", args,
            "--only-phase", case["phase"],
        ],
        capture_output=True,
        text=True,
    )


def assert_text_checks(content: str, checks: dict) -> None:
    minimum = int(checks.get("min_chars", 0))
    assert len(content) >= minimum, f"Output too short: {len(content)} < {minimum}"
    lowered = content.lower()
    missing = [value for value in checks.get("contains", []) if str(value).lower() not in lowered]
    forbidden = [value for value in checks.get("not_contains", []) if str(value).lower() in lowered]
    unmatched_groups = [
        values for values in checks.get("contains_any", [])
        if not any(str(value).lower() in lowered for value in values)
    ]
    assert not missing, f"Missing expected content: {missing}"
    assert not forbidden, f"Found forbidden content: {forbidden}"
    assert not unmatched_groups, f"None of the alternatives were found: {unmatched_groups}"
