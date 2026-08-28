"""公开问题清单 → 任务注入段（评测方职责，系统侧不感知）。

ADR-0011 §4.1 / Interface 0002 §2.1：`input/questions.yaml` 是任务的一部分，
由评测方（converter）生成。本模块把问题清单翻译成 **任务注入段**（走 loopflow
原生 `--append-prompt` 通道，注入每个 agent 的 user prompt 末尾），并返回键列表
供 workflow 的 lint 校验。**系统侧（agents/*.md、workflow.py）不写任何文件名**——
只有评测方（adapter / run-entry.sh）调用本模块。

入口无 questions.yaml 时返回 (None, [])：系统退化为 T 编号路径（v1 风格 rubric
如 bench-001~006 无清单，行为不变）。
"""

from __future__ import annotations

from pathlib import Path


def load_question_targets(input_dir: str | Path) -> list[str]:
    """读 input/questions.yaml 的 target_id 列表；无文件/不可解析返回 []。"""
    qfile = Path(input_dir) / "questions.yaml"
    if not qfile.is_file():
        return []
    try:
        import yaml
        data = yaml.safe_load(qfile.read_text(encoding="utf-8"))
        keys = [q.get("target_id") for q in (data.get("questions") or [])]
        return [k for k in keys if isinstance(k, str) and k]
    except Exception:
        return []


def build_questions_injection(input_dir: str | Path) -> tuple[str | None, list[str]]:
    """把公开问题清单翻译成任务注入段文本 + 键列表。

    返回 (injection_text, question_keys)：
    - 有 questions.yaml：注入段（markdown 清单，含逐字 target_id/问题/单位），
      键列表按文件顺序；injection 非 None。
    - 无 questions.yaml / 无 questions： (None, [])，调用方不注入。
    """
    qfile = Path(input_dir) / "questions.yaml"
    if not qfile.is_file():
        return None, []
    try:
        import yaml
        data = yaml.safe_load(qfile.read_text(encoding="utf-8"))
    except Exception:
        return None, []
    questions = data.get("questions") or []
    keys: list[str] = []
    lines: list[str] = ["任务公开问题清单（复现值声明 answers.csv 的 target_id 必须逐字使用以下键）："]
    for i, q in enumerate(questions, 1):
        tid = q.get("target_id")
        if not isinstance(tid, str) or not tid:
            continue
        keys.append(tid)
        qtext = str(q.get("question", "")).strip()
        unit = str(q.get("unit", "")).strip()
        lines.append(f"{i}. target_id=`{tid}` ｜ 问题：{qtext} ｜ 单位：{unit}")
    if not keys:
        return None, []
    return "\n".join(lines), keys
