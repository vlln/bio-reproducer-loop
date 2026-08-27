"""Data phase 产物契约测试（ADR-0011 §2/§2.1/§5，单元 02）。

正反例用已归档 run 的真实产物构造（tests/fixtures/contract/，见 README.md）：
- bench-234 p4_gse136831.log：`curl: (35)` + `wget not found` → not_attempted
- bench-234 p4_gse289881.log：中途 `curl: (56)` 但终态 `Download complete` → completed
- bench-217：04_data 仅散文 manifest，无日志/校验文件 → 无证据（不得判外部不可得）

验收对应 Plan 02：终态类别区分、阻塞也留证据、无阈值、存在+可解析。
"""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "contract"

spec = importlib.util.spec_from_file_location(
    "bio_reproducer_artifact_checks",
    ROOT / "loops" / "bio-reproducer" / "artifact_checks.py",
)
ac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ac)

wf_spec = importlib.util.spec_from_file_location(
    "bio_reproducer_workflow",
    ROOT / "loops" / "bio-reproducer" / "workflow.py",
)
wf = importlib.util.module_from_spec(wf_spec)
wf_spec.loader.exec_module(wf)


# ── 终态类别区分（验收：curl:(35) 判未完成；4xx 判外部不可得；Download complete 判已获取）
def test_bench234_transport_failure_is_not_attempted():
    text = (FIXTURES / "bench-234" / "p4_gse136831.log").read_text()
    assert text.strip().splitlines() == [
        "curl: (35) Recv failure: Connection reset by peer",
        "bash: line 1: wget: command not found",
    ]
    assert ac.classify_download_log(text) == ac.NOT_ATTEMPTED


def test_bench234_completed_despite_intermediate_failure():
    text = (FIXTURES / "bench-234" / "p4_gse289881.log").read_text()
    assert "curl: (56)" in text  # 中途传输失败存在
    assert "Download complete" in text  # 但终态是完成
    assert ac.classify_download_log(text) == ac.COMPLETED


@pytest.mark.parametrize(
    "log",
    [
        "curl: (22) The requested URL returned error: 404\n",
        "curl: (22) The requested URL returned error: 403\n",
        "HTTP/1.1 404 Not Found\n",
        "HTTP/2 451\n",
        "Access denied: registration required\n",
        "requires a registered account to download\n",
    ],
)
def test_http_4xx_and_access_wall_is_unavailable(log):
    assert ac.classify_download_log(log) == ac.UNAVAILABLE


@pytest.mark.parametrize(
    "log",
    [
        "curl: (35) Recv failure: Connection reset by peer\n",
        "curl: (56) OpenSSL SSL_read: unexpected eof while reading\n",
        "curl: (28) Operation timed out after 30000 milliseconds\n",
        "curl: (6) Could not resolve host: ftp.ncbi.nlm.nih.gov\n",
        "bash: line 1: wget: command not found\n",
        "",  # 空日志 = 无证据，保守记未完成
    ],
)
def test_transport_failure_and_missing_fallback_is_not_attempted(log):
    assert ac.classify_download_log(log) == ac.NOT_ATTEMPTED


def test_download_complete_wins_over_transport_failure():
    # 续传场景：同一日志里既有失败又有完成 → 终态按完成
    log = (
        "curl: (56) OpenSSL SSL_read: unexpected eof while reading, errno 0\n"
        "Download complete: GSE289881_RAW.tar (628.6 MB)\n"
        "-rw-r--r-- 1 1000 1000 629M GSE289881_RAW.tar\n"
    )
    assert ac.classify_download_log(log) == ac.COMPLETED


# ── 阻塞也留证据（验收：无正常产物但有日志 → 可判定；两者皆无 → 无证据）
def _make_run_dir(tmp_path, fixture_name):
    """把 fixture 目录当作 04_data 拷入 run 结构（04_data 的父级为 workdir）。"""
    data = tmp_path / "04_data"
    src = FIXTURES / fixture_name
    if src.is_dir():
        import shutil

        shutil.copytree(src, data)
    else:
        data.mkdir()
        shutil.copy2(src, data / src.name)
    return tmp_path


def test_bench217_no_logs_is_no_evidence(tmp_path):
    workdir = _make_run_dir(tmp_path, "bench-217")
    manifest = (FIXTURES / "bench-217" / "data_manifest.md").read_text()
    assert "BLOCKED" in manifest  # 散文 manifest 自称阻塞
    evidence = ac.data_phase_evidence(workdir / "04_data")
    assert evidence["logs"] == {}
    assert evidence["has_checksums"] is False
    assert evidence["has_data_files"] is False
    # 散文里的「不可访问」不构成证据：不得判外部不可得
    ok, detail = ac.check_data_phase(workdir)
    assert ok is False
    assert "无任何标准格式证据" in detail


def test_bench234_logs_are_evidence(tmp_path):
    workdir = _make_run_dir(tmp_path, "bench-234")
    evidence = ac.data_phase_evidence(workdir / "04_data")
    assert set(evidence["logs"]) == {
        "p4_gse136831.log",
        "p4_gse289881.log",
    }
    assert evidence["logs"]["p4_gse136831.log"] == ac.NOT_ATTEMPTED
    assert evidence["logs"]["p4_gse289881.log"] == ac.COMPLETED
    ok, detail = ac.check_data_phase(workdir)
    assert ok is True
    assert "p4_gse289881.log=completed" in detail


# ── check_data_phase：存在 + 可被标准工具解析
def test_check_data_phase_missing_dir(tmp_path):
    ok, detail = ac.check_data_phase(tmp_path)
    assert ok is False
    assert "04_data" in detail


def test_check_data_phase_empty_dir(tmp_path):
    (tmp_path / "04_data").mkdir()
    ok, detail = ac.check_data_phase(tmp_path)
    assert ok is False
    assert "无任何标准格式证据" in detail


def test_check_data_phase_checksums_parseable(tmp_path):
    data = tmp_path / "04_data"
    data.mkdir()
    (data / "sha256sums.txt").write_text("0" * 64 + "  sample.fastq.gz\n")
    ok, _ = ac.check_data_phase(tmp_path)
    assert ok is True


def test_check_data_phase_garbage_checksums_fails(tmp_path):
    data = tmp_path / "04_data"
    data.mkdir()
    (data / "sha256sums.txt").write_text("not a checksum line\n")
    ok, detail = ac.check_data_phase(tmp_path)
    assert ok is False
    assert "无任何标准格式证据" in detail


def test_checksums_parseable_accepts_real_output(tmp_path):
    f = tmp_path / "sha256sums.txt"
    f.write_text(
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  file1.txt\n"
        "01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b  dir/file2.csv\n"
    )
    assert ac.checksums_parseable(f) is True


def test_checksums_parseable_rejects_garbage(tmp_path):
    f = tmp_path / "sha256sums.txt"
    f.write_text("sha256  file1.txt\n  no-hash-here\n")
    assert ac.checksums_parseable(f) is False


# ── 无阈值（验收：代码中不出现重试次数/比例常量）
def test_no_magic_thresholds_in_artifact_checks():
    src = (ROOT / "loops" / "bio-reproducer" / "artifact_checks.py").read_text()
    for needle in ("attempts", "retries", ">= 2", ">= 3", "0.5 *", "threshold"):
        assert needle not in src, f"artifact_checks.py 含评分阈值魔数: {needle}"


# ── workflow 集成：Data 幻觉 complete（04_data 无证据）→ fail-fast
def test_workflow_data_hallucination_fail_fast(tmp_path):
    from types import SimpleNamespace

    def make_result(status="complete", verdict="REPRODUCED"):
        value = {"payload": {"verdict": verdict}} if verdict else None
        return SimpleNamespace(status=status, reason="", value=value, turns=1, tokens=100)

    class FakeAgent:
        def __init__(self):
            self.calls = []

        def __call__(self, prompt, **kwargs):
            self.calls.append(kwargs["label"])
            return make_result()

    class FakeIntervene:
        def __call__(self, key, prompt, schema=None, *, options=None, allow_custom=True):
            return "继续"

    for rel in (
        "01_plan/plan.md",
        "03_provision/provision.md",
        "04_data/data_manifest.md",
        "05_run/run_results.md",
        "06_validate/report.md",
    ):
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x")
    # 04_data 只有散文 manifest，无日志/校验文件 → 模拟旧契约产物
    agent, intervene = FakeAgent(), FakeIntervene()
    logs = []
    import os

    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = wf.run(agent, None, None, logs.append, {"paper_path": "paper.pdf"}, None, intervene, None)
    finally:
        os.chdir(old_cwd)
    assert result is None
    assert agent.calls == ["Reader", "Bootstrap", "Provision", "Data"]
    assert any("前置产物不可用" in line and "04_data" in line for line in logs)
