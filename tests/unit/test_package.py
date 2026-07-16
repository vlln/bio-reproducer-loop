"""L1: Package Phase — 验证 Package Agent 的打包正确性。

使用 loop run --only-phase Package + golden fixtures 作为前序输入。
"""

import json
import subprocess
import tempfile
from pathlib import Path


def _run_package(entry_dir: str, golden_plan_path: str,
                 golden_report_path: str) -> dict:
    """Run Package phase with plan and validate report as previous phase outputs."""
    output_dir = tempfile.mkdtemp(prefix="l1-test-package-")

    # Copy golden fixtures as previous phase outputs
    setups = {
        "01_plan/plan.md": golden_plan_path,
        "06_validate/report.md": golden_report_path,
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
         "--only-phase", "Package"],
        capture_output=True, text=True,
    )
    return {
        "returncode": result.returncode,
        "stderr": result.stderr,
        "output_dir": output_dir,
    }


def test_package_produces_deliverables(bench_001, golden_plan, golden_report):
    """AC-0001-N-2: Package agent 产出可复现包 (README.md + run.sh)."""
    result = _run_package(
        bench_001["entry_dir"],
        golden_plan["path"],
        golden_report["path"],
    )

    output_dir = Path(result["output_dir"])

    # Package phase writes to root of output_dir
    readme = output_dir / "README.md"
    run_sh = output_dir / "run.sh"

    assert readme.exists(), (
        f"Package must produce README.md. Files: {list(output_dir.iterdir())}"
    )
    assert run_sh.exists(), (
        f"Package must produce run.sh. Files: {list(output_dir.iterdir())}"
    )

    readme_content = readme.read_text()
    assert len(readme_content) > 50, f"README.md too short: {len(readme_content)} chars"
    assert "reproduc" in readme_content.lower(), (
        "README.md must mention reproducibility"
    )