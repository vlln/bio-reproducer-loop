"""Evaluate benchmark artifacts against a private oracle."""

from __future__ import annotations

import csv
import importlib.util
import json
import re
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


class EvaluationError(ValueError):
    """A protocol error with a stable public error code."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def evaluate_submission(entry_path: str | Path, submission_path: str | Path) -> dict:
    """Evaluate one submission without trusting any system-provided score."""
    entry_dir = Path(entry_path)
    submission_file = Path(submission_path)
    oracle_dir = entry_dir / "oracle"
    rubric_path = oracle_dir / "rubric.yaml"

    if not rubric_path.is_file():
        raise EvaluationError("INVALID_ORACLE", f"Missing rubric: {rubric_path}")

    try:
        rubric = yaml.safe_load(rubric_path.read_text())
    except yaml.YAMLError as exc:
        raise EvaluationError("INVALID_ORACLE", f"Invalid rubric YAML: {exc}") from exc

    try:
        submission = json.loads(submission_file.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise EvaluationError("INVALID_SUBMISSION", f"Invalid submission: {exc}") from exc

    _validate_protocol(entry_dir, rubric, submission)
    artifacts = _resolve_artifacts(submission_file.parent, submission)

    check_results = []
    total_weight = 0.0
    earned_weight = 0.0
    for check in rubric.get("checks", []):
        weight = float(check.get("weight", 0))
        total_weight += weight
        passed, actual, note = _evaluate_check(check, artifacts, oracle_dir)
        if passed:
            earned_weight += weight
        check_results.append({
            "check_id": check["id"],
            "passed": passed,
            "weight": weight,
            "earned": weight if passed else 0.0,
            "actual": actual,
            "note": note,
        })

    if total_weight <= 0:
        raise EvaluationError("INVALID_ORACLE", "Rubric check weights must total above zero")

    score = round(100 * earned_weight / total_weight, 2)
    verdict = _verdict(score, submission, rubric)
    claimed = submission.get("claimed_verdict")

    return {
        "run_id": submission["submission_id"],
        "bench_id": submission["bench_id"],
        "benchmark_version": str(rubric.get("benchmark_version", "2.0.0")),
        "submission_id": submission["submission_id"],
        "verdict": verdict,
        "score": score,
        "checks": check_results,
        "calibration": {
            "claimed_verdict": claimed,
            "matches": claimed == verdict if claimed is not None else None,
        },
        "provenance": {
            "evaluator_version": "2.0.0",
            "oracle_version": str(rubric.get("oracle_version", "1.0.0")),
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        },
    }


def summarize_evaluations(results: list[dict], rubric: dict) -> dict:
    """Aggregate independently generated results across repeated runs."""
    verdicts = {name: 0 for name in ("REPRODUCED", "PARTIAL", "FAILED", "BLOCKED")}
    for result in results:
        verdict = result.get("verdict", "BLOCKED")
        verdicts[verdict] = verdicts.get(verdict, 0) + 1

    expected = rubric.get("expected_verdict", "REPRODUCED")
    threshold = float(rubric.get("verdict_match_threshold", 0.6))
    total = len(results)
    match_rate = verdicts.get(expected, 0) / total if total else 0.0
    scores = [float(result.get("score", 0)) for result in results]
    return {
        "passed": match_rate >= threshold,
        "verdict_distribution": verdicts,
        "verdict_match_rate": round(match_rate, 2),
        "score_stats": {
            "min": min(scores) if scores else 0,
            "max": max(scores) if scores else 0,
            "mean": round(sum(scores) / len(scores), 2) if scores else 0,
        },
        "total_runs": total,
        "provenance": {"evaluator_version": "2.0.0"},
    }


def _validate_protocol(entry_dir: Path, rubric: Any, submission: Any) -> None:
    if not isinstance(rubric, dict) or not isinstance(rubric.get("checks"), list):
        raise EvaluationError("INVALID_ORACLE", "Rubric must contain a checks list")

    required = {"submission_id", "bench_id", "system", "artifacts", "execution"}
    if not isinstance(submission, dict) or required - submission.keys():
        missing = sorted(required - submission.keys()) if isinstance(submission, dict) else []
        raise EvaluationError("INVALID_SUBMISSION", f"Missing submission fields: {missing}")
    if submission["bench_id"] != entry_dir.name:
        raise EvaluationError("INVALID_SUBMISSION", "Submission bench_id does not match entry")
    if not isinstance(submission["artifacts"], list):
        raise EvaluationError("INVALID_SUBMISSION", "artifacts must be a list")

    seen = set()
    for check in rubric["checks"]:
        if not isinstance(check, dict) or not {"id", "evidence", "comparison", "weight"} <= check.keys():
            raise EvaluationError("INVALID_ORACLE", "Each check needs id, evidence, comparison and weight")
        if check["id"] in seen:
            raise EvaluationError("INVALID_ORACLE", f"Duplicate check id: {check['id']}")
        seen.add(check["id"])


def _resolve_artifacts(root: Path, submission: dict) -> dict[tuple[str, str | None], Path]:
    root = root.resolve()
    resolved = {}
    for artifact in submission["artifacts"]:
        if not isinstance(artifact, dict) or not {"role", "path"} <= artifact.keys():
            raise EvaluationError("INVALID_SUBMISSION", "Each artifact needs role and path")
        relative = Path(artifact["path"])
        if relative.is_absolute():
            raise EvaluationError("INVALID_SUBMISSION", f"Absolute artifact path: {relative}")
        path = (root / relative).resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise EvaluationError("INVALID_SUBMISSION", f"Artifact path escapes submission: {relative}") from exc
        if not path.is_file():
            raise EvaluationError("INVALID_SUBMISSION", f"Artifact does not exist: {relative}")
        key = (str(artifact["role"]), artifact.get("id"))
        if key in resolved:
            raise EvaluationError("INVALID_SUBMISSION", f"Duplicate artifact: {key}")
        resolved[key] = path
    return resolved


def _evaluate_check(check: dict, artifacts: dict, oracle_dir: Path) -> tuple[bool, Any, str]:
    evidence = check["evidence"]
    alternatives = evidence.get("alternatives", [])
    if alternatives:
        failures = []
        for alternative in alternatives:
            candidate = {
                **check,
                "evidence": {
                    key: value
                    for key, value in alternative.items()
                    if key != "comparison"
                },
                "comparison": alternative.get("comparison", check["comparison"]),
            }
            passed, actual, note = _evaluate_check(candidate, artifacts, oracle_dir)
            if passed:
                return True, actual, note
            failures.append(note)
        return False, None, "; ".join(failures)

    role = evidence.get("artifact_role")
    artifact_id = evidence.get("artifact_id")
    path = artifacts.get((role, artifact_id))
    if path is None and artifact_id is None:
        matches = [value for (item_role, _), value in artifacts.items() if item_role == role]
        path = matches[0] if len(matches) == 1 else None
    if path is None:
        return False, None, f"Artifact not submitted: role={role}, id={artifact_id}"

    comparison = check["comparison"]
    comparator = comparison.get("comparator")
    try:
        if comparator == "file_nonempty":
            actual = path.stat().st_size
            return actual > 0, actual, "file size in bytes"
        if comparator == "png_valid":
            with path.open("rb") as handle:
                header = handle.read(24)
            if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
                return False, None, "invalid PNG header"
            width, height = struct.unpack(">II", header[16:24])
            passed = width >= int(comparison.get("min_width", 1)) and height >= int(comparison.get("min_height", 1))
            return passed, {"width": width, "height": height}, "PNG dimensions"
        if comparator == "csv_shape":
            header, rows = _read_csv(path)
            actual = {"rows": len(rows), "columns": len(header)}
            passed = len(rows) == int(comparison["rows"]) and len(header) == int(comparison["columns"])
            return passed, actual, "CSV shape"
        if comparator == "csv_row":
            header, rows = _read_csv(path)
            row = _find_row(header, rows, comparison)
            if row is None:
                return False, None, "CSV row not found"
            assertions = comparison.get("assertions", [])
            values = [(_row_value(row, rule), rule) for rule in assertions]
            passed = all(_compare(value, rule) for value, rule in values)
            actual = {
                str(rule.get("column", rule.get("columns"))): value
                for value, rule in values
            }
            return passed, actual, "CSV row assertions"
        if comparator == "csv_rows":
            header, rows = _read_csv(path)
            actual = {}
            passed = True
            base = {"key_columns": comparison.get("key_columns", [header[0]])}
            for expected_row in comparison.get("rows", []):
                row_comparison = {**base, "key_equals": expected_row["key_equals"]}
                row = _find_row(header, rows, row_comparison)
                if row is None:
                    actual[expected_row["key_equals"]] = None
                    passed = False
                    continue
                values = [(_row_value(row, rule), rule) for rule in expected_row.get("assertions", [])]
                row_passed = all(_compare(value, rule) for value, rule in values)
                actual[expected_row["key_equals"]] = {
                    str(rule.get("column", rule.get("columns"))): value
                    for value, rule in values
                }
                passed = passed and row_passed
            return passed, actual, "CSV multi-row assertions"
        if comparator == "csv_count":
            _, rows = _read_csv(path)
            count = sum(
                1 for row in rows
                if all(_compare(_row_value(row, rule), rule) for rule in comparison.get("where", []))
            )
            passed = _compare(count, comparison["assertion"])
            return passed, count, "matching CSV rows"
        if comparator == "csv_set_overlap":
            _, rows = _read_csv(path)
            columns = comparison.get("columns", [comparison.get("column")])
            column = next((candidate for candidate in columns if rows and candidate in rows[0]), None)
            if column is None:
                return False, None, "set column not found"
            actual_set = {row[column] for row in rows if row.get(column)}
            expected_set = {str(value) for value in comparison.get("expected", [])}
            overlap = actual_set & expected_set
            recall = len(overlap) / len(expected_set) if expected_set else 1.0
            union = actual_set | expected_set
            jaccard = len(overlap) / len(union) if union else 1.0
            passed = recall >= float(comparison.get("min_recall", 0)) and jaccard >= float(comparison.get("min_jaccard", 0))
            return passed, {"overlap": sorted(overlap), "recall": round(recall, 4), "jaccard": round(jaccard, 4)}, "set overlap"
        if comparator == "text_regex":
            matched = re.search(str(comparison["pattern"]), path.read_text(), re.MULTILINE) is not None
            return matched, matched, "regular expression match"
        if comparator == "python_verify":
            return _run_python_verifier(oracle_dir, path, comparison)
    except EvaluationError:
        raise
    except (KeyError, TypeError, ValueError, csv.Error) as exc:
        return False, None, f"Comparator error: {exc}"
    raise EvaluationError("INVALID_ORACLE", f"Unknown comparator: {comparator}")


def _run_python_verifier(oracle_dir: Path, artifact: Path, comparison: dict) -> tuple[bool, Any, str]:
    module_path = (oracle_dir / comparison.get("module", "verify.py")).resolve()
    try:
        module_path.relative_to(oracle_dir.resolve())
    except ValueError as exc:
        raise EvaluationError("INVALID_ORACLE", "Verifier path escapes oracle") from exc
    if not module_path.is_file():
        raise EvaluationError("INVALID_ORACLE", f"Verifier not found: {module_path}")

    spec = importlib.util.spec_from_file_location(f"benchmark_verifier_{id(module_path)}", module_path)
    if spec is None or spec.loader is None:
        raise EvaluationError("INVALID_ORACLE", f"Cannot load verifier: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    function = getattr(module, comparison.get("function", "verify"), None)
    if not callable(function):
        raise EvaluationError("INVALID_ORACLE", "Verifier function is not callable")
    result = function(artifact, comparison.get("config", {}))
    if not isinstance(result, dict) or "passed" not in result:
        raise EvaluationError("INVALID_ORACLE", "Verifier must return a dict containing passed")
    return bool(result["passed"]), result.get("actual"), str(result.get("note", "custom verifier"))


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("CSV has no header")
        return reader.fieldnames, list(reader)


def _find_row(header: list[str], rows: list[dict[str, str]], comparison: dict) -> dict | None:
    candidates = comparison.get("key_columns", [comparison.get("key_column", header[0])])
    key = next((candidate for candidate in candidates if candidate in header), None)
    if key is None:
        return None
    expected = str(comparison["key_equals"])
    filters = comparison.get("where", [])
    return next((
        row for row in rows
        if row.get(key) == expected
        and all(_compare(_row_value(row, rule), rule) for rule in filters)
    ), None)


def _row_value(row: dict[str, str], rule: dict) -> str | None:
    candidates = rule.get("columns", [rule.get("column")])
    return next((row[column] for column in candidates if column in row), None)


def _compare(actual: Any, rule: dict) -> bool:
    operator = rule.get("operator", "equals")
    expected = rule.get("value")
    if operator == "matches":
        return re.search(str(expected), str(actual)) is not None
    if operator == "equals":
        return str(actual).lower() == str(expected).lower()

    actual_number = float(actual)
    expected_number = float(expected)
    if operator == "absolute_less_than":
        return abs(actual_number) < expected_number
    return {
        "less_than": actual_number < expected_number,
        "less_than_or_equal": actual_number <= expected_number,
        "greater_than": actual_number > expected_number,
        "greater_than_or_equal": actual_number >= expected_number,
    }.get(operator, False)


def _verdict(score: float, submission: dict, rubric: dict) -> str:
    execution = submission.get("execution", {})
    if execution.get("blocked_reason") and not submission.get("artifacts"):
        return "BLOCKED"
    thresholds = rubric.get("verdict_thresholds", {})
    if score >= float(thresholds.get("reproduced", 85)):
        return "REPRODUCED"
    if score >= float(thresholds.get("partial", 50)):
        return "PARTIAL"
    return "FAILED"
