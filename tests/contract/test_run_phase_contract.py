"""Run phase 产物契约 + routing.jsonl 契约测试（ADR-0011 §2/§3，单元 03）。

- 05_run 结果契约：results/ CSV 非空 + answers.csv 表头白名单（FC-003）
- routing.jsonl 键名白名单（FC-003）：ts/target/decision/route_to/reason
- answers 的「值可定位」交叉核对（FC-005）由单元 04 evaluator 实现，本文件不覆盖
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).parents[2]

spec = importlib.util.spec_from_file_location(
    "bio_reproducer_artifact_checks",
    ROOT / "loops" / "bio-reproducer" / "artifact_checks.py",
)
ac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ac)


# ── answers 表头白名单 ──────────────────────────────────────────────
def _write_answers(base, content):
    (base / "05_run").mkdir(parents=True, exist_ok=True)
    (base / "05_run" / "answers.csv").write_text(content)


def test_answers_parseable_accepts_full_header(tmp_path):
    _write_answers(tmp_path, "target_id,value,unit,source_file\nT1,1.63,HR,results/t1.csv\n")
    assert ac.answers_parseable(tmp_path / "05_run" / "answers.csv") is True


def test_answers_parseable_rejects_missing_columns(tmp_path):
    _write_answers(tmp_path, "id,val,unit,file\nT1,1.63,HR,f.csv\n")
    assert ac.answers_parseable(tmp_path / "05_run" / "answers.csv") is False


def test_answers_parseable_rejects_extra_judgment_columns(tmp_path):
    # FC-003：不得含状态词/判断/理由列
    _write_answers(tmp_path, "target_id,value,unit,source_file,status,reason\nT1,1.63,HR,f.csv,ok,because\n")
    assert ac.answers_parseable(tmp_path / "05_run" / "answers.csv") is False


def test_answers_parseable_missing_file(tmp_path):
    assert ac.answers_parseable(tmp_path / "05_run" / "answers.csv") is False


# ── check_run_phase：存在 + 可被标准工具解析 ─────────────────────────
def test_check_run_phase_ok(tmp_path):
    results = tmp_path / "05_run" / "results"
    results.mkdir(parents=True)
    (results / "table2.csv").write_text("g,hr\nA,1.63\n")
    (tmp_path / "05_run" / "answers.csv").write_text("target_id,value,unit,source_file\nT1,1.63,HR,results/table2.csv\n")
    ok, detail = ac.check_run_phase(tmp_path)
    assert ok is True
    assert "answers 表头合规" in detail


def test_check_run_phase_missing_dir(tmp_path):
    ok, detail = ac.check_run_phase(tmp_path)
    assert ok is False
    assert "05_run" in detail


def test_check_run_phase_no_results(tmp_path):
    (tmp_path / "05_run").mkdir()
    (tmp_path / "05_run" / "answers.csv").write_text("target_id,value,unit,source_file\n")
    ok, detail = ac.check_run_phase(tmp_path)
    assert ok is False
    assert "无任何非空 CSV/TSV" in detail


def test_check_run_phase_empty_csv_ignored(tmp_path):
    results = tmp_path / "05_run" / "results"
    results.mkdir(parents=True)
    (results / "empty.csv").write_text("")  # 空文件不算证据
    (tmp_path / "05_run" / "answers.csv").write_text("target_id,value,unit,source_file\n")
    ok, detail = ac.check_run_phase(tmp_path)
    assert ok is False
    assert "无任何非空 CSV/TSV" in detail


def test_check_run_phase_missing_answers(tmp_path):
    results = tmp_path / "05_run" / "results"
    results.mkdir(parents=True)
    (results / "table2.csv").write_text("g,hr\nA,1.63\n")
    ok, detail = ac.check_run_phase(tmp_path)
    assert ok is False
    assert "answers.csv" in detail


# ── answers target_id 与公开问题清单键对齐（ADR-0011 §4.1，0026 验收补）──
def _write_questions(base, keys):
    (base / "input").mkdir(parents=True, exist_ok=True)
    import yaml
    (base / "input" / "questions.yaml").write_text(yaml.safe_dump({
        "schema": "questions/v1",
        "questions": [{"target_id": k, "question": f"Q {k}", "unit": "value"} for k in keys],
    }))


def _write_run_with_answers(base, target_ids):
    results = base / "05_run" / "results"
    results.mkdir(parents=True)
    (results / "table2.csv").write_text("g,hr\nA,1.63\n")
    rows = "\n".join(f"{t},1.63,HR,results/table2.csv" for t in target_ids)
    (base / "05_run" / "answers.csv").write_text(
        f"target_id,value,unit,source_file\n{rows}\n")


def test_check_run_phase_answers_aligned_with_questions(tmp_path):
    _write_questions(tmp_path, ["blood-lead-cvd-hr", "tibia-lead-cvd-hr"])
    _write_run_with_answers(tmp_path, ["blood-lead-cvd-hr", "tibia-lead-cvd-hr"])
    ok, detail = ac.check_run_phase(tmp_path)
    assert ok is True
    assert "target_id 对齐问题清单" in detail


def test_check_run_phase_answers_stray_target_id_rejected(tmp_path):
    # 用 plan.md 内部 T 编号而非问题清单键 → 拦截（2026-08-27 端到端实证）
    _write_questions(tmp_path, ["blood-lead-cvd-hr", "tibia-lead-cvd-hr"])
    _write_run_with_answers(tmp_path, ["T1", "T2"])
    ok, detail = ac.check_run_phase(tmp_path)
    assert ok is False
    assert "target_id" in detail and "问题清单" in detail


def test_check_run_phase_no_questions_skips_alignment(tmp_path):
    # 无 input/questions.yaml 时（旧入口/无公开问题场景）不强制对齐
    results = tmp_path / "05_run" / "results"
    results.mkdir(parents=True)
    (results / "table2.csv").write_text("g,hr\nA,1.63\n")
    (tmp_path / "05_run" / "answers.csv").write_text(
        "target_id,value,unit,source_file\nT1,1.63,HR,results/table2.csv\n")
    ok, detail = ac.check_run_phase(tmp_path)
    assert ok is True


# ── routing.jsonl 键名白名单（FC-003）───────────────────────────────
def test_routing_events_ok_accepts_whitelist():
    events = [
        {"ts": "t1", "target": "T1", "decision": "deviation", "route_to": "run", "reason": "x"},
        {"ts": "t2", "target": "T2", "decision": "reproduced", "route_to": None, "reason": ""},
    ]
    assert ac.routing_events_ok(events) is True


def test_routing_events_ok_rejects_extra_keys():
    events = [{"ts": "t", "target": "T1", "decision": "deviation", "route_to": "run",
               "reason": "x", "score": 0.5}]
    assert ac.routing_events_ok(events) is False


def test_routing_events_ok_rejects_missing_keys():
    events = [{"ts": "t", "target": "T1", "route_to": "run"}]  # 缺 decision/reason
    assert ac.routing_events_ok(events) is False


def test_routing_events_ok_rejects_non_dict():
    assert ac.routing_events_ok(["not-json-object"]) is False
    assert ac.routing_events_ok([]) is True  # 无事件 = 无路由 = 合法
