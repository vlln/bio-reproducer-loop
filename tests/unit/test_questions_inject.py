"""questions_inject（评测方注入段生成）测试。

验证：公开问题清单 → 任务注入段 + 键列表；无清单 → (None, [])。
系统侧（agents/workflow/lint）不读文件——本模块是评测方唯一接触
questions.yaml 的地方（2026-08-27 分层讨论落地）。
"""

from pathlib import Path

import yaml

from benchmarks.harness.questions_inject import (
    build_questions_injection,
    load_question_targets,
)


def _write_questions(input_dir: Path, questions: list[dict]) -> None:
    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "questions.yaml").write_text(yaml.safe_dump(
        {"schema": "questions/v1", "questions": questions}))


def test_no_questions_file_returns_empty(tmp_path):
    (tmp_path / "empty").mkdir(parents=True)
    assert build_questions_injection(tmp_path / "empty") == (None, [])
    assert load_question_targets(tmp_path / "empty") == []


def test_missing_dir_returns_empty(tmp_path):
    assert build_questions_injection(tmp_path / "nope") == (None, [])


def test_questions_file_generates_injection_and_keys(tmp_path):
    _write_questions(tmp_path, [
        {"target_id": "blood-lead-cvd-hr", "question": "复现论文报告的 Blood lead CVD HR 数值", "unit": "value"},
        {"target_id": "tibia-lead-cvd-hr", "question": "复现 Tibia lead CVD HR 数值", "unit": "value"},
    ])
    injection, keys = build_questions_injection(tmp_path)
    assert keys == ["blood-lead-cvd-hr", "tibia-lead-cvd-hr"]
    assert injection is not None
    assert "blood-lead-cvd-hr" in injection
    assert "tibia-lead-cvd-hr" in injection
    assert "复现论文报告的 Blood lead CVD HR 数值" in injection
    assert "任务公开问题清单" in injection


def test_empty_questions_list_returns_none(tmp_path):
    _write_questions(tmp_path, [])
    assert build_questions_injection(tmp_path) == (None, [])


def test_injection_preserves_key_order(tmp_path):
    _write_questions(tmp_path, [
        {"target_id": "b-key", "question": "Q b", "unit": "v"},
        {"target_id": "a-key", "question": "Q a", "unit": "v"},
    ])
    injection, keys = build_questions_injection(tmp_path)
    assert keys == ["b-key", "a-key"]  # 文件顺序，不排序（转录必须逐字保序）


def test_invalid_yaml_returns_empty(tmp_path):
    (tmp_path / "input").mkdir(parents=True, exist_ok=True)
    (tmp_path / "input" / "questions.yaml").write_text("::: not yaml [[[")
    assert build_questions_injection(tmp_path / "input") == (None, [])
