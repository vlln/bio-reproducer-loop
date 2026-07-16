"""L1: Reader Phase — 验证 Reader Agent 的业务逻辑正确性。

使用 loop run --from-phase 实现 Phase 隔离执行。
Reader 无前序依赖，直接跑全 workflow 即可。
golden/plan.md 提供期望输出的关键结构化字段。
"""

import json
import subprocess
import tempfile
from pathlib import Path


def _run_phase(entry_dir: str, from_phase: str, setup: dict | None = None) -> dict:
    """Run a single phase via loop run --from-phase.

    Args:
        entry_dir: Path to benchmark entry directory
        from_phase: Phase name to start from
        setup: Dict of {relative_path: source_path} to copy into output_dir
               before running (simulates previous phase outputs).

    Returns:
        dict with status, output_dir, and the phase's main output file content.
    """
    output_dir = tempfile.mkdtemp(prefix="l1-test-")

    # Copy golden fixtures as previous phase outputs
    if setup:
        for rel_path, src_path in setup.items():
            dst = Path(output_dir) / rel_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(Path(src_path).read_text())

    # Resolve paper path
    paper = Path(entry_dir) / "paper.pdf"
    if not paper.exists():
        paper = Path(entry_dir) / "paper.md"

    args = json.dumps({
        "paper_path": str(paper),
        "output_dir": output_dir,
        "language": "en",
    })

    result = subprocess.run(
        ["loop", "run", "bio-reproducer", "--args", args,
         "--only-phase", from_phase],
        capture_output=True, text=True,
    )
    return {
        "returncode": result.returncode,
        "stderr": result.stderr,
        "output_dir": output_dir,
    }


def _read_phase_output(output_dir: str, phase_rel_path: str) -> str:
    """Read a phase's main output file."""
    path = Path(output_dir) / phase_rel_path
    if not path.exists():
        return ""
    return path.read_text()


def _extract_key_fields(content: str, golden_path: str) -> dict:
    """Extract key business fields from output for comparison with golden.

    Returns a dict of field_name -> (actual_value, golden_value, match).
    """
    fields = {}
    golden = Path(golden_path).read_text()

    # Key field checks — these are the business-critical extractions
    checks = [
        ("has_deseq2", "DESeq2"),
        ("has_r_version", "4.3.0"),
        ("has_gene_a", "Gene_A"),
        ("has_gene_b", "Gene_B"),
        ("has_counts_csv", "counts.csv"),
        ("has_volcano", "volcano"),
    ]

    for name, keyword in checks:
        fields[name] = {
            "actual": keyword in content,
            "golden": keyword in golden,
            "match": (keyword in content) == (keyword in golden),
        }

    return fields


def test_reader_completes_with_valid_paper(bench_001):
    """AC-0001-N-1: Reader 正确提取论文关键信息."""
    result = _run_phase(
        bench_001["entry_dir"], "Reader",
        setup=None,  # Reader has no previous phase dependencies
    )

    assert result["returncode"] == 0, (
        f"Reader should exit cleanly. stderr: {result['stderr'][:500]}"
    )

    output = _read_phase_output(result["output_dir"], "01_plan/plan.md")
    assert len(output) > 100, f"plan.md too short: {len(output)} chars"

    # Compare key fields against golden
    golden_path = f"{bench_001['entry_dir']}/golden/plan.md"
    fields = _extract_key_fields(output, golden_path)

    failures = [f"{k}: actual={v['actual']}, golden={v['golden']}"
                for k, v in fields.items() if not v["match"]]
    assert not failures, (
        f"Key fields mismatch golden fixture:\n" + "\n".join(failures)
    )


def test_reader_blocks_on_missing_paper():
    """AC-0001-B-1: 论文路径不存在, Reader 应报告阻塞."""
    output_dir = tempfile.mkdtemp(prefix="l1-test-")
    args = json.dumps({
        "paper_path": "/nonexistent/path/paper.pdf",
        "output_dir": output_dir,
        "language": "en",
    })

    result = subprocess.run(
        ["loop", "run", "bio-reproducer", "--args", args],
        capture_output=True, text=True,
    )
    # Should either fail (returncode != 0) or produce blocked output
    output = _read_phase_output(output_dir, "01_plan/plan.md")
    is_blocked = result.returncode != 0 or "blocked" in output.lower()
    assert is_blocked, (
        f"Reader should block on missing paper. "
        f"returncode={result.returncode}, output={output[:200]}"
    )


def test_reader_stability(bench_001):
    """AC-0001-N-3: 同一输入跑 3 次, 关键决策点一致."""
    golden_path = f"{bench_001['entry_dir']}/golden/plan.md"

    results = []
    for i in range(3):
        r = _run_phase(bench_001["id"], "Reader")
        assert r["returncode"] == 0, f"Run {i}: Reader should exit cleanly"
        output = _read_phase_output(r["output_dir"], "01_plan/plan.md")
        fields = _extract_key_fields(output, golden_path)
        results.append(fields)

    # All runs must agree on the key fields
    for i in range(1, len(results)):
        for k in results[0]:
            assert results[i][k]["actual"] == results[0][k]["actual"], (
                f"Run {i}: field '{k}' differs from run 0: "
                f"{results[i][k]['actual']} vs {results[0][k]['actual']}"
            )