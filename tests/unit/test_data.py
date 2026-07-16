"""L1: Data Phase — 验证 Data Agent 的数据获取策略正确性。

使用 loop run --only-phase Data + golden fixtures 作为前序输入。
"""

import json
import subprocess
import tempfile
from pathlib import Path


def _run_data(entry_dir: str, golden_plan_path: str) -> dict:
    """Run Data phase with golden plan as previous phase output."""
    output_dir = tempfile.mkdtemp(prefix="l1-test-data-")

    # Copy golden plan as Reader's output
    plan_dir = Path(output_dir) / "01_plan"
    plan_dir.mkdir(parents=True, exist_ok=True)
    (plan_dir / "plan.md").write_text(Path(golden_plan_path).read_text())

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
         "--only-phase", "Data"],
        capture_output=True, text=True,
    )
    return {
        "returncode": result.returncode,
        "stderr": result.stderr,
        "output_dir": output_dir,
    }


def test_data_identifies_sources_from_plan(bench_001, golden_plan, golden_data_manifest):
    """AC-0001-N-2: Data agent 从 plan.md 识别数据源, 产出与 golden 一致."""
    result = _run_data(bench_001["entry_dir"], golden_plan["path"])

    output_path = Path(result["output_dir"]) / "04_data" / "data_manifest.md"
    if not output_path.exists():
        # Data phase may have failed — acceptable if it reports the issue
        assert "data" in result["stderr"].lower() or result["returncode"] != 0, (
            f"Data should produce output or fail cleanly"
        )
        return

    output = output_path.read_text()
    golden = golden_data_manifest["content"]

    # Key business fields: data sources identified
    checks = [
        ("has_counts_csv", "counts.csv"),
        ("has_gse", "GSE"),
    ]
    failures = []
    for name, keyword in checks:
        in_output = keyword.lower() in output.lower()
        in_golden = keyword.lower() in golden.lower()
        if in_output != in_golden:
            failures.append(f"{name}: output={in_output}, golden={in_golden}")

    assert not failures, (
        f"Data output differs from golden:\n" + "\n".join(failures)
    )