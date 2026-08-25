#!/usr/bin/env bash
# harness 前置探针（Plan 0026-01 交付物）
#
# 用途：在**与正式 run 相同的容器配置**下，实测三类前置条件并留下可复现记录：
#   1) 出口网络：论文/数据源各打一次真实请求，记录状态码与耗时
#   2) 下载工具：curl / wget / 断点续传能力
#   3) 技能前置：解析每个挂载技能的 SKILL.md 中 `requires.bins` / `requires.env`，
#      逐项验证是否满足 —— loopflow 的 check_skills 只验 SKILL.md 是否存在，
#      不验技能自己声明的前置（BL-026），因此这一段是必需的补充校验
#
# 背景：BL-019 曾被两次误诊（先判「技能注入有 bug」，再判「容器出口网络不通」），
# 两次都是拿单行日志当根因。第三次实测才定位到「技能声明的前置从未被满足」。
# 本脚本存在的意义就是让这类判断必须基于实测，而不是日志措辞。
#
# 用法（远端）：
#   bash harness-probe.sh [runtime_image] [skills_dir]
set -uo pipefail

IMAGE="${1:-bio-reproducer-runtime:system-idlefix}"
SKILLS_DIR="${2:-$HOME/.agents/skills}"

echo "=== harness probe: image=$IMAGE skills=$SKILLS_DIR ts=$(date -Iseconds)"

# 与 bench-v3.sh 一致的安全 flags（不含 docker.sock —— 见 BL-018）
docker run --rm -i --network bridge --user 1000:1000 \
  --cap-drop ALL --security-opt no-new-privileges \
  --mount "type=bind,src=$SKILLS_DIR,dst=/home/sandbox/.loopflow/skills,readonly" \
  --env HOME=/home/sandbox \
  "$IMAGE" bash -s <<'PROBE'
set -uo pipefail
fail=0

echo "--- [1] 出口网络"
for u in \
  "https://api.crossref.org/works/10.1136/bmjebm-2023-112303" \
  "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12874334/fullTextXML" \
  "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE289nnn/GSE289881/" ; do
  host=$(echo "$u" | cut -d/ -f3)
  out=$(curl -s -o /dev/null -w "code=%{http_code} t=%{time_total}s size=%{size_download}" --max-time 30 "$u" 2>&1) \
    || { echo "  FAIL $host ($out)"; fail=1; continue; }
  case "$out" in *code=200*) echo "  OK   $host  $out";; *) echo "  FAIL $host  $out"; fail=1;; esac
done

echo "--- [2] 下载工具"
for b in curl wget aria2c; do
  if command -v "$b" >/dev/null 2>&1; then echo "  OK   $b"; else echo "  MISS $b"; [ "$b" = curl ] && fail=1; fi
done
# 断点续传能力（curl -C - 需服务端支持 Range；此处只验本地 flag 可用）
curl --help all 2>/dev/null | grep -q -- "-C, --continue-at" && echo "  OK   curl 支持 --continue-at" || { echo "  MISS curl 断点续传"; fail=1; }

echo "--- [3] 技能前置（解析 SKILL.md 的 requires.bins / requires.env）"
python3 - <<'PY'
import os, re, sys
from pathlib import Path

base = Path("/home/sandbox/.loopflow/skills")
bad = []
for d in sorted(p for p in base.iterdir() if p.is_dir()):
    f = d / "SKILL.md"
    if not f.is_file():
        continue
    text = f.read_text(errors="replace")
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        continue
    fm = m.group(1) + "\n"  # 末行补换行：否则 requires 段最后一项会被漏掉
    # 不引入 yaml 依赖：只抓 requires 段内的 bins / env 列表项
    req = re.search(r"^requires:\n((?:[ \t]+.*\n)+)", fm, re.M)
    blocks = [req.group(1)] if req else []
    # skit 风格：metadata.skit.requires
    for m2 in re.finditer(r"^[ \t]+requires:\n((?:[ \t]+.*\n)+)", fm, re.M):
        blocks.append(m2.group(1))
    bins, envs = set(), set()
    for blk in blocks:
        cur = None
        for line in blk.splitlines():
            s = line.strip()
            if s.startswith("bins:"):
                cur = bins; continue
            if s.startswith("env:"):
                cur = envs; continue
            if s.startswith("- ") and cur is not None:
                cur.add(s[2:].strip())
            elif s and not s.startswith("-") and s.endswith(":"):
                cur = None
    for b in sorted(bins):
        ok = any((Path(p) / b).is_file() for p in os.environ.get("PATH", "").split(":") if p)
        print(f"  {'OK  ' if ok else 'MISS'} {d.name}: bin {b}")
        if not ok:
            bad.append(f"{d.name}:bin:{b}")
    for e in sorted(envs):
        ok = bool(os.environ.get(e))
        print(f"  {'OK  ' if ok else 'MISS'} {d.name}: env {e}")
        if not ok:
            bad.append(f"{d.name}:env:{e}")
    if not bins and not envs:
        print(f"  --   {d.name}: 未声明前置")
print(f"未满足前置数: {len(bad)}" + (f" -> {', '.join(bad)}" if bad else ""))
sys.exit(1 if bad else 0)
PY
[ $? -ne 0 ] && fail=1

echo "--- 结论: $([ $fail -eq 0 ] && echo ALL-PASS || echo HAS-FAILURE)"
exit $fail
PROBE
