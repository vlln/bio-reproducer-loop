"""证据面切换契约测试（ADR-0011 §4/§5，单元 04）。

- verify 模板：check_claim（answers + 交叉核对）/ check_data_references（04_data
  日志终态）/ check_code_references（digests）
- evaluator：NO-EVIDENCE 三态（不计分不扣分，FC-005）
- check_provision_phase（digests 契约）
- 端到端：bench-220 的 answers 样例经 evaluator 评分（完成判据 3 雏形）
"""
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
ENTRY = ROOT / "benchmarks" / "entries" / "bench-220"


def _load_verify(entry_dir):
    spec = importlib.util.spec_from_file_location("entry_verify", entry_dir / "oracle" / "verify.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── check_claim：answers + 交叉核对（FC-005）──────────────────────────
def _write_answers(base, content):
    p = base / "answers.csv"
    p.write_text("target_id,value,unit,source_file\n" + content)
    return p


def test_check_claim_crosscheck_hit(tmp_path):
    mod = _load_verify(ENTRY)
    results = tmp_path / "results"
    results.mkdir()
    # bench-220 真实样例：table2_q91_results.csv 的 HR 值（ADR-0011 验证 1）
    (results / "table2.csv").write_text(
        "group,outcome,exposure,hr,lower_ci,upper_ci,p_value\n"
        "all,death,blood,1.63390378426855,1.28,2.08,0.0002\n"
        "all,death,tibia,3.32464221876738,2.31,4.78,0.0001\n"
        "all,death,patella,2.42303481511462,1.72,3.41,0.0003\n"
    )
    answers = _write_answers(tmp_path, (
        "blood-lead-cvd-hr,1.63390378426855,value,results/table2.csv\n"
        "tibia-lead-cvd-hr,3.32464221876738,value,results/table2.csv\n"
        "patella-lead-cvd-hr,2.42303481511462,value,results/table2.csv\n"
    ))
    for claim_id in ("C1", "C2", "C3"):
        r = mod.check_claim(str(answers), {"claim_id": claim_id})
        assert r["passed"], f"{claim_id}: {r['note']}"


def test_check_claim_no_evidence_when_value_not_located(tmp_path):
    """值真实但标错 source_file（或文件中无该值）→ NO-EVIDENCE 不计分。"""
    mod = _load_verify(ENTRY)
    results = tmp_path / "results"
    results.mkdir()
    (results / "other.csv").write_text("x,1.0\n")
    answers = _write_answers(tmp_path, "blood-lead-cvd-hr,1.63390378426855,value,results/other.csv\n")
    r = mod.check_claim(str(answers), {"claim_id": "C1"})
    assert not r["passed"]
    assert r.get("no_evidence") is True


def test_check_claim_no_evidence_when_target_missing(tmp_path):
    mod = _load_verify(ENTRY)
    answers = _write_answers(tmp_path, "other-target,1.63,value,results/x.csv\n")
    r = mod.check_claim(str(answers), {"claim_id": "C1"})
    assert not r["passed"]
    assert r.get("no_evidence") is True


def test_check_claim_violation_when_out_of_tolerance(tmp_path):
    mod = _load_verify(ENTRY)
    results = tmp_path / "results"
    results.mkdir()
    (results / "table2.csv").write_text("hr\n2.5\n")
    answers = _write_answers(tmp_path, "blood-lead-cvd-hr,2.5,value,results/table2.csv\n")
    r = mod.check_claim(str(answers), {"claim_id": "C1"})
    assert not r["passed"]
    assert r.get("no_evidence") is None  # 判错（VIOLATED），不是无证据


# ── check_data_references：04_data 日志终态推导（A1）───────────────────
def _entry_with_gse_claim(tmp_path):
    """拷贝 bench-220 并注入 GSE accession 的 data_references（推导测试用）。"""
    import yaml

    entry = tmp_path / "bench-gse"
    shutil.copytree(ENTRY, entry)
    claims = yaml.safe_load((entry / "oracle" / "claims.yaml").read_text())
    claims["data_references"] = [
        {"accession": "GSE289881", "repository": "GEO", "is_primary": True,
         "downloadable": "true", "notes": "test"},
        {"accession": "GSE136831", "repository": "GEO", "is_primary": False,
         "downloadable": "true", "notes": "test"},
    ]
    (entry / "oracle" / "claims.yaml").write_text(yaml.safe_dump(claims, sort_keys=False))
    return _load_verify(entry)


def test_check_data_references_from_logs(tmp_path):
    mod = _entry_with_gse_claim(tmp_path)
    data = tmp_path / "04_data"
    data.mkdir()
    (data / "p4_gse289881.log").write_text(
        "Download complete: GSE289881_RAW.tar (628.6 MB)\nGSE289881 complete\n")
    (data / "p4_gse136831.log").write_text(
        "curl: (35) Recv failure: Connection reset by peer\nbash: wget: command not found\n")
    artifact = data / "sha256sums.txt"
    artifact.write_text("0" * 64 + "  GSE289881_RAW.tar\n")
    r = mod.check_data_references(str(artifact), {})
    # GSE289881 completed（通过）；GSE136831 not_attempted（ground truth 可下载 → 失败）
    assert not r["passed"]
    assert r["actual"] is not None
    states = {a["accession"]: a["system"] for a in r["actual"]}
    assert states["gse289881"] == "completed"
    assert states["gse136831"] == "not_attempted"

    good = tmp_path / "04_data_good"
    good.mkdir()
    (good / "p4_gse289881.log").write_text(
        "Download complete: GSE289881_RAW.tar (628.6 MB)\nGSE289881 complete\n")
    (good / "p4_gse136831.log").write_text(
        "Download complete: GSE136831 (1.2 GB)\nGSE136831 complete\n")
    (good / "sha256sums.txt").write_text("0" * 64 + "  GSE289881_RAW.tar\n")
    r2 = mod.check_data_references(str(good / "sha256sums.txt"), {})
    assert r2["passed"]


# ── check_code_references：digests 推导（A2）──────────────────────────
def test_check_code_references_from_digests(tmp_path):
    mod = _load_verify(ENTRY)
    digests = tmp_path / "digests.txt"
    digests.write_text("REPOSITORY TAG DIGEST\nbio/x latest sha256:" + "a" * 64 + "\n")
    r = mod.check_code_references(str(digests), {})
    assert r["passed"]

    r2 = mod.check_code_references(str(tmp_path / "missing.txt"), {})
    assert not r2["passed"] and r2.get("no_evidence")


# ── evaluator：NO-EVIDENCE 三态（FC-005）──────────────────────────────
def test_evaluator_no_evidence_excludes_weight(tmp_path):
    from benchmarks.runner.independent_evaluator import evaluate_submission

    entry = tmp_path / "bench-e"
    shutil.copytree(ENTRY, entry)
    # 只保留 C1 claim 的 rubric（其他 check 删掉，聚焦三态）
    rubric = json.loads(entry.joinpath("oracle", "rubric.yaml").read_text()) if False else None
    import yaml

    rub = yaml.safe_load((entry / "oracle" / "rubric.yaml").read_text())
    rub["checks"] = [c for c in rub["checks"] if c["id"] == "C1"]
    (entry / "oracle" / "rubric.yaml").write_text(yaml.safe_dump(rub, sort_keys=False))

    sub = tmp_path / "submission.json"
    results = tmp_path / "results"
    results.mkdir()
    (results / "table2.csv").write_text("hr\n1.63390378426855\n")

    # 有证据且通过 → C1 计分（权重 70）
    (tmp_path / "answers.csv").write_text(
        "target_id,value,unit,source_file\nblood-lead-cvd-hr,1.63390378426855,value,results/table2.csv\n")
    sub.write_text(json.dumps({
        "protocol_version": "2.0", "submission_id": "s1", "bench_id": "bench-e",
        "system": {"name": "x", "version": "0"},
        "claimed_verdict": "REPRODUCED",
        "artifacts": [{"role": "answers", "path": "answers.csv"}],
        "execution": {"purpose": "validation-only", "isolation": "test-double"},
    }))
    r1 = evaluate_submission(entry, sub)
    assert r1["score"] == 100.0

    # 无证据（answers 缺 target）→ C1 从权重排除 → 全部 check 无证据 →
    # 不可评分（BLOCKED，score 不构成复现率）
    (tmp_path / "answers.csv").write_text(
        "target_id,value,unit,source_file\nother,1.63390378426855,value,results/table2.csv\n")
    sub.write_text(json.dumps({
        "protocol_version": "2.0", "submission_id": "s2", "bench_id": "bench-e",
        "system": {"name": "x", "version": "0"},
        "claimed_verdict": "PARTIAL",
        "artifacts": [{"role": "answers", "path": "answers.csv"}],
        "execution": {"purpose": "validation-only", "isolation": "test-double"},
    }))
    r2 = evaluate_submission(entry, sub)
    assert r2["verdict"] == "BLOCKED"
    assert r2.get("no_evidence") is True
    assert r2["checks"][0]["passed"] is None
    assert r2["checks"][0].get("no_evidence") is True


# ── check_provision_phase（digests 契约）──────────────────────────────
def test_check_provision_phase(tmp_path):
    from benchmarks.runner.adapters.loopflow import _artifact_candidates as _  # noqa: F401
    spec = importlib.util.spec_from_file_location(
        "artifact_checks", ROOT / "loops" / "bio-reproducer" / "artifact_checks.py")
    ac = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ac)

    ok, _ = ac.check_provision_phase(tmp_path)
    assert ok is False  # 无 digests

    prov = tmp_path / "03_provision"
    prov.mkdir()
    (prov / "digests.txt").write_text("REPO TAG DIGEST\nbio/x latest sha256:" + "c" * 64 + "\n")
    ok, detail = ac.check_provision_phase(tmp_path)
    assert ok is True
    assert "digest" in detail

    (prov / "digests.txt").write_text("no digests here\n")
    ok, _ = ac.check_provision_phase(tmp_path)
    assert ok is False


# ── check_package_phase（FC-008：run.sh + check.log 退出码 0）─────────
def test_check_package_phase(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "artifact_checks", ROOT / "loops" / "bio-reproducer" / "artifact_checks.py")
    ac = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ac)

    ok, detail = ac.check_package_phase(tmp_path)
    assert ok is False and "run.sh" in detail  # 缺 run.sh

    (tmp_path / "run.sh").write_text("#!/usr/bin/env bash\ncheck(){ echo OK; }\n")
    ok, detail = ac.check_package_phase(tmp_path)
    assert ok is False and "check.log" in detail  # 缺 check.log

    log = tmp_path / "07_package" / "check.log"
    log.parent.mkdir()
    log.write_text("=== check ===\nOK: 前置条件满足\nEXIT=1\n")
    ok, detail = ac.check_package_phase(tmp_path)
    assert ok is False and "退出码 0" in detail  # 退出码非 0

    log.write_text("=== check ===\nOK: 前置条件满足\nEXIT=0\n")
    ok, detail = ac.check_package_phase(tmp_path)
    assert ok is True and "退出码 0" in detail

    # status: 0 / exit 0 也是标准记录
    log.write_text("status: 0\n")
    assert ac.check_package_phase(tmp_path)[0] is True
    log.write_text("exit 0\n")
    assert ac.check_package_phase(tmp_path)[0] is True
