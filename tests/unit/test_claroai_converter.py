"""AC-0009 ClaroAI Converter tests (TDD). Deterministic, offline, uses tests/fixtures/claroai/."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

FIXTURES = Path(__file__).parent.parent / "fixtures" / "claroai"


def _make_snapshot(tmp_path: Path) -> Path:
    """Build a 2-paper claroai-bench snapshot from fixtures."""
    snap = tmp_path / "snapshot"
    snap.mkdir()
    (snap / "papers").mkdir()
    for p in ("paper_01", "paper_10"):
        shutil.copytree(FIXTURES / p, snap / "papers" / p)
    return snap


def _run_converter(snapshot: Path, out: Path, start_id: int = 200, extra: list | None = None):
    from benchmarks.converters.claroai.cli import main
    argv = ["--source", str(snapshot), "--output", str(out),
            "--start-id", str(start_id)] + (extra or [])
    return main(argv)


@pytest.fixture(scope="module")
def snapshot(tmp_path_factory):
    return _make_snapshot(tmp_path_factory.mktemp("snap"))


# ── AC-0009-N-1: 快照生成全部 entry 且 validate 全过（L5） ──────────────────
def test_n1_generates_entries_and_passes_bundle_gate(snapshot, tmp_path):
    out = tmp_path / "entries"
    result = _run_converter(snapshot, out)
    assert result["status"] == "CONVERT_OK"
    for paper in ("paper_01", "paper_10"):
        entry_dir = out / result["mapping"][paper]
        assert (entry_dir / "bundle.yaml").is_file()
        assert (entry_dir / "metadata.yaml").is_file()
        assert (entry_dir / "oracle" / "claims.yaml").is_file()
        assert (entry_dir / "oracle" / "rubric.yaml").is_file()
        assert (entry_dir / "oracle" / "verify.py").is_file()
        assert (entry_dir / "input" / "paper" / "locator.md").is_file()
        bundle = yaml.safe_load((entry_dir / "bundle.yaml").read_text())
        assert bundle["level"] == "L5"
        assert bundle["primary_paper"] == "paper-main"
        from benchmarks.runner.bundle_validator import validate_entry
        validate_entry(entry_dir)  # raises on failure


# ── AC-0009-N-2: 确定性可重放（同快照 → 字节一致） ──────────────────────────
def test_n2_deterministic_output(snapshot, tmp_path):
    out1, out2 = tmp_path / "e1", tmp_path / "e2"
    _run_converter(snapshot, out1)
    _run_converter(snapshot, out2)
    files1 = sorted(p.relative_to(out1) for p in out1.rglob("*") if p.is_file())
    files2 = sorted(p.relative_to(out2) for p in out2.rglob("*") if p.is_file())
    assert [str(f) for f in files1] == [str(f) for f in files2]
    for f in files1:
        assert (out1 / f).read_bytes() == (out2 / f).read_bytes()


# ── AC-0009-N-3: locator 与 bundle primary paper DOI 一致 ────────────────────
def test_n3_locator_matches_bundle_doi(snapshot, tmp_path):
    out = tmp_path / "entries"
    result = _run_converter(snapshot, out)
    entry_dir = out / result["mapping"]["paper_01"]
    bundle = yaml.safe_load((entry_dir / "bundle.yaml").read_text())
    locator = (entry_dir / "input" / "paper" / "locator.md").read_text()
    primary = next(r for r in bundle["resources"] if r["id"] == bundle["primary_paper"])
    assert primary["availability"] == "external"
    assert primary["source"].startswith("https://doi.org/")
    assert primary["source"].split("/doi.org/")[1] in locator


# ── AC-0009-N-5: 转录正确性（paper_01 ground truth 与 scores.json evidence 一致） ──
def test_n5_transcription_matches_ground_truth(snapshot, tmp_path):
    out = tmp_path / "entries"
    result = _run_converter(snapshot, out)
    entry_dir = out / result["mapping"]["paper_01"]
    claims = yaml.safe_load((entry_dir / "oracle" / "claims.yaml").read_text())
    scores = json.loads((FIXTURES / "paper_01" / "scores.json").read_text())
    d1, d2, d3 = (scores["dimensions"][k] for k in
                  ("D1_data_findable", "D2_data_accessible", "D3_code_methods_available"))
    assert claims["audit_scope"] == "d1_d3_audit"
    # D2=0 → 全部不可下载
    assert all(r["downloadable"] == "false" for r in claims["data_references"])
    # 主代码仓库按 D3=1 → hollow；非主仓库 unknown（不编造）
    code = claims["code_references"]
    main_repo = [r for r in code if r["ground_truth"] != "unknown"]
    assert main_repo and all(r["ground_truth"] == "hollow" for r in main_repo)
    assert any(r["ground_truth"] == "unknown" for r in code)  # 工具仓库不审计
    # calibration 段 = 作者分数（只作校准）
    assert claims["calibration"] == {"d1": d1["score"], "d2": d2["score"], "d3": d3["score"],
                                     "confidence": {"d1": d1["agent_confidence"],
                                                    "d2": d2["agent_confidence"],
                                                    "d3": d3["agent_confidence"]}}


# ── AC-0009-B-2: 湿实验论文正常生成 ──────────────────────────────────────────
def test_b2_wetlab_paper_generates(snapshot, tmp_path):
    out = tmp_path / "entries"
    result = _run_converter(snapshot, out)
    entry_dir = out / result["mapping"]["paper_10"]
    metadata = yaml.safe_load((entry_dir / "metadata.yaml").read_text())
    assert metadata["scored_scope"] == "d1_d3_audit"
    claims = yaml.safe_load((entry_dir / "oracle" / "claims.yaml").read_text())
    assert claims["calibration"] is not None


# ── AC-0009-B-3: evidence 缺失 → unknown，不编造 ─────────────────────────────
def test_b3_missing_evidence_marks_unknown(tmp_path):
    snap = _make_snapshot(tmp_path)
    # 篡改 scores.json：D3 分数为 2 但 justification/evidence 均不提及任何 repo
    sc = json.loads((snap / "papers" / "paper_01" / "scores.json").read_text())
    sc["dimensions"]["D3_code_methods_available"]["score"] = 2
    sc["dimensions"]["D3_code_methods_available"]["justification"] = "no repo mentioned"
    sc["dimensions"]["D3_code_methods_available"]["evidence"] = ["No code repository linked"]
    (snap / "papers" / "paper_01" / "scores.json").write_text(json.dumps(sc))
    out = tmp_path / "entries"
    result = _run_converter(snap, out)
    entry_dir = out / result["mapping"]["paper_01"]
    claims = yaml.safe_load((entry_dir / "oracle" / "claims.yaml").read_text())
    assert all(r["ground_truth"] == "unknown" for r in claims["code_references"])


# ── AC-0009-E-1: 快照损坏 → 报错并列出受影响论文 ─────────────────────────────
def test_e1_corrupt_snapshot_reports(tmp_path):
    snap = _make_snapshot(tmp_path)
    (snap / "papers" / "paper_01" / "scores.json").write_text("{broken json")
    out = tmp_path / "entries"
    with pytest.raises(SystemExit) as exc:
        _run_converter(snap, out)
    assert exc.value.code != 0


# ── AC-0009-E-2: locator 与 bundle DOI 不一致 → 阻止生成 ─────────────────────
def test_e2_locator_doi_conflict(snapshot, tmp_path):
    out = tmp_path / "entries"
    result = _run_converter(snapshot, out)
    entry_dir = out / result["mapping"]["paper_01"]
    # 篡改 locator 造成与 bundle primary DOI 不一致
    locator = entry_dir / "input" / "paper" / "locator.md"
    locator.write_text("# locator\nDOI: 10.9999/conflict\n")
    # 重跑 converter（entry 已存在 → CONVERT_ID_CONFLICT，阻止生成不一致 entry）
    with pytest.raises(SystemExit):
        _run_converter(snapshot, out, extra=["--check-existing"])


# ── AC-0009-F-1: rubric 含作者真值键 → validator INVALID_BUNDLE（CC-003） ────
def test_f1_rubric_forbidden_author_keys(snapshot, tmp_path):
    out = tmp_path / "entries"
    result = _run_converter(snapshot, out)
    entry_dir = out / result["mapping"]["paper_01"]
    rubric = yaml.safe_load((entry_dir / "oracle" / "rubric.yaml").read_text())
    rubric["calibration"] = {"d1": 2}  # inject forbidden author-truth key
    (entry_dir / "oracle" / "rubric.yaml").write_text(yaml.safe_dump(rubric))
    from benchmarks.runner.bundle_validator import BundleValidationError, validate_entry
    with pytest.raises(BundleValidationError):
        validate_entry(entry_dir)


# ── AC-0009-F-4: metadata 缺 scored_scope → validator INVALID_BUNDLE（CC-002） ──
def test_f4_missing_scored_scope_rejected(snapshot, tmp_path):
    out = tmp_path / "entries"
    result = _run_converter(snapshot, out)
    entry_dir = out / result["mapping"]["paper_01"]
    metadata = yaml.safe_load((entry_dir / "metadata.yaml").read_text())
    del metadata["scored_scope"]
    (entry_dir / "metadata.yaml").write_text(yaml.safe_dump(metadata))
    from benchmarks.runner.bundle_validator import BundleValidationError, validate_entry
    with pytest.raises(BundleValidationError):
        validate_entry(entry_dir)


# ── 回归：validator 扩展不影响既有 entry（bench-001） ────────────────────────
def test_existing_entry_unaffected():
    from benchmarks.runner.bundle_validator import validate_entry
    here = Path(__file__).parent.parent.parent
    validate_entry(here / "benchmarks" / "entries" / "bench-001")
