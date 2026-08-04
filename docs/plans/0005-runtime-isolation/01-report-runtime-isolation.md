---
title: Report 005 — Benchmark Runtime Isolation
description: 记录 Docker 隔离边界、profile、恶意路径探针、timeout 清理、submission 收集与残余风险的实现和验收证据。
type: report
status: complete
created: 2026-07-21T00:00:00Z
---

# 结果

Plan 005 已在 commit `c12e5e1` 实现通用 Docker sandbox。Runner/Curator 在宿主机校验
entry 并 stage 公开 InputBundle，被测系统只接收 container 内的 `/input`、`/workspace`
和 `/output` 路径。Private evaluator 仍在被测进程结束后于可信宿主侧运行。

# 实现

- `DockerSandbox` 构建只读 root、非 root UID/GID、capability drop、
  `no-new-privileges`、CPU/memory/PID 限制与受限 tmpfs。
- `/input` 只读；`/workspace` 与 `/output` 可写；三个宿主目录必须存在、互不相同且
  不得形成父子嵌套。
- `offline` 使用 `--network none`；`discovery` 与 `tool-runtime` 使用 Docker bridge；
  所有 profile 均不暴露 Docker socket。
- CLI 要求显式 sandbox image，支持 profile、timeout 和 env name allowlist；没有镜像时
  host execution 被禁用。
- 每次运行使用唯一 container name。Deadline 到达后 runner 强制执行 `docker rm -f`，
  避免只终止 Docker client 而让 container 后台存活。
- Adapter 仅传递 `/input/...` 和 `/output`，保存 stdout/stderr，并在 nonzero exit、
  timeout 或 runtime 缺失时生成 blocked submission。成功 submission 记录 runtime、
  profile 与 image provenance。
- GitHub Actions 增加独立 Docker isolation probe step；它不运行全部 benchmark entry。

# 验证证据

| Gate | 结果 | 说明 |
|------|------|------|
| 完整确定性测试 | PASS | `73 passed, 4 skipped`；Docker probe 默认显式跳过 |
| 真实 Docker probe | PASS | `RUN_DOCKER_ISOLATION_TESTS=1 ...` 得到 `4 passed` |
| Lint/bundle gate | PASS | `make lint`，六个 entry 全部 VALID |
| Python compile | PASS | runner、sandbox、adapter、CLI 与测试文件均通过 `py_compile` |
| Diff hygiene | PASS | `git diff --check` 无错误 |
| Hosted CI execution | PENDING | workflow gate 已配置；本分支未 push，未声称 GitHub Actions 已运行 |

真实 Docker 探针验证了以下能力：

1. 被测进程不是 root；`/input` 可读但不可写；container root 只读；两个输出目录可写。
2. 临时 private oracle、相邻 entry oracle、仓库 `.git/config` 和 Docker socket 均不可见。
3. `offline` 只有 loopback；`discovery` 有 container network，但仍无宿主 runtime socket。
4. 超时 container 被强制删除，不留 stopped/running container。
5. Container 生成的 result table 与 log 可由 host-side collector 写入 submission manifest。

验证按隔离能力/profile 取样，不对六个 benchmark 各跑一遍。文件系统与 network boundary
由同一个 sandbox 实现，逐 entry 重复运行不会增加新的隔离证明；科学正确性仍由各 entry
的 evaluator 与后续 release run 负责。

# AC 与完成条件

| 条目 | 结果 | 证据 |
|------|------|------|
| AC-0005-N-1/N-2 | PASS | sandbox 输出仍被标准化为 submission artifacts 与 stages |
| AC-0005-N-3 | PASS | host absolute path、相邻 oracle、`.git` 与 Docker socket escape probe 被拒绝 |
| AC-0005-B-1 | PASS | adapter 保留 blocked/partial artifact 协议路径 |
| 失败与 timeout | PASS | nonzero exit 生成 blocked submission；timeout 有稳定错误并清理 container |
| Profile coverage | PASS | 三种 profile 的 command policy 有单测，offline/discovery 有真实 Docker 探针 |
| CI gate | PASS（配置） | CI 明确启用真实 Docker probe；托管执行结果留待 branch push/PR |

# 残余风险

- 本边界依赖 Docker daemon、默认 seccomp 与宿主 kernel，不覆盖 runtime/kernel escape。
- `discovery`/`tool-runtime` 允许网络。显式传入的凭据可能被恶意被测系统外传，因此凭据
  必须最小权限、短期有效且独立计费；本 Plan 不提供网络 egress allowlist。
- Container 启动与 bind mount 存在固定开销。本轮只验证功能，没有建立可跨平台解释的
  性能基线；四个 probe 的总时长包含一个强制 1 秒 timeout，不能作为运行开销指标。
- CI 使用 `alpine:3` probe image，首次运行依赖 registry 可用性。
- 当前没有可发布的完整 bio-reproducer sandbox image。bench-100 历史工具链和 L4 镜像
  仍由 Plan 002 冻结；Plan 005 完成的是通用执行边界，不代表六个 entry 已完成发布运行。

# 结论

Plan 004 留下的宿主文件系统越界风险已由通用 container boundary 覆盖。Plan 005 可以
标记 done；下一步是 Plan 002 构建实际系统镜像并在该边界内执行 bench-100 smoke，随后
进入 release-gated benchmark 运行与 baseline 判定。
