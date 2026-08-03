"""Run one isolated loopflow agent for an internal evaluation case.

loopflow ≥0.24.0 移除 phase 抽象（ADR-0052），`--only-phase` 不再存在；
单 phase 评测改用 loopflow ≥0.26.0 的 `--agent` 单 agent 运行入口
（BL-047 / ADR-0055）：不导入、不执行 workflow.py，直接运行指定
agent_def，具有完整 Run 语义（run_dir/缓存/事件/可 recover）。

prompt / agent_def 从 `loops/bio-reproducer/workflow.py` 的 PHASES 注册表
读取，与完整 workflow 保持单一事实来源，避免 phase prompt 双处维护漂移。
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).parents[2]
ENTRIES_DIR = ROOT / "benchmarks" / "entries"
FIXTURES_DIR = ROOT / "evals" / "fixtures"
LOOP_DIR = ROOT / "loops" / "bio-reproducer"


def _load_workflow():
    """Load loops/bio-reproducer/workflow.py without executing run()."""
    spec = importlib.util.spec_from_file_location(
        "bio_reproducer_workflow", LOOP_DIR / "workflow.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def phase_spec(phase: str) -> dict:
    """Look up a phase agent call spec from the workflow PHASES registry."""
    spec = _load_workflow().PHASES
    if phase not in spec:
        raise KeyError(f"Unknown phase {phase!r}; known: {sorted(spec)}")
    return spec[phase]


def run_phase(case: dict, output_dir: Path) -> subprocess.CompletedProcess:
    input_dir = ENTRIES_DIR / case["input"]["benchmark"] / "input"
    output_dir.mkdir(parents=True, exist_ok=True)
    for relative, declaration in case.get("upstream", {}).items():
        if isinstance(declaration, dict) and "input" in declaration:
            source = input_dir / declaration["input"]
        else:
            source = FIXTURES_DIR / declaration
        target = output_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)

    override_paper = case["input"].get("override_paper")
    paper = Path(override_paper) if override_paper else input_dir / "paper.pdf"
    if not override_paper and not paper.is_file():
        paper = input_dir / "paper.md"

    spec = phase_spec(case["phase"])
    # consent=ask 与完整 workflow 缺省一致（_base.md 权限模式缺省 ask）。
    params = [f"language={case.get('language', 'en')}", "consent=ask"]
    if paper.is_file():
        params.append(f"paper_path={paper}")
    param_args = [item for pair in (("--param", p) for p in params) for item in pair]
    return subprocess.run(
        [
            "loop",
            "run",
            "bio-reproducer",
            "--agent",
            spec["agent_def"],
            "--prompt",
            spec["prompt"],
            "--work-dir",
            str(output_dir),
            *param_args,
        ],
        capture_output=True,
        text=True,
    )


def assert_text_checks(content: str, checks: dict) -> None:
    minimum = int(checks.get("min_chars", 0))
    assert len(content) >= minimum, f"Output too short: {len(content)} < {minimum}"
    lowered = content.lower()
    missing = [value for value in checks.get("contains", []) if str(value).lower() not in lowered]
    forbidden = [value for value in checks.get("not_contains", []) if str(value).lower() in lowered]
    unmatched_groups = [
        values for values in checks.get("contains_any", [])
        if not any(str(value).lower() in lowered for value in values)
    ]
    assert not missing, f"Missing expected content: {missing}"
    assert not forbidden, f"Found forbidden content: {forbidden}"
    assert not unmatched_groups, f"None of the alternatives were found: {unmatched_groups}"
