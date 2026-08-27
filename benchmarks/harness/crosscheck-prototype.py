"""ADR-0011 验证 6 原型：answers 交叉核对。

规则（无魔数）：answers 中的 value 必须是 source_file 中某个数值的**正确舍入**——
容差由 value 自身书写的精度决定：|a - b| <= 0.5 * 10^(-decimals(a))。
不引入任何人为阈值；找不到即"无证据"，不是"判错"。
"""
import csv
import re
import sys
from decimal import Decimal
from pathlib import Path

NUM = re.compile(r"[-+]?\d+\.?\d*(?:[eE][-+]?\d+)?")


def decimals(s: str) -> int:
    try:
        d = Decimal(s)
    except Exception:
        return 0
    return max(0, -d.as_tuple().exponent)


def numbers_in(path: Path) -> list[float]:
    out = []
    for tok in NUM.findall(path.read_text(errors="replace")):
        try:
            out.append(float(tok))
        except ValueError:
            pass
    return out


def locate(value_str: str, source: Path) -> tuple[bool, str]:
    if not source.is_file():
        return False, f"source_file 不存在: {source.name}"
    try:
        a = float(value_str)
    except ValueError:
        return False, "value 非数值"
    tol = 0.5 * 10 ** (-decimals(value_str))
    for b in numbers_in(source):
        if abs(a - b) <= tol:
            return True, f"命中 {b}（容差 {tol:g}，由书写精度导出）"
    return False, f"在 {source.name} 中找不到 {value_str}（容差 {tol:g}）"


def check(answers_csv: Path, base: Path) -> int:
    failed = 0
    with answers_csv.open() as fh:
        for row in csv.DictReader(fh):
            ok, note = locate(row["value"], base / row["source_file"])
            print(f"{'PASS' if ok else 'NO-EVIDENCE'}  {row['target']:<28} {row['value']:<20} {note}")
            failed += 0 if ok else 1
    return failed


if __name__ == "__main__":
    base = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(".")
    sys.exit(1 if check(Path(sys.argv[1]), base) else 0)
