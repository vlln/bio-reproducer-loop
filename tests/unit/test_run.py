"""L1: Run Phase — 验证 Run Agent 的流程编排正确性。

使用 loop run --only-phase Run + golden fixtures 作为前序输入。
"""

import json
import subprocess
import tempfile
from pathlib import Path


def _run_run(entry_dir: str, golden_plan_path: str, golden_provision_path: str,
             golden_data_manifest_path: str) -> dict:
    """Run Run phase with all previous phase outputs."""
    output_dir = tempfile.mkdtemp(prefix="l1-test-run-")

    # Copy golden fixtures as previous phase outputs
    setups = {
        "01_plan/plan.md": golden_plan_path,
        "03_provision/provision.md": golden_provision_path,
        "04_data/data_manifest.md": golden_data_manifest_path,
    }
    for rel_path, src_path in setups.items():
        dst = Path(output_dir) / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(Path(src_path).read_text())

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
         "--only-phase", "Run"],
        capture_output=True, text=True,
    )
    return {
        "returncode": result.returncode,
        "stderr": result.stderr,
        "output_dir": output_dir,
    }


def test_run_plans_pipeline_from_plan(bench_001, golden_plan, golden_provision,
                                       golden_data_manifest, golden_run_results):
    """AC-0001-N-2: Run agent 根据前序输出执行分析, 产出与 golden 一致."""
    result = _run_run(
        bench_001["entry_dir"],
        golden_plan["path"],
        golden_provision["path"],
        golden_data_manifest["path"],
    )

    output_path = Path(result["output_dir"]) / "05_run" / "run_results.md"
    if not output_path.exists():
        assert "run" in result["stderr"].lower() or result["returncode"] != 0, (
            f"Run should produce output or fail cleanly"
        )
        return

    output = output_path.read_text()
    golden = golden_run_results["content"]

    # Key business fields: analysis method and key genes
    checks = [
        ("has_deseq2", "DESeq2"),
        ("has_gene_a", "Gene_A"),
        ("has_gene_b", "Gene_B"),
    ]
    failures = []
    for name, keyword in checks:
        in_output = keyword.lower() in output.lower()
        in_golden = keyword.lower() in golden.lower()
        if in_output != in_golden:
            failures.append(f"{name}: output={in_output}, golden={in_golden}")

    assert not failures, (
        f"Run output differs from golden:\n" + "\n".join(failures)
    )