"""Pytest 根 conftest：为测试提供 loopflow 框架可导入路径。

bio-reproducer workflow 自 ADR-0058 迁移后依赖框架层 run_rerun_loop
（loopflow.domain.rerun_loop）。loopflow 以源码形式存在于
~/Project/loopflow（或 LOOPFLOW_SRC 环境变量覆盖）；测试将其实 src/
加入 sys.path，使 workflow 能 import 真实框架实现（而非 mock）。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _loopflow_src() -> Path | None:
    env = os.environ.get("LOOPFLOW_SRC")
    if env:
        return Path(env)
    candidates = [
        Path.home() / "Project" / "loopflow" / "src",
        Path(__file__).resolve().parents[2] / "loopflow" / "src",  # 仓库内联
    ]
    for c in candidates:
        if (c / "loopflow" / "__init__.py").is_file():
            return c
    return None


_src = _loopflow_src()
if _src is not None and str(_src) not in sys.path:
    sys.path.insert(0, str(_src))
