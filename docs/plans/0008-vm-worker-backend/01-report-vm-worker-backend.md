---
title: Report 008 — QEMU/KVM Worker Test Infrastructure
description: 记录 VM executor contract、fake tests、worker image、gs smoke、性能、隔离和 teardown 证据。
type: report
status: complete
created: 2026-07-22T00:00:00Z
---

# 结论

Plan 008 已完成。正式 backend 固定为 QEMU/KVM disposable VM，Docker 只能由
`--backend docker-validation` 显式选择并生成 `purpose=validation-only`。Runner 在启动前
校验 worker/system digest，每次创建 fresh qcow2 overlay，只 attach input、workspace、output
和 system 四个目录，并在 success、非零退出与 timeout 后执行 guest shutdown、QMP fallback
和残留审计。

该 Plan 证明的是 worker 基础设施可用，不代表完整 bio-reproducer system artifact 已构建，
也没有运行六个 benchmark entry 或建立 baseline。

# 实现结果

| 组件 | 结果 |
|------|------|
| Executor contract | `ExecutionRequest` 统一 Docker 与 VM 的 command/I/O contract；旧 `SandboxRequest` 保留为兼容别名 |
| Formal backend | `QemuWorker` 实现 KVM preflight、digest gate、fresh overlay、9p/virtio attach、SSH readiness、deadline、QMP/ACPI shutdown 与 teardown audit |
| Provenance | Adapter 在 submission 根记录 protocol `2.0`，在 execution 根写 ExecutionEnvelope，不再嵌套旧 sandbox provenance |
| Partial output | 系统非零退出或 timeout 时保留 output 中实际存在的 artifacts，不再强制提交空列表 |
| Validation backend | Docker envelope 固定为 `validation-only/container/docker`，无 host fallback |
| Release gate | `bench-run release-check --submission ...` 拒绝 Docker、TCG、digest 缺失、infrastructure blocked 或 teardown 不完整的结果 |
| Worker supply | 固定 Ubuntu cloud image SHA，预构建 VM-local Docker，支持断点 cache、低速超时、mirror transport 与 build serial failure log |
| Packaging/CI | 修正 setuptools backend 与 package discovery；editable install 只包含 `benchmarks.runner*` 和 `evals.runner*` |

# 确定性门禁

本地最终证据：

```text
Python 3.12 venv: pip install -e '.[test]' PASS
pytest tests/: 87 passed, 4 skipped
RUN_DOCKER_ISOLATION_TESTS=1: 4 passed
make lint: PASS
bundle validator: bench-001/002/004/005/006/100 VALID
git diff --check: PASS
```

普通测试中的四个 skip 是显式真实 Docker probe；同一组已通过 opt-in 运行。Fake tests 覆盖
KVM/QEMU 缺失、digest mismatch、mount command、success、timeout、QMP fallback、teardown
失败、Docker validation envelope、formal adapter 与 release rejection。

# `gs` 真实证据

## 构建边界

`gs@172.16.209.237` 的普通用户不能直接打开 `/dev/kvm`，因此 QEMU runner 位于 trusted
control container，并只获得 `/dev/kvm` 与 Plan 008 临时目录。被测 system 仍位于 guest，
没有 host Docker socket。构建输入和产物：

```text
Ubuntu jammy dated base SHA256:
757908b2fd6d5b1431bb45070fc1f56cbf017d4025568d292ece37d9cc75e812

worker.qcow2 SHA256:
5454bac4ed88c62b5016e709aecc3c6e4eec49e5a6832b73a696fbd32d908397

smoke system tree SHA256:
5c7279c1d2cfd8fb6f0f9215f2b4eb4c2fd7772a3c68599e197a21bb084a0f5b
```

Worker image 为约 2.4 GiB 的 qcow2；`qemu-img check` 报告无错误。构建期官方 cloud endpoint
曾在 299,384,832 bytes 后形成死连接，配方因此加入 Range resume、low-speed timeout 与
retry-all-errors。第二次构建暴露完整 cache 的 HTTP 416，随后改为 digest 命中时跳过网络。
Guest apt 首次因 control DNS 不可达失败；fresh overlay 使用 spike 已验证的 resolver 后成功。

## Success smoke

Fake system 在 guest 的 VM-local Docker 中读取 `/input/public.txt`，尝试写 input 被拒绝；
nested container 将整个 guest `/` 只读挂载后仍看不到 control-plane canary，并向 output
写入 artifact。Runner 在 VM 外读到：

```text
vm_worker_smoke:PASS
boot_seconds: 11.036
artifact: nested-docker-artifact-plan008
artifact_sha256: f7c6d3e7c48ed354892d54037cc3de7b9995f95793c65d5e932fedaa8696e36c
input_write_marker: absent
```

ExecutionEnvelope 为 `formal/disposable-vm/qemu-kvm/offline`，worker/system digest 与上文
一致；teardown 的 `worker_absent`、`overlay_absent`、`secrets_revoked` 全为 true。

## Timeout smoke

第二个 fresh VM 使用相同 worker/system digest，执行 30 秒 fake command，Runner deadline
设为 3 秒：

```text
vm_worker_timeout:PASS
boot_seconds: 9.824
deadline_seconds: 3
teardown.status: completed
worker_absent: true
overlay_absent: true
secrets_revoked: true
```

## 最终清理

证据收集后删除 worker/control image、control container、临时 key、OCI tar、run directories
和 background-task 状态。最终审计：

```text
Plan 008 temp paths: absent
matching containers: 0
control image count: 0
qemu processes: 0
remote project status hash:
b42dec57ee3a21c0d45a0488369da3f225960142fe3856b6461c6483b3b403a3
```

该 status hash 与 Plan 008 前完全一致；远端 `~/bio-reproducer` 未被修改。

# 验收状态

| 条目 | 状态 | 证据 |
|------|------|------|
| WI-001 | PASS | QEMU/KVM 与 `/dev/kvm` mandatory preflight；无 TCG/Docker fallback |
| WI-002 | PASS | Worker file 与 symlink-free system tree 在 guest 启动前校验 SHA256 |
| WI-003 | PASS | Guest/nested Docker 实测 input 只读、workspace/output 可写、canary 不可见 |
| WI-004 | PASS | VM-local Docker load/run 成功，运行期不依赖 registry |
| WI-005 | PASS | Fake success/nonzero/timeout/teardown tests 与真实 success/timeout smoke 全部完成 teardown |
| WI-006 | PASS | Docker 标为 validation-only；function 与 CLI release gate 均拒绝 |
| WI-007 | PASS | 两次 fresh overlay cold boot 分别为 11.036 秒与 9.824 秒，低于 60 秒 |
| WI-008 | PASS | Editable install、87 tests、4 Docker probes、lint、bundle 与远端 smoke 通过 |
