# Report 07 — run-entry.sh 端到端首跑（进行中）

> 2026-08-27。目的：验证单元 01-06 改动（dind 新基建、动态路由、新契约闭环）。
> 本报告记录首跑暴露的 harness 缺口与修复（已完成部分）；run 结果待完成后补全。

## 首跑暴露的三个缺口（全部已修复，commit 逐条记录）

selftest（单元 01）只覆盖边界自检，**不跑 loop**——完整 entry 首跑暴露三个
「selftest 覆盖不到」的缺口：

| # | 缺口 | 现象 | 修复 | commit |
|---|------|------|------|--------|
| 1 | sandbox 未挂载 loop 定义 | `loop run bio-reproducer` 在沙箱找不到 loop（~/.loopflow/loops/） | 挂载 `$REPO/loops/bio-reproducer` → `/home/sandbox/.loopflow/loops/bio-reproducer:ro`（loop 定义与 entry input 同源） | 8744861 |
| 2 | backend env 未进沙箱 | Claude Code 无 ANTHROPIC_* env（宿主配置在 ~/.claude/settings.json）→ Reader 无产物 fail-fast | 从宿主 settings.json 的 env 块生成 `--env-file` 注入（最小暴露：只传 env，不挂 .claude 目录） | 3e2fa22* |
| 3 | /home/sandbox 不可写 | 镜像内无 /home/sandbox（docker 自动创建 root 属主）→ claude 写 ~/.claude session 静默失败；迭代 2：skills 嵌套挂载使 docker 预建 .loopflow 仍 root 属主 | 整个 /home/sandbox 挂载 `$RUN/home`（777）+ **宿主预建 `.loopflow` 777**（防 docker root 预建） | 2 个 commit |

诊断方法（可复用）：宿主对照组（`claude -p` 在宿主 OK、沙箱静默 → 环境差异定位到
HOME 可写性）；container.log 的 fail-fast 时序（几秒内「前置产物缺失」= agent 调用
未产出，非正常快速完成）。

## 运行结果（2026-08-27 补全）

- entry: bench-220，run 目录 `/tmp/harness/run-bench-220-20260827-113053`，
  已归档 `/storeData/gs/claroai-calibration/runs/bench-220-0026-run1/`
- **终止于 Provision 收尾**：agent API 调用挂起（claude 会话 45+ 分钟无活动、
  无子进程、loop CPU 停滞——BL-013 已知「LLM 长会话无超时」缺陷的又一次实证，
  bench-229 曾挂 6.5h 同类）。后端健康（dashscope 200/1.35s）——挂起在 claude CLI
  侧连接，非我们的改动缺陷。已 kill + 清理，产物保留。

## BL-013 根因确认与修复（2026-08-27 续）

挂起后排查（非猜测，全部实测）：
1. **会话文件定位挂起点**：最后事件 = `assistant thinking`（12:44:22，
   「Now let me finalize the provision.md…」）——模型思考完毕**正要发 Edit tool_use
   时 SSE 流静默中断**，assistant 消息永远不完整，claude CLI 无超时等待。
2. **排除服务端**：curl 直连 dashscope（普通流 / thinking+工具 / 强制 tool_use /
   重放挂起会话 201 条历史）全部完整结束（message_stop 正常），4 次测试 0 挂起；
   claude CLI 多轮工具循环（3 步、15 步）也正常——**是偶发静默断流，非确定性路径**。
3. **确认 `API_TIMEOUT_MS` 对流式无效**：设 30000ms 实测 150s 仍未触发（该变量只
   作用于请求建立，不覆盖流式读取）；且宿主配置 3000000ms（50min）是放大器。
4. **定位上游根因**：Claude Code 官方 changelog——
   - v2.1.196（2026-06-29）：「streaming idle watchdog 现**对所有 provider 默认开启**，
     5 分钟无事件即 abort+retry」——我们镜像里的 **2.1.126 在此版本之前**，
     对非官方端点（dashscope 走 ANTHROPIC_BASE_URL）看门狗默认关闭。
   - v2.1.210（2026-07-14）：「新增 `CLAUDE_STREAM_IDLE_TIMEOUT_MS`（默认 90s）」。
   - 另有条目精确对应本症状：「Fixed a hang where the assistant could finish
     thinking but show no output after a run of empty turns」。

### BL-013 修复（已落地）

| 层 | 动作 | 状态 |
|----|------|------|
| 主防：claude 版本 | runtime 镜像内 claude 2.1.126 → **2.1.247**（npm 全局包），commit 为 `bio-reproducer-runtime:system-idlefix-cc247` | ✅ |
| 主防：watchdog 配置 | 宿主+远端 `~/.claude/settings.json` env 块加 `CLAUDE_ENABLE_STREAM_WATCHDOG=1` + `CLAUDE_STREAM_IDLE_TIMEOUT_MS=300000`（5min，官方 clamp 10s~30min 内） | ✅ |
| 主防：harness | run-entry.sh 默认镜像改 `system-idlefix-cc247`（`HARNESS_RUNTIME_IMAGE` 可覆盖）；backend.env 自动透传新变量（settings.json env 块直出） | ✅ |
| 兜底：loopflow | `CliTransport` 空闲看门狗完善为**子进程感知**：idle 超时但子进程存活（mip/docker pull 长命令）继续等，无子进程才 kill；默认 43200s→7200s；新增 7 测试；提交 loopflow develop `4b9bdf7` | ✅ |
| 验证 | 新镜像 claude 2.1.247 真实 dashscope 冒烟 EXIT=0；loopflow 全量 446 passed；harness selftest 6/6（含 Nextflow docker executor，ubuntu:22.04 经 mirror pull） | ✅ |

注意：升级镜像内 claude 2.1.247 后，模型名验证更严格（mock 端点
`unrecognized_model` 会被拒）；真实 dashscope 链路不受影响（冒烟已证）。

### 已验证（首跑目的部分达成）

| 验证项 | 结果 |
|--------|------|
| dind 新基建（无 docker.sock、registry-mirror 透传、任务容器挂载） | ✅ 镜像经 dind 拉取成功（rocker/r-ver 1.21GB + r-base 1.17GB） |
| loop 定义挂载（run-entry.sh 修复 1） | ✅ `loop run bio-reproducer` 正常加载 workflow/agents |
| backend env 注入（修复 2） | ✅ Reader 正常调用 claude（dashscope deepseek-v4-pro） |
| HOME 可写（修复 3） | ✅ claude 会话写入正常 |
| 技能补齐（单元 02）：paperutils + mineru-api | ✅ Reader 真实使用（paperutils 元数据 + mineru-api PDF 转换，WebFetch blocked 后 curl 兜底） |
| goal 从 plan.md 派生（单元 03） | ⏳ 未直接观察（container.log 无 goal 日志；plan.md 已产出待核对） |
| provision 契约 digests.txt（单元 04） | ✅ `03_provision/digests.txt` 落盘（docker images --digests 原始输出） |
| provision 纪律（镜像复用/技能/mip） | ✅ mip pull 走 image-mirror-skill + 交互验证后固化 Dockerfile；SAS 正确标 out-of-scope |
| 动态路由 / answers / routing.jsonl / check.log | ⏳ 未到阶段（Data/Run/Validate/Package 未执行） |

### 未验证（需重跑）

Data（curl -C - 续传）、Run（answers.csv）、Validate（routing.jsonl 回环）、
Package（check.log）。**重跑前置已解决**：BL-013 根因确认（claude 2.1.126 对第三方
端点 SSE 看门狗默认关闭）+ 官方修复（升级 2.1.247 + `CLAUDE_STREAM_IDLE_TIMEOUT_MS`）
+ loopflow 兜底（子进程感知看门狗）——见上文 BL-013 修复表，可直接重跑。

### 监控方法教训

container.log 无新行 ≠ 挂起：需用 `docker top` 看 claude 子进程树区分
「等待长命令」（bash/mip/docker pull 存活 = 正常）与「API 挂起」
（无子进程 + 会话文件停滞 + loop CPU 不增长 = 挂起）。两次误判：
mip pull 慢曾误判为挂起（有子进程实为正常）；此后用进程树判断才准确。

