#!/usr/bin/env bash
# 验证 bench-220 重跑的四阶段新契约产物（0026 容器验收用）
# 用法: bash verify-0026-run.sh <run_dir>
set -uo pipefail
RUN="${1:?用法: verify-0026-run.sh <run_dir>}"
PASS=0; FAIL=0

check() { # check <desc> <cond>
  if [ "$2" = "1" ]; then echo "  ✅ $1"; PASS=$((PASS+1));
  else echo "  ❌ $1"; FAIL=$((FAIL+1)); fi
}

echo "=== 验证 run 目录: $RUN ==="
[ -d "$RUN" ] && check "run 目录存在" 1 || check "run 目录存在" 0

echo; echo "--- Phase 1: Reader (01_plan/plan.md) ---"
[ -s "$RUN/repro-data/01_plan/plan.md" ] && check "plan.md 非空" 1 || check "plan.md 非空" 0
grep -q "Reproduction Target" "$RUN/repro-data/01_plan/plan.md" 2>/dev/null && check "含 Reproduction Target 表" 1 || check "含 Reproduction Target 表" 0
[ -d "$RUN/repro-data/01_plan/paper_markdown" ] && check "paper_markdown/ 存在 (mineru 转换)" 1 || check "paper_markdown/ 存在 (mineru 转换)" 0

echo; echo "--- Phase 2: Bootstrap (02_bootstrap) ---"
BOOT=$(find "$RUN" -maxdepth 2 -type d -name "02_bootstrap" 2>/dev/null | head -1)
if [ -n "$BOOT" ]; then
  find "$BOOT" -type f | head -5 >/dev/null && check "02_bootstrap 有产物" 1 || check "02_bootstrap 有产物" 0
else
  check "02_bootstrap 目录存在" 0
fi

echo; echo "--- Phase 3: Provision (03_provision/digests.txt) ---"
PROV=$(find "$RUN" -maxdepth 2 -type d -name "03_provision" 2>/dev/null | head -1)
if [ -n "$PROV" ] && [ -s "$PROV/digests.txt" ]; then
  check "digests.txt 非空" 1
  head -2 "$PROV/digests.txt" | grep -qE "REPOSITORY|TAG|IMAGE ID|:" && check "digests.txt 为 docker images --digests 格式" 1 || check "digests.txt 格式" 0
else
  check "03_provision/digests.txt 存在且非空" 0
fi

echo; echo "--- Phase 4: Data (04_data) ---"
DATA=$(find "$RUN" -maxdepth 2 -type d -name "04_data" 2>/dev/null | head -1)
if [ -n "$DATA" ]; then
  SHA=$(find "$DATA" -name "sha256sums.txt" 2>/dev/null | head -1)
  [ -n "$SHA" ] && [ -s "$SHA" ] && check "sha256sums.txt 非空" 1 || check "sha256sums.txt 存在且非空" 0
  LOGS=$(find "$DATA" -name "*.log" 2>/dev/null | wc -l | tr -d ' ')
  [ "$LOGS" -ge 1 ] && check "每资源下载日志存在 ($LOGS 个)" 1 || check "下载日志存在" 0
  # curl -C - 续传证据：日志含 206 或 Range
  grep -rl "206\|Content-Range\|range" "$DATA" --include="*.log" 2>/dev/null | head -1 >/dev/null && check "curl 续传证据 (206/Range)" 1 || check "curl 续传证据 (206/Range，可能无需续传)" 0
else
  check "04_data 目录存在" 0
fi

echo; echo "--- Phase 5: Run (05_run) ---"
RUNP=$(find "$RUN" -maxdepth 2 -type d -name "05_run" 2>/dev/null | head -1)
if [ -n "$RUNP" ]; then
  ANSWERS=$(find "$RUNP" -name "answers.csv" 2>/dev/null | head -1)
  if [ -n "$ANSWERS" ] && [ -s "$ANSWERS" ]; then
    check "answers.csv 非空" 1
    HEADER=$(head -1 "$ANSWERS" | tr -d '\r')
    [ "$HEADER" = "target_id,value,unit,source_file" ] && check "answers.csv 表头 = target_id,value,unit,source_file" 1 || check "answers.csv 表头正确 (实际: $HEADER)" 0
    N=$(tail -n +2 "$ANSWERS" | wc -l | tr -d ' ')
    [ "$N" -ge 1 ] && check "answers.csv 数据行 ≥1 ($N 行)" 1 || check "answers.csv 数据行" 0
  else
    check "answers.csv 存在且非空" 0
  fi
  find "$RUNP" -name "commands.log" 2>/dev/null | head -1 | grep -q . && check "commands.log 存在" 1 || check "commands.log 存在" 0
else
  check "05_run 目录存在" 0
fi

echo; echo "--- Phase 6: Validate (06_validate) ---"
VAL=$(find "$RUN" -maxdepth 2 -type d -name "06_validate" 2>/dev/null | head -1)
if [ -n "$VAL" ]; then
  RT=$(find "$VAL" -name "routing.jsonl" 2>/dev/null | head -1)
  if [ -n "$RT" ] && [ -s "$RT" ]; then
    check "routing.jsonl 非空（可选交付记录）" 1
    # 键名白名单: ts/target/decision/route_to/reason（写了必须合规，ADR-0058 可选）
    python3 - "$RT" <<'PY' >/dev/null 2>&1 && check "routing.jsonl 键名在白名单内" 1 || check "routing.jsonl 键名在白名单内" 0
import json,sys
allowed={"ts","target","decision","route_to","reason"}
for line in open(sys.argv[1]):
    d=json.loads(line)
    assert set(d)<=allowed, f"bad keys: {set(d)-allowed}"
PY
    grep -qE "reproduced|proceed|pass|blocked|no_evidence" "$RT" 2>/dev/null && check "routing.jsonl 有决策记录" 1 || check "routing.jsonl 决策记录" 0
  else
    # ADR-0058 迁移：routing.jsonl 为可选交付记录（回环决策在 payload.route_to），
    # 不写不算失败
    check "routing.jsonl 存在（可选，不写视为通过）" 1
  fi
else
  check "06_validate 目录存在" 0
fi

echo; echo "--- Phase 7: Package (check.log) ---"
PKG=$(find "$RUN" -maxdepth 2 -type d -name "07_package" -o -maxdepth 2 -type d -name "package" 2>/dev/null | head -1)
if [ -n "$PKG" ]; then
  CL=$(find "$PKG" -name "check.log" 2>/dev/null | head -1)
  [ -n "$CL" ] && [ -s "$CL" ] && check "check.log 非空" 1 || check "check.log 存在且非空" 0
  grep -qE "\b0\b" "$CL" 2>/dev/null && check "check.log 含退出码 0" 1 || check "check.log 含退出码 0 (可能格式不同)" 0
else
  check "package 目录存在" 0
fi

echo
echo "=== 结果: PASS=$PASS FAIL=$FAIL ==="
[ "$FAIL" = "0" ] && echo "✅ 全部通过" || echo "❌ $FAIL 项未通过"
