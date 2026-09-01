#!/usr/bin/env python3
"""bench-220-0026-migrate answers.csv 修正版生成脚本（归档补证，5e37e08a 审查 gap a）。

背景：2026-08-27 迁移 run 的 answers.csv 把 `hr_formatted` 列（`1.63 (1.25–2.14)`）
误当 value 转录，而源表 `hr` 列就是纯数值（1.6339/3.3246/2.423）。CI 格式使外部
evaluate_run 判「交叉核对失败 — value 非数值（NO-EVIDENCE，不计分）」（对照 JSON：
eval-0026-migrate-ci.json）；修正为纯数值后 C1-C3 全部 passed=true（eval-0026-migrate-fixed.json）。

本脚本**不覆盖原始 answers.csv**（诚实保留 run 原始产物），只生成 `answers.fixed.csv`：
- 逐行读原始 answers.csv（保留 target_id/unit/source_file 不变）
- 从 all_cvd_hr_results.csv（含 target_id + hr 纯数值列）取 value
- 校验：所有行都能映射到源表 hr，否则退出码 1

用法：
    python3 fix-answers-0026-migrate.py \
        /storeData/gs/claroai-calibration/runs/bench-220-0026-migrate/repro-data/05_run
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path


def main(phase5_dir: str) -> int:
    d = Path(phase5_dir)
    answers = d / "answers.csv"
    all_cvd = d / "results" / "all_cvd_hr_results.csv"
    if not answers.is_file() or not all_cvd.is_file():
        print(f"error: 需要 {answers} 与 {all_cvd} 都存在", file=sys.stderr)
        return 1

    hr_by_target: dict[str, str] = {}
    with open(all_cvd, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            hr_by_target[row["target_id"].strip()] = row["hr"].strip()

    out_rows = []
    with open(answers, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        if [h.strip().lower() for h in header] != ["target_id", "value", "unit", "source_file"]:
            print(f"error: {answers} 表头不是 target_id,value,unit,source_file", file=sys.stderr)
            return 1
        for row in reader:
            if not row:
                continue
            target, _value, unit, source = (c.strip() for c in row[:4])
            if target not in hr_by_target:
                print(f"error: target_id {target!r} 在 all_cvd_hr_results.csv 无 hr 映射", file=sys.stderr)
                return 1
            out_rows.append([target, hr_by_target[target], unit, source])

    fixed = d / "answers.fixed.csv"
    with open(fixed, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["target_id", "value", "unit", "source_file"])
        w.writerows(out_rows)
    print(f"written {fixed} ({len(out_rows)} rows; source=hr column of all_cvd_hr_results.csv)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
