"""L1: Provision Phase — 验证 Provision Agent 的工具部署计划正确性。

使用 loop run --from-phase Provision + golden/plan.md 作为前序输入。
golden/provision.md 提供期望输出的关键结构化字段。
"""

import json
import subprocess
import tempfile
from pathlib import Path


def _run_provision(entry_dir: str, golden_plan_path: str) -> dict:
    """Run Provision phase with golden plan as previous phase output."""
    output_dir = tempfile.mkdtemp(prefix="l1-test-provision-")

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
         "--from-phase", "Provision", "--only-phase", "Provision"],
        capture_output=True, text=True,
    )
    return {
        "returncode": result.returncode,
        "stderr": result.stderr,
        "output_dir": output_dir,
    }


def _read_provision_output(output_dir: str) -> str:
    """Read the provision phase output."""
    path = Path(output_dir) / "03_provision" / "provision.md"
    if not path.exists():
        return ""
    return path.read_text()


def test_provision_identifies_tools_from_plan(bench_001, golden_plan):
    """AC-0001-N-2: Provision 从 plan.md 识别工具, 产出与 golden 一致."""
    result = _run_provision(
        bench_001["entry_dir"], golden_plan["path"]
    )

    output = _read_provision_output(result["output_dir"])

    # Provision may complete (tools deployed) or block (no Docker).
    # Both are valid business decisions. What matters is the tool
    # identification, not the deployment success.
    assert len(output) > 50, f"Provision output too short: {len(output)} chars"

    # Compare against golden provision fixture
    golden = Path(
        f"{bench_001['entry_dir']}/golden/provision.md"
    ).read_text()

    # Key business fields: tools identified
    checks = [
        ("has_r", "R"),
        ("has_deseq2", "DESeq2"),
        ("has_ggplot2", "ggplot2"),
        ("has_apeglm", "apeglm"),
        ("has_bioconductor", "bioconductor"),
    ]

    failures = []
    for name, keyword in checks:
        in_output = keyword.lower() in output.lower()
        in_golden = keyword.lower() in golden.lower()
        if in_output != in_golden:
            failures.append(
                f"{name}: output={in_output}, golden={in_golden}"
            )

    assert not failures, (
        f"Provision tool list differs from golden:\n" + "\n".join(failures)
    )