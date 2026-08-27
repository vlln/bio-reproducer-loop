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
Package（check.log）。**重跑前置**：修或规避 agent 调用挂起（loopflow 无 agent
超时——BL-013；可加 claude 侧 `--max-turns`/会话超时，或接受低概率重跑）。

### 监控方法教训

container.log 无新行 ≠ 挂起：需用 `docker top` 看 claude 子进程树区分
「等待长命令」（bash/mip/docker pull 存活 = 正常）与「API 挂起」
（无子进程 + 会话文件停滞 + loop CPU 不增长 = 挂起）。两次误判：
mip pull 慢曾误判为挂起（有子进程实为正常）；此后用进程树判断才准确。

