#!/usr/bin/env bash
# 校准/验证用 harness（Plan 0026-01）——取代仅存在于远端、未纳入版本管理的 bench-v3.sh
#
# 与 bench-v3.sh 的关键差异（BL-018 / BL-021）：
#   1) 不再挂载 /var/run/docker.sock 与整个 $HOME —— 沙箱内不再等于宿主 root
#   2) 容器运行时改为**每 run 一个 dind sidecar**（privileged 只落在 sidecar 上，
#      沙箱本身保持 --cap-drop ALL --user 1000:1000 零特权）
#   3) sidecar 与沙箱把 run 目录挂在**相同路径**（/input /workspace /output），
#      因此沙箱内 `docker run -v /output/...:/x` 的挂载对 dind daemon 是真实路径
#      —— 这正是 19 个 run 里 Nextflow docker executor 挂载失败、被迫退回
#      手工 docker run + docker cp 的根因（挂宿主 socket 时路径对宿主 daemon 不存在）
#   4) 技能前置（requires.bins / requires.env）在启动前由 harness-probe.sh 校验
#   5) loop 定义（loops/bio-reproducer/）从 $REPO 只读挂载到沙箱
#      ~/.loopflow/loops/bio-reproducer —— loopflow 从那里加载 agents/workflow.py
#      （2026-08-27 首跑补齐：selftest 不跑 loop，此路径此前未覆盖）
#
# 注意：dind 需要 --privileged，其内核暴露面仍大于 VM。开发/校准可用；
# **可发布的正式结果仍须按 ADR-0009 / BR-013 走 disposable VM**，两者不可混同。
#
# 用法:
#   bash run-entry.sh selftest                 # 只跑边界自检，不跑 entry
#   bash run-entry.sh <entry-id> [repo_dir]    # 跑一个 entry
set -uo pipefail

MODE="${1:?用法: run-entry.sh <entry-id|selftest> [repo_dir]}"
REPO="${2:-$HOME/bio-reproducer}"
IMAGE="${HARNESS_RUNTIME_IMAGE:-bio-reproducer-runtime:system-idlefix-cc247}"
DIND_IMAGE="${HARNESS_DIND_IMAGE:-docker:latest}"
SKILLS_DIR="${HARNESS_SKILLS_DIR:-$HOME/.agents/skills}"
STAMP=$(date +%Y%m%d-%H%M%S)
RUN="${HARNESS_RUN_ROOT:-/tmp/harness}/run-$MODE-$STAMP"
NET="harness-$MODE-$STAMP"
DIND="dind-$MODE-$STAMP"

cleanup() {
  docker rm -f "$DIND" >/dev/null 2>&1
  docker network rm "$NET" >/dev/null 2>&1
}
trap cleanup EXIT

mkdir -p "$RUN/input" "$RUN/workspace" "$RUN/repro-data"
chmod -R 777 "$RUN"
docker network create "$NET" >/dev/null

# 镜像加速：dind 是全新 daemon，不继承宿主 /etc/docker/daemon.json 的 registry-mirrors。
# 远端 Docker Hub 直连被墙（BL-008；实测 registry-1.docker.io i/o timeout），
# 不透传 mirror 会导致任务容器**一个镜像都拉不下来**。默认取宿主同款 mirror。
MIRRORS="${HARNESS_REGISTRY_MIRRORS:-$(docker info --format '{{range .RegistryConfig.Mirrors}}{{.}} {{end}}' 2>/dev/null)}"
MIRROR_ARGS=""
for m in $MIRRORS; do MIRROR_ARGS="$MIRROR_ARGS --registry-mirror=${m%/}"; done
[ -n "$MIRROR_ARGS" ] && echo "dind registry mirrors:$MIRROR_ARGS"

# dind sidecar：privileged 仅在此处；不挂宿主 socket；run 目录路径与沙箱一致
docker run -d --privileged --network "$NET" --name "$DIND" \
  -e DOCKER_TLS_CERTDIR="" \
  -v "$RUN/repro-data:/output" -v "$RUN/workspace:/workspace" -v "$RUN/input:/input:ro" \
  "$DIND_IMAGE" dockerd-entrypoint.sh --host=tcp://0.0.0.0:2375 $MIRROR_ARGS >/dev/null

# 等 daemon 就绪（轮询，不睡死）
for _ in $(seq 1 30); do
  docker run --rm --network "$NET" -e DOCKER_HOST="tcp://$DIND:2375" "$DIND_IMAGE" \
    docker version --format '{{.Server.Version}}' >/dev/null 2>&1 && break
  sleep 2
done

# 运行时镜像内无 docker CLI（实测 MISSING），只挂**客户端二进制**（只读）。
# 与 bench-v3.sh 的区别：只给 CLI，不给 /var/run/docker.sock —— CLI 通过
# DOCKER_HOST 指向 dind，宿主 daemon 全程不可达。
DOCKER_BIN="${HARNESS_DOCKER_BIN:-$(command -v docker)}"

# Claude Code backend（远端 dashscope proxy，见 ~/.claude/settings.json 的 env 块）：
# 只注入 env（--env-file），不挂载整个 ~/.claude（含 session 历史）。
# 首跑实测：沙箱 HOME 无 settings.json、env 未传 → agent 无法连接后端，
# Reader 无产物 → 前置产物缺失 fail-fast（2026-08-27）。
BACKEND_ENV="$RUN/backend.env"
CLAUDE_SETTINGS="${HARNESS_CLAUDE_SETTINGS:-$HOME/.claude/settings.json}"
ENVFILE_ARG=""
if [ -f "$CLAUDE_SETTINGS" ]; then
  python3 - "$CLAUDE_SETTINGS" "$BACKEND_ENV" <<'PY' 2>/dev/null || true
import json, sys
settings, out = sys.argv[1], sys.argv[2]
d = json.load(open(settings))
with open(out, "w") as f:
    for k, v in (d.get("env") or {}).items():
        f.write(f"{k}={v}\n")
PY
  [ -s "$BACKEND_ENV" ] && ENVFILE_ARG="--env-file $BACKEND_ENV"
fi

sandbox() {  # sandbox <image> <cmd...>：零特权沙箱，容器运行时指向 dind
  local img="$1"; shift
  # 整个 /home/sandbox 挂载为可写 volume（uid 1000 需要写 ~/.claude session 与
  # ~/.loopflow/runs；镜像内无 /home/sandbox，docker 自动创建为 root 属主——
  # 首跑实测 claude 写 session 静默失败 → Reader 无产物，2026-08-27）。
  # .loopflow 必须在宿主预建并 777：docker 为嵌套挂载（skills）预建的目录
  # 属主 root，uid 1000 仍不可写 runs/（第二次迭代实测）。
  # skills / loop 定义为嵌套子挂载（只读）。
  # .claude/skills：claude 自动发现技能目录（BL-029：loopflow 只把技能注入
  # prompt 文本，claude 的 Skill 工具查 ~/.claude/skills/ 找不到 → Unknown skill；
  # 挂到此处让 Skill 工具可用）。
  mkdir -p "$RUN/home/.loopflow" "$RUN/home/.claude/skills" && chmod -R 777 "$RUN/home"
  docker run --rm -i --network "$NET" \
    --user 1000:1000 --cap-drop ALL --security-opt no-new-privileges \
    --workdir /workspace \
    ${DOCKER_BIN:+-v "$DOCKER_BIN:/usr/bin/docker:ro"} \
    -v "$RUN/input:/input:ro" -v "$RUN/workspace:/workspace" -v "$RUN/repro-data:/output" \
    -v "$RUN/home:/home/sandbox" \
    -v "$SKILLS_DIR:/home/sandbox/.loopflow/skills:ro" \
    -v "$SKILLS_DIR:/home/sandbox/.claude/skills:ro" \
    -v "$REPO/loops/bio-reproducer:/home/sandbox/.loopflow/loops/bio-reproducer:ro" \
    -e HOME=/home/sandbox \
    -e DOCKER_HOST="tcp://$DIND:2375" \
    ${MINERU_API_URL:+-e MINERU_API_URL="$MINERU_API_URL"} \
    ${ENVFILE_ARG} \
    "$img" "$@"
}

if [ "$MODE" = "selftest" ]; then
  echo "=== harness selftest run=$RUN net=$NET"
  echo "hello-from-host" > "$RUN/repro-data/probe.txt"
  sandbox "$DIND_IMAGE" sh -s <<'SELF'
set -u
echo -n "1) 沙箱能否连到 dind daemon: "
docker version --format 'server={{.Server.Version}}' 2>&1 | head -1
echo -n "2) 宿主 docker.sock 是否泄漏: "
if [ -S /var/run/docker.sock ]; then echo "泄漏-FAIL"; else echo "不可见-OK"; fi
echo "3) 任务容器挂载沙箱内路径（Nextflow work 同构）:"
docker run --rm -v /output:/data alpine:latest cat /data/probe.txt 2>&1 | sed 's/^/     /'
echo -n "4) 任务容器写回的文件沙箱可见: "
docker run --rm -v /output:/data alpine:latest sh -c 'echo written-by-task > /data/back.txt' >/dev/null 2>&1
[ -f /output/back.txt ] && cat /output/back.txt || echo "不可见-FAIL"
SELF
  echo -n "5) 宿主侧也能看到任务容器写回的文件: "
  [ -f "$RUN/repro-data/back.txt" ] && cat "$RUN/repro-data/back.txt" || echo "不可见-FAIL"

  # 6) Plan 0026-01 的 DinD 验收判据：运行时镜像内用 Nextflow docker executor 跑通
  #    （19 个 run 正是在这一步失败后退回手工 docker run + docker cp）
  echo "6) 运行时镜像 + Nextflow docker executor:"
  sandbox "$IMAGE" bash -s <<'NF'
set -u
echo -n "   docker CLI 可用: "; command -v docker >/dev/null && docker version --format 'server={{.Server.Version}}' 2>&1 | head -1 || echo FAIL
mkdir -p /workspace/nftest && cd /workspace/nftest
cat > main.nf <<'PIPE'
process SMOKE {
  container 'ubuntu:22.04'  // 需带 /bin/bash：Nextflow docker executor 以 /bin/bash -ue 启动
  publishDir '/output/nfsmoke', mode: 'copy'
  output: path 'nf_ok.txt'
  script:
  """
  echo nextflow-docker-executor-ok > nf_ok.txt
  """
}
workflow { SMOKE() }
PIPE
cat > nextflow.config <<'CFG'
docker.enabled = true
docker.runOptions = '-u 1000:1000'
CFG
NXF_HOME=/workspace/.nextflow timeout 240 nextflow -q run main.nf 2>&1 | tail -12
if [ -f /output/nfsmoke/nf_ok.txt ]; then
  echo -n "   产物: "; cat /output/nfsmoke/nf_ok.txt
else
  echo "   产物: 未生成-FAIL；诊断如下"
  echo "   --- .command.err:"; find work -name .command.err 2>/dev/null | head -1 | xargs -r tail -8 | sed 's/^/     /'
  echo "   --- .command.run 里的 docker 命令:"; find work -name .command.run 2>/dev/null | head -1 | xargs -r grep -m2 -n "docker run" | sed 's/^/     /'
  echo "   --- .nextflow.log:"; tail -12 .nextflow.log 2>/dev/null | sed 's/^/     /'
fi
NF
  exit 0
fi

# ---- 正式跑一个 entry ----
ENTRY="$MODE"
cp -r "$REPO/benchmarks/entries/$ENTRY/input/." "$RUN/input/"
DOI=$(sed -n 's/^DOI: //p' "$REPO/benchmarks/entries/$ENTRY/input/paper/locator.md" | head -1)
ARXIV=$(sed -n 's/^arXiv: //p' "$REPO/benchmarks/entries/$ENTRY/input/paper/locator.md" | head -1)
ID="${DOI:-arXiv:$ARXIV}"
TASK=$(python3 -c "import yaml,json;print(json.dumps(yaml.safe_load(open('$REPO/benchmarks/entries/$ENTRY/metadata.yaml')).get('task','')))")
SCOPE_ARG=""
[ "$TASK" != '""' ] && SCOPE_ARG=",\"scope\":$TASK"

echo "entry=$ENTRY id=$ID run=$RUN"

# 任务公开问题清单（ADR-0011 §4.1）：评测方把 entry 的 input/questions.yaml 翻译成
# 注入段（--append-prompt，loopflow 原生，注入每个 agent 的 user prompt 末尾）
# + 键列表（args.question_keys 供系统侧 lint 键对齐校验）。系统侧不读文件——
# 问题清单的存在/位置是评测方职责（2026-08-27 分层讨论）。
QUESTIONS_JSON=$(python3 - "$REPO" "$REPO/benchmarks/entries/$ENTRY/input" <<'PY' 2>/dev/null
import json, sys
sys.path.insert(0, sys.argv[1] + "/benchmarks/harness")
from questions_inject import build_questions_injection
injection, keys = build_questions_injection(sys.argv[2])
print(json.dumps({"injection": injection, "keys": keys}))
PY
)
Q_INJECTION=$(echo "$QUESTIONS_JSON" | python3 -c "import json,sys;print(json.load(sys.stdin)['injection'] or '')")
Q_KEYS=$(echo "$QUESTIONS_JSON" | python3 -c "import json,sys;print(json.dumps(json.load(sys.stdin)['keys']))")
APPEND_ARG=""
[ -n "$Q_INJECTION" ] && APPEND_ARG=",\"question_keys\":$Q_KEYS"

echo "entry=$ENTRY id=$ID run=$RUN"
sandbox "$IMAGE" \
  loop run bio-reproducer --work-dir /output \
  --args "{\"paper_doi\":\"$ID\",\"language\":\"zh\",\"confirm_plan\":false,\"consent\":\"auto\"$SCOPE_ARG$APPEND_ARG}" \
  ${Q_INJECTION:+--append-prompt "$Q_INJECTION"} \
  > "$RUN/container.log" 2>&1
echo "exit=$? log=$RUN/container.log"
