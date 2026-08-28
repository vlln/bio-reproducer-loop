#!/usr/bin/env python3
"""S2/BL-015 claim 策展落盘脚本：把 subagent 提取的 claims JSON 写入 entry。

对每个 entry：
1. claims.yaml：替换 claims: [] 为提取的 claims（保留 data_references/code_references/calibration）
2. input/questions.yaml：追加缺失的 target_id（保持现有 + 新增）
3. bundle.yaml：更新 questions.yaml 的 sha256
4. oracle/rubric.yaml：A1/A2 降为诊断权重（10/10）+ 新增 C1-Cn 数值 check（平分 80）
5. 打印待人工复核的条目

用法: python3 s2_apply_claims.py <claims.json>
claims.json 格式: {"bench-227": {"paper_found": true, "claims": [...]}, ...}
"""

import json
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
ENTRIES = ROOT / "benchmarks" / "entries"


def apply_entry(entry_id: str, data: dict) -> list[str]:
    changes = []
    claims = data.get("claims") or []
    if not data.get("paper_found"):
        changes.append(f"{entry_id}: paper_found=false，跳过（需人工）")
        return changes
    if not claims:
        changes.append(f"{entry_id}: 0 claims，跳过")
        return changes
    e = ENTRIES / entry_id

    # 1. claims.yaml
    cp = e / "oracle" / "claims.yaml"
    d = yaml.safe_load(cp.read_text())
    d["claims"] = claims
    # calibration.d5 反映有数值 claim
    cal = d.get("calibration") or {}
    cal["d5"] = 2 if len(claims) >= 3 else cal.get("d5", 0)
    d["calibration"] = cal
    cp.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False, default_flow_style=False))
    changes.append(f"{entry_id}: claims.yaml {len(claims)} claims")

    # 2. questions.yaml
    qp = e / "input" / "questions.yaml"
    q = yaml.safe_load(qp.read_text())
    existing = {x["target_id"] for x in q.get("questions", [])}
    added = 0
    for c in claims:
        if c["target_id"] not in existing:
            q["questions"].append({
                "target_id": c["target_id"],
                "question": f"复现论文报告的 {c['metric']} 数值",
                "unit": c.get("unit", "value"),
            })
            added += 1
    qp.write_text(yaml.safe_dump(q, allow_unicode=True, sort_keys=False))
    changes.append(f"{entry_id}: questions.yaml +{added}")

    # 3. bundle.yaml sha256
    import hashlib
    import re
    sha = hashlib.sha256(qp.read_bytes()).hexdigest()
    bp = e / "bundle.yaml"
    btext = bp.read_text()
    # 找到 questions 资源的 sha256 行并替换
    lines = btext.splitlines()
    for i, line in enumerate(lines):
        if "path: questions.yaml" in line:
            # 向下找最近的 sha256 行
            for j in range(i + 1, min(i + 6, len(lines))):
                if "sha256:" in lines[j]:
                    lines[j] = re.sub(r"sha256:\s*\w+", f"sha256: {sha}", lines[j])
                    break
            break
    bp.write_text("\n".join(lines) + "\n")
    changes.append(f"{entry_id}: bundle sha256 更新")

    # 4. rubric.yaml
    rp = e / "oracle" / "rubric.yaml"
    r = yaml.safe_load(rp.read_text())
    # 先移除全部 C* check（幂等：重复运行不叠加），A1/A2 降诊断权重
    r["checks"] = [c for c in r["checks"] if not c["id"].startswith("C")]
    for c in r["checks"]:
        if c["id"] in ("A1", "A2"):
            c["weight"] = 10
    w = round(80.0 / len(claims), 4)
    for c in claims:
        r["checks"].append({
            "id": c["id"],
            "description": f"复现声明 {c['metric']}（论文值 {c['paper_value']}）",
            "evidence": {"artifact_role": "answers"},
            "comparison": {
                "comparator": "python_verify", "module": "verify.py",
                "function": "check_claim", "config": {"claim_id": c["id"]},
            },
            "weight": w,
        })
    rp.write_text(yaml.safe_dump(r, allow_unicode=True, sort_keys=False))
    total = sum(c["weight"] for c in r["checks"])
    changes.append(f"{entry_id}: rubric {len(r['checks'])} checks (w={total:.2f})")
    return changes


def main():
    src = Path(sys.argv[1])
    data = json.loads(src.read_text())
    all_changes = []
    for entry_id, entry_data in sorted(data.items()):
        all_changes.extend(apply_entry(entry_id, entry_data))
    print("\n".join(all_changes))
    print(f"\n处理 {len(data)} 个 entry")


if __name__ == "__main__":
    main()
