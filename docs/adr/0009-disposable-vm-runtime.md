---
title: ADR-0009 — Disposable VM 正式运行边界
description: 将 disposable VM 定义为公开 benchmark 可发布结果的唯一运行边界，同时保留容器 sandbox 作为开发验证 backend。
type: adr
status: accepted
created: 2026-07-22T00:00:00Z
---

# ADR-0009: Disposable VM 正式运行边界

## 背景

Plan 005 用宿主 Docker daemon 启动受限 container，能够隔离 InputBundle、private oracle、
仓库和历史结果。但该方案要求被测系统预先封装成单一 sandbox image，并禁止 Docker
socket。真实论文复现系统经常需要 root、动态安装系统依赖、启动多个 OCI container，或
使用 Pixi、Conda、R、Nextflow 等不同工具链。把这些实现方式提升为 benchmark 的公共
`pixi | oci | hybrid` runtime 分支，会让 benchmark 同时承担系统打包和科学复现两类职责。

把宿主 Docker socket 交给被测 container 可以恢复灵活性，但 socket 等价于宿主 daemon
控制权，破坏 Runner、oracle 和其他 entry 的信任边界。仅靠 rootless/container hardening
也仍共享宿主 kernel，不能把任意被测系统当作黑盒运行。

Plan 006 在 `spike/0006-vm-isolation` commit `e1c1290` 上完成了 KVM/QEMU 实测：真实
Ubuntu guest、VM-local Docker、只读 input、可写 output、host-only oracle 隔离、产物
回收和完整 teardown 全部通过，且未修改远端 benchmark 工作树。

## 决策内容

### 1. 正式结果统一来自 disposable VM

所有可进入 release report、跨系统比较或 baseline 的 benchmark run，必须在每次运行新建
的 disposable VM 中产生。`isolation` 的公共协议值固定为 `disposable-vm`，不提供
`pixi`、`oci`、`hybrid` 或 host execution 等并列正式路径。

现有 Docker sandbox 保留，用于单元/集成测试、CI escape probe 和开发期快速验证；它产生
的结果必须标记为 `validation-only`，不得进入正式 baseline。

### 2. 控制面与被测系统分离

可信控制面在 VM 外运行 Runner、Curator、bundle validator、private oracle、evaluator、
worker image resolver 和 artifact collector。被测系统只在 guest 内运行。以下内容不得
进入 guest：

- benchmark repository、`.git`、其他 entry 和历史结果；
- `bundle.yaml`、`metadata.yaml`、private oracle 与 evaluator；
- host Docker socket、hypervisor control socket 和 control-plane credentials；
- 共享对象库的原始 mount。

Guest 只获得物化后的只读 InputBundle、独立可写 workspace/output、被测系统本身，以及
entry 允许的网络/临时凭据。Runner 只能从 output 收集 SubmissionBundle。

### 3. VM 内实现自由

被测系统在 guest 内可以拥有 root、VM-local Docker daemon 和任意用户空间环境管理器。
Pixi、Conda、OCI image、源码安装或多容器 workflow 都是系统实现细节，不属于 benchmark
entry schema 或公共 runtime 类型。

Runner 使用 runner-owned、按 digest 固定的 worker image 提供最小 VM 基础设施。Adapter
负责把被测系统作为 opaque system artifact 注入 guest 并给出启动命令；公共协议只记录
adapter identity、system artifact digest 和实际 worker image digest，不规定 system
artifact 的内部打包格式。

### 4. 环境与网络策略正交

L3/L4/L5 和 entry taxonomy 描述材料真实性、资源冻结及任务范围，不选择不同的隔离
backend。所有 level 使用同一个 VM boundary。

Entry 的 interaction mode 只映射为 VM 网络策略：

| interaction mode | VM network policy | 说明 |
|------------------|-------------------|------|
| `offline` | `offline` | 除 control channel 外无 egress |
| `discovery` | `controlled-egress` | 允许在线发现论文、数据和代码资源 |
| `tool-runtime` | `controlled-egress` | 允许模型/API 与工具资源访问 |

网络策略不是 runtime backend。允许 egress 时，临时凭据必须最小权限、短期有效、逐 run
注入并在 teardown 后失效；协议记录凭据名称和来源类型，不记录 secret value。VM boundary
不防止已获得凭据的不可信系统通过允许的网络或 output 主动泄露它，因此凭据必须按已暴露
处理，并使用独立额度与撤销策略。

### 5. 生命周期与证据

Formal runner 必须执行以下生命周期：

1. 校验 entry、worker image digest 与 system artifact identity；
2. 从 immutable base 创建 fresh worker，不恢复失败 run 的可写 overlay；
3. 以只读语义 attach InputBundle，以独立可写语义 attach workspace/output；
4. 启动被测系统并执行 runner-owned deadline；
5. 停止 guest 后仅从 output 收集 submission；
6. 删除 VM process、VM-local container、overlay、临时凭据和 attach point；
7. 记录 worker、system、网络策略、timeout、teardown 和 artifact checksum provenance。

Worker boot、基础设施网络、artifact attach 或 teardown 失败属于 infrastructure error，不得
伪装成系统科学能力失败。Timeout 可以形成系统 `BLOCKED` 观测，但只有 teardown 成功的
run 才可发布。

### 6. 镜像供应

正式 runner 不在每个 run 的 cloud-init 中安装 Docker，也不隐式依赖 Docker Hub、Quay
或系统包仓库实时可用。Worker image 和 runner-required OCI images 应由可信控制面预构建、
校验、缓存或注入。L5 对外部网络真实性的测试仅针对 entry 所声明的资源发现，不等于把
runner 自身启动依赖交给公共网络。

### 7. 当前正式 backend

当前正式 backend 固定为 QEMU/KVM：

- QEMU 使用 KVM hardware acceleration，不允许 formal run 静默回退到 TCG；
- immutable Ubuntu worker base + 每 run 新建 qcow2 writable overlay；
- `virtio-blk` / `virtio-net` 提供磁盘与网络，`virtiofs` 提供 input/output attach；
- QMP 管理生命周期，首版使用 SSH 或 guest agent 执行 guest control；
- worker image 预装 VM-local Docker，不在 run 时通过 cloud-init 在线安装；
- cold boot 到可执行状态的门禁目标为 60 秒以内。

Plan 006 使用未预装 Docker 的 cloud image 实测 SSH ready 约 28 秒；约 21 分钟的完整
cloud-init 来自在线 apt/Docker 安装，不是 VM 固有启动成本。正式 worker 必须预构建这些
基础设施依赖。

本轮不使用 snapshot restore、Firecracker、libvirt 或其他 VM provider。以后引入其他
provider 必须单独 ADR，并证明 isolation、I/O、network、teardown 与结果可比性；不能作为
QEMU/KVM 失败时的静默 fallback。

## 方案比较

| 方案 | 结论 | 原因 |
|------|------|------|
| 单一受限 Docker sandbox | 仅保留验证用途 | 不能安全提供 VM-local root/Docker，且强迫系统预封装 |
| 向 container 暴露 host Docker socket | 拒绝 | 等价于泄露宿主 daemon 控制权 |
| 公共 `pixi | oci | hybrid` 多路径 | 拒绝 | 将被测系统实现细节变成 benchmark 政策，产生不可比执行路径 |
| Participant 自带完整 VM image | 暂不采用 | 扩大 boot/guest-agent 兼容面；当前用 runner-owned base + opaque system artifact 足够 |
| QEMU/KVM runner-owned disposable VM | 采用 | 已实测，保持单一正式边界，同时允许 guest 内任意工具链 |
| Firecracker/microVM | 暂不采用 | 需额外维护 kernel/rootfs/jailer，当前启动收益不足以抵消实现成本 |

## 后果

### 正面

- 被测系统保持黑盒，不需按 benchmark 选择特定包管理器或容器化方式。
- VM-local Docker 的控制权止于 guest，不暴露 host daemon。
- L3/L4/L5 的结果共享同一隔离语义，环境差异来自 entry，而不是 runner 分叉。
- Control plane、oracle 和 evaluator 继续独立于被测系统。

### 负面

- Runner 需要管理 VM image、hardware virtualization、guest control channel 和 teardown。
- 启动、磁盘和缓存成本高于单 container；需要预构建 image 与后续性能优化。
- VM boundary 仍依赖 hypervisor 和 host kernel，不宣称抵御其漏洞。
- 允许 egress 且显式注入凭据时，VM 不能防止被测系统主动外传该凭据。
- 不支持硬件虚拟化的执行节点不能生成正式结果，只能运行 validation backend。

## 对现有设计的影响

- Plan 005 的 Docker sandbox 实现不删除，但其“正式执行边界”结论由本 ADR 取代。
- ADR-0008 的 taxonomy、entry identity 和资源复用决策继续有效；其中 `sandbox` 字样按本
  ADR 解释为 disposable VM execution environment。
- Spec 0001 升级至 v4；Interface 0001 和 runtime AC 已完成审查并重新冻结。
- 当前开发期历史 run 不自动成为新 runtime 下的 baseline，必须在 VM 中重新执行。

## 约束规则

| 规则编号 | 规则 | 检出方式 |
|----------|------|----------|
| VM-AR-001 | 正式 run 的 isolation 必须为 `disposable-vm` | submission/release validator |
| VM-AR-002 | Guest 不得获得 control-plane 路径或 socket | VM escape probe |
| VM-AR-003 | Input 只读，workspace/output 独立可写 | guest mount probe |
| VM-AR-004 | Guest root 与 VM-local Docker 不得扩大到 host | nested container oracle probe |
| VM-AR-005 | Worker/system artifact 必须按 digest 记录 | execution provenance validator |
| VM-AR-006 | Timeout、失败与成功 run 均必须完成 teardown | process/container/overlay audit |
| VM-AR-007 | Validation backend 结果不得进入 baseline | release gate |
| VM-AR-008 | Pixi/OCI 等实现方式不得成为 entry runtime 枚举 | schema review |
| VM-AR-009 | QEMU/KVM cold boot 到可执行状态不超过 60 秒 | real worker boot probe |

## 验证

| 验证项 | 复现步骤 | 预期结论 |
|--------|----------|----------|
| VM-local Docker | Guest root 启动 Docker container | container 成功，host socket 未挂载 |
| Oracle 隔离 | Nested container 挂载 guest `/` 并探测 host canary | 路径和 marker 均不可见 |
| I/O boundary | Guest 读写 input/output | input 写入失败，output 可收集且 checksum 一致 |
| Timeout teardown | 强制超时正在运行的系统 | VM、container、overlay 和 secret 均无残留 |
| Backend gate | 提交 Docker validation-only result 作为 baseline | release gate 拒绝 |
| Packaging neutrality | 用两种内部打包方式运行相同 fake system | 公共 execution schema 不产生 runtime 分支 |
