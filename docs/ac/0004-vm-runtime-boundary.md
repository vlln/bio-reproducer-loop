---
title: AC 004 — Disposable VM Runtime Boundary
description: 验收正式 benchmark 的 disposable VM 生命周期、guest 权限、control-plane 隔离、I/O、provenance 和 teardown。
type: ac
status: proposed
created: 2026-07-22T00:00:00Z
---

# AC-0008: Disposable VM 正式执行

验证所有可发布 benchmark 结果来自同一个 disposable VM boundary。

## 正常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0008-N-1 | Worker image 与 system artifact digest 有效 | 启动一次 formal run | Fresh VM 启动，被测系统拥有 guest root 与 VM-local Docker | 自动化 + 真实 VM probe |
| AC-0008-N-2 | InputBundle 已物化，output 为空 | 在 guest 与 nested container 中读写 I/O | Input 可读不可写；workspace/output 可写 | 自动化 + 真实 VM probe |
| AC-0008-N-3 | 被测系统生成 artifacts | 正常停止 guest 并收集 output | 生成标准 SubmissionBundle，VM 内外 artifact checksum 一致 | 自动化 |
| AC-0008-N-4 | Formal run 完成 | 检查 execution provenance | 记录 disposable-vm、worker/system digest、network policy、deadline 与 teardown 结果 | 自动化 |

## 边界场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0008-B-1 | Entry interaction mode 为 offline | Guest 尝试访问外部网络 | Egress 被拒绝，control channel 仍可完成状态与产物收集 | 自动化 + 真实 VM probe |
| AC-0008-B-2 | Entry 允许 discovery/tool-runtime | 使用短期凭据访问允许资源 | 使用 controlled-egress；provenance 只记录 secret 名称/类型，不记录值 | 自动化 + 安全审查 |
| AC-0008-B-3 | 两个 fake system 分别内部使用 Pixi 与 OCI | 通过 adapter 在相同 worker contract 下执行 | 两者使用同一 `disposable-vm` schema，不新增 runtime enum | 契约测试 |
| AC-0008-B-4 | Docker sandbox validation run 成功 | 尝试加入 release baseline | Release gate 拒绝，要求 disposable VM 重跑 | 自动化 |

## 异常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0008-E-1 | 节点无 KVM/VM provider | 启动 formal run | 返回 WORKER_UNAVAILABLE，不回退 host 或 Docker sandbox | 自动化 |
| AC-0008-E-2 | Worker image/system artifact digest 不匹配 | 启动 run | 返回 INVALID_EXECUTION_ENVIRONMENT，guest 不启动 | 自动化 |
| AC-0008-E-3 | Guest boot 或 output attach 失败 | 执行 run | 返回 infrastructure error，不计为系统科学能力失败 | 自动化 |
| AC-0008-E-4 | Teardown 审计发现残留 worker | 完成 run | 标记 TEARDOWN_ERROR，结果不得发布或进入 baseline | 自动化 + process audit |

## 失败场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0008-F-1 | Guest 内系统超过 deadline | 等待 runner timeout | 系统 run 记录 BLOCKED/timeout；VM、container、overlay 和 secret 全部清理 | 自动化 + 真实 VM probe |
| AC-0008-F-2 | Guest root/nested Docker 探测 host oracle、repository 与 Docker socket | 执行 escape probe | 所有 control-plane 目标不可见 | 自动化 + 真实 VM probe |
| AC-0008-F-3 | 系统非零退出但 output 有部分 artifacts | 收集 submission | 保留实际 artifacts 与失败状态；仍完成 teardown | 自动化 |
