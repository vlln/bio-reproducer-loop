---
title: Plan 009 — Opaque Bio-Reproducer System Artifact
description: 构建可校验、自包含的 bio-reproducer system artifact，以稳定 launcher 接入 disposable VM，并正式 smoke 一个构造 entry。
type: plan
status: done
created: 2026-07-23T00:00:00Z
---

# Context

Plan 008 已证明 disposable QEMU/KVM worker、I/O boundary、nested Docker、deadline 和 teardown
可用，但只注入了 fake system。当前 adapter 直接调用 guest PATH 中的 `loop`，完整系统则依赖
本机可变的 `.pixi/`、`.skills/`、用户级 loopflow 安装和 provider 配置，尚不能作为按 digest
固定的 opaque artifact 注入 VM。

# Request

构建一个由 adapter 管理的 bio-reproducer system artifact。制品提供稳定的
`/system/run-system` launcher，在内部设置 loopflow、loop、skills、Pixi/runtime 与必要配置；
公开 benchmark 协议仍只看到 system digest 和 adapter identity，不暴露内部 runtime taxonomy。
完成确定性契约测试后，在 `gs` 的 fresh disposable VM 中正式运行一次 `bench-001`。

# Output Format

1. `benchmarks/runner/system_artifact.py`：显式构建输入、manifest、稳定 tree digest 与校验。
2. `benchmarks/runner/system_artifact/`：launcher 和必要的构建资源，不包含本机生成状态。
3. Adapter/CLI：正式运行使用稳定 launcher，并可构建或检查 system artifact。
4. Unit/contract tests：覆盖正常、边界、异常和失败路径。
5. Report：记录构建输入版本、digest、VM execution envelope、smoke 结果和清理证据。

# Constraints

- 不复制当前工作区的 `.pixi/`、`.skills/`、`.local/` 或用户 home。
- `loop.md` 必须成为受 Git 管理的 loop source，不从本机 ignored 文件隐式获取。
- Loopflow source/version、`pixi.lock` digest、skills 名称与内容 digest必须进入 manifest。
- Secret 只记录逻辑名称；token、API key、provider credential 和用户配置不得进入制品或 manifest。
- 制品不得包含 entry input、oracle、历史 results 或 benchmark repository。
- Worker base 保持最小；bio-reproducer、MinerU、R 与科学环境仍属于 system/guest 内部。
- 正式路径固定 QEMU/KVM；Docker 仅用于 validation，不产生可发布结果。
- 本 Plan 只运行一次 `bench-001`，不运行其他 entry，不建立 baseline。
- 不修改或清理远端 `~/bio-reproducer`，远端临时产物位于 `/tmp` 并在验收后审计清理。
- 不 push；只有用户明确要求时才 push。

# Checkpoints

| 编号 | 终止条件 |
|------|----------|
| CP-1 | Artifact contract、manifest schema、launcher 与 adapter tests 全部通过 |
| CP-2 | 本地 fake provider/launcher smoke 证明 loop discovery 和 I/O 参数正确 |
| CP-3 | `gs` 构建可校验 artifact，fresh VM 中一次 `bench-001` 产生真实 submission |
| CP-4 | Release gate、teardown、远端 residue audit 与本地全量门禁通过 |

若 CP-1 表明 pinned runtime 无法自包含，停止真实 entry smoke并在 Report 中分类为设计缺陷；
不得回退到 host 或 Docker formal run。若 CP-3 的科学执行失败但 artifact、launcher、VM 与
teardown 契约成立，保留 blocked submission 并将失败归类为 system capability，而不是伪造成功。

# Steps

1. 将 `loop.md` 纳入受控 source，枚举 agent 声明的 skills 和 runtime 输入。
2. 先写 artifact manifest、路径边界、symlink、secret、digest 和 launcher contract tests。
3. 实现 deterministic builder/validator 与稳定 `/system/run-system` launcher。
4. 将 adapter 从 guest PATH 中的裸 `loop` 切换到 artifact launcher，保留公共协议不变。
5. 以 fake backend 验证 launcher 设置的 loop discovery、参数和输出边界。
6. 在 `gs` 使用 pinned inputs 构建 artifact，并复用 Plan 008 worker recipe。
7. 通过实际 QEMU/KVM adapter 正式运行一次 `bench-001`，执行 release check。
8. 运行全量确定性测试、lint、bundle validation 和 residue audit，完成 Report。

# Acceptance

| 编号 | 条件 | 对应 AC |
|------|------|---------|
| SA-001 | 相同输入两次构建得到相同 manifest 与 tree digest | AC-0008-E-2 |
| SA-002 | Symlink、越界路径、mutable generated state 和 secret value 被拒绝 | AC-0008-E-2/B-2 |
| SA-003 | Launcher 只依赖 `/system`、`/input`、`/workspace`、`/output` contract | AC-0008-N-2/F-2 |
| SA-004 | Manifest 固定 loopflow、loop source、Pixi lock 与 skills provenance | AC-0008-N-4 |
| SA-005 | Adapter 使用 `/system/run-system` 且 Docker 仍是 validation-only | AC-0008-B-3/B-4 |
| SA-006 | `bench-001` fresh VM run 生成 formal ExecutionEnvelope 和真实 submission | AC-0008-N-1/N-3/N-4 |
| SA-007 | Success、blocked 或 timeout 均保留实际 artifacts 并完成 teardown | AC-0008-F-1/F-3 |
| SA-008 | 普通 tests、lint、bundle validators 和远端 residue audit 通过 | DEVELOP gate |
