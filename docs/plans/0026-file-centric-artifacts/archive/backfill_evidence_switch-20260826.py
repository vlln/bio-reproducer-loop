"""一次性迁移（单元 04 证据面切换）：已生成 entry 增量更新，不重生成。

对 `benchmarks/entries/bench-*` 每个 entry：
- `oracle/claims.yaml`：每个 claim 若无 `target_id` → 加 `_slugify(metric)`
  （公开问题清单的键，ADR-0011 §4.1）；**不动 paper_value/tolerance/notes**
- `input/questions.yaml`：不存在时从 claims 生成（target_id + question + unit，无期望值）
- `oracle/verify.py`：替换为 converter 的 VERIFY_TEMPLATE（新证据面：answers +
  交叉核对 + 04_data/03_provision 标准格式）

幂等：已有 target_id/questions/新模板则跳过对应项。不触碰手工策展的 claims
（bench-223 AUROC 等）——只加字段，不改值。

用法：PYTHONPATH=. python3 benchmarks/converters/claroai/backfill_evidence_switch.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from benchmarks.converters.claroai.converter import (  # noqa: E402
    VERIFY_TEMPLATE,
    _build_questions,
    _slugify,
)


def backfill_entry(entry_dir: Path) -> dict:
    changed = {"claims": [], "questions": None, "verify": False}
    claims_path = entry_dir / "oracle" / "claims.yaml"
    if not claims_path.is_file():
        return changed

    claims = yaml.safe_load(claims_path.read_text())
    # 保护：只处理 claroai claims 结构（claims 为数值列表）；手写 entry
    # （bench-001~006/100 的 experimental_design/methods 结构）不动
    if not isinstance(claims.get("claims"), list):
        return changed
    updated = False
    for c in claims.get("claims", []):
        if "target_id" not in c:
            c["target_id"] = _slugify(c["metric"])
            changed["claims"].append(c["id"])
            updated = True
    if updated:
        claims_path.write_text(yaml.safe_dump(claims, sort_keys=False, allow_unicode=True))

    questions_path = entry_dir / "input" / "questions.yaml"
    if not questions_path.exists():
        questions = _build_questions(claims.get("claims", []))
        questions_path.write_text(yaml.safe_dump(questions, sort_keys=False, allow_unicode=True))
        changed["questions"] = len(questions.get("questions", []))

    # rubric.yaml：证据面切换（FC-004）——validate_report/data_manifest/
    # provision_report 散文证据 → answers/data_evidence/environment 标准格式
    rubric_path = entry_dir / "oracle" / "rubric.yaml"
    if rubric_path.is_file():
        rubric = yaml.safe_load(rubric_path.read_text())
        role_map = {
            "validate_report": "answers",
            "data_manifest": "data_evidence",
            "provision_report": "environment",
        }
        remapped = False
        for check in rubric.get("checks", []):
            role = (check.get("evidence") or {}).get("artifact_role")
            if role in role_map:
                check["evidence"]["artifact_role"] = role_map[role]
                remapped = True
        if remapped:
            rubric_path.write_text(yaml.safe_dump(rubric, sort_keys=False, allow_unicode=True))
            changed["rubric"] = True

    # bundle.yaml：声明 questions 资源（bundle_validator 要求 staged 文件全部声明）
    bundle_path = entry_dir / "bundle.yaml"
    if bundle_path.is_file() and questions_path.exists():
        bundle = yaml.safe_load(bundle_path.read_text())
        if not any(r.get("id") == "questions" for r in bundle.get("resources", [])):
            from benchmarks.converters.claroai.converter import _sha256

            bundle["resources"].append({
                "id": "questions",
                "role": "questions",
                "authority": "benchmark",
                "availability": "bundled",
                "path": "questions.yaml",
                "source": f"urn:benchmark:{entry_dir.name}:questions",
                "sha256": _sha256(questions_path),
                "media_type": "text/yaml",
                "license": "CC-BY-4.0",
            })
            bundle_path.write_text(yaml.safe_dump(bundle, sort_keys=False, allow_unicode=True))
            changed["bundle"] = True

    verify_path = entry_dir / "oracle" / "verify.py"
    if verify_path.exists() and "v0.2.1" not in verify_path.read_text():
        verify_path.write_text(VERIFY_TEMPLATE)
        changed["verify"] = True
    return changed


def main() -> int:
    entries_root = ROOT / "benchmarks" / "entries"
    total = {"entries": 0, "claims_added": 0, "questions": 0, "rubric": 0, "verify_replaced": 0}
    for entry_dir in sorted(entries_root.glob("bench-*")):
        if not (entry_dir / "oracle").is_dir():
            continue
        changed = backfill_entry(entry_dir)
        total["entries"] += 1
        total["claims_added"] += len(changed["claims"])
        total["questions"] += 1 if changed["questions"] is not None else 0
        total["rubric"] += 1 if changed.get("rubric") else 0
        total["verify_replaced"] += 1 if changed["verify"] else 0
        if any([changed["claims"], changed["questions"] is not None,
                changed.get("rubric"), changed["verify"]]):
            print(f"  {entry_dir.name}: claims+{len(changed['claims'])} "
                  f"questions={'+' + str(changed['questions']) if changed['questions'] is not None else '=unchanged'} "
                  f"rubric={'remapped' if changed.get('rubric') else '=unchanged'} "
                  f"verify={'replaced' if changed['verify'] else '=unchanged'}")
    print(f"done: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
