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

## 运行状态（进行中）

- entry: bench-220（3 claims，NHANES，之前 ~1h15m）
- 第四次启动后 **Reader agent 正常运行**：paperutils 技能可用、WebFetch blocked 后
  curl 兜底、PMC 全文获取中
- 监控：loop 定时检查 container.log + 产物目录

## 完成后补全

- [ ] run 结束（进程消失）后：产物核验（04_data 日志/sha256sums、03_provision
  digests、05_run results/answers、06_validate routing.jsonl、07_package check.log）
- [ ] evaluate_run.py 新证据流评估
- [ ] 验证目标核对：动态路由（routing.jsonl 回环）、新基建（dind/续传/技能）、
  新契约闭环（answers 交叉核对）
- [ ] 归档 run + 更新 calibration-assets.md
- [ ] 删远端 bench-v3.sh（run-entry.sh 跑通后）
