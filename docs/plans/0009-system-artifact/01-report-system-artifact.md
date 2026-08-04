---
title: Report 009 — Opaque Bio-Reproducer System Artifact
description: 记录 system artifact 构建、manifest、launcher、adapter、bench-001 formal VM smoke 和 teardown 证据。
type: report
status: complete
created: 2026-07-23T00:00:00Z
---

# 结论

Plan 009 已完成。Runner 现在可以从显式、固定的输入构建 opaque bio-reproducer system
artifact，校验其 manifest 和稳定 tree digest，并通过 `/system/run-system` 在 disposable VM
内启动。制品不复制用户 home、`.pixi/`、`.skills/`、entry、oracle、历史 results 或 secret
value；公开 submission 只记录 system digest 与 adapter identity。

按 Plan 约束只正式运行了一次 `bench-001`。该 run 在 loopflow 启动前因原 worker 缺少
Docker 返回 `BLOCKED`，实际 submission 和完整 teardown 证据均被保留。随后定位并修复
worker provisioning 与 release gate 缺陷，使用独立 VM probe 验证修复后的 worker，但没有
违反 exact-one 约束重跑 benchmark，也没有建立 baseline。

# 实现结果

| 组件 | 结果 |
|------|------|
| Artifact builder | 显式接收 loop source、OCI archive、skills lock 和 provenance；拒绝 symlink、generated state、越界路径和非法 secret 声明 |
| Manifest | 固定 loopflow commit/version、repository commit、Pixi lock、runtime image/archive 和每个 skill 的 repository/commit/content digest |
| Launcher | 稳定入口 `/system/run-system`，只使用 `/system`、只读 `/input`、`/workspace`、`/output` 与 guest-local Docker socket |
| Adapter/CLI | Formal adapter 固定调用 artifact launcher；新增 build/validate system artifact 命令和 digest 校验 |
| Runtime | 固定 Pixi 0.72.2、Python base digest、Claude Code 2.1.126、MIP 0.2.0 与 MIP archive SHA256 |
| Worker | Ready marker 仅在 `docker`、active daemon 和 `docker.io` package 全部存在后写入；失败 provisioning 不再关机伪装成功 |
| Release gate | JSON round-trip 后 teardown status 使用值比较，仍拒绝 infrastructure-blocked 或 teardown 不完整的 submission |
| Test isolation | 动态加载 workflow 不写 bytecode；artifact tests 从排除本地 generated state 的 source fixture 构建，仍单独验证 builder 严格拒绝这些目录 |

实现 commits：`83ce804`、`5465c23`、`15e5b15`、`345da6a`、`8adbac1`、`838d193`、
`4c212d1`。

# Artifact 证据

`gs@172.16.209.237` 使用镜像 transport override 下载固定 SHA 的 MIP；GitHub 直连曾以
HTTP/2 protocol error 失败，mirror 在约 4.8 秒完成。override 只改变下载地址，不改变版本
或内容校验。

```text
artifact repository commit:
345da6a615a81d835e669e1350e73001727a1ade

loopflow commit / version:
e6334ab05d908bf83792f42be32fb9849375347e / 0.17.2

runtime image:
sha256:b5ac039a6fb22a82ceea2a299904dc718d48c396adee1dbe20bf0df3b0d5aaed

runtime OCI archive SHA256:
3ffaee0b2ff801a1f8fc57f2089a2858d82f631a81b496c298bdd0542ab3ec62

system artifact tree:
sha256:c856a668914504e3d669594d453e6b2ba3a839360f91c99a861327c4d3be9c38

manifest file count: 54
```

Runtime self-check 确认 Claude Code 2.1.126、MIP 0.2.0、Java 与 Nextflow 26.04.6 可用。

# 唯一 Formal Smoke

唯一正式输出为 `bench-001/run_01/submission.json`：

```text
claimed_verdict: BLOCKED
error_code: EXECUTION_BLOCKED
blocked_reason: system
error: loopflow exited with code 127
stderr: /system/run-system: 10: docker: not found
purpose / isolation / provider: formal / disposable-vm / qemu-kvm
network_policy: controlled-egress
boot_seconds: 30.26
system artifact: sha256:c856a668914504e3d669594d453e6b2ba3a839360f91c99a861327c4d3be9c38
original worker: sha256:0b5ff873ec537e7f08c7e0a466b4fbbe92dbfdaaf90e207b3cce842a5421e4e3
teardown.status: completed
worker_absent / overlay_absent / secrets_revoked: true / true / true
```

Runner 根据 launcher 的非零退出将它记录为 system blocked；事后诊断证明直接原因其实是
原 worker 的 cloud-init package 安装因 DNS 失败，但配方仍无条件写 ready marker。因而该
submission 证明 formal I/O、VM、artifact injection、失败保留和 teardown 路径成立，不证明
bio-reproducer 已开始执行，也不可作为科学能力 baseline。

# Worker 修复证据

嵌套在 control container 内的 QEMU slirp 无法使用默认 resolver。探针确认 `223.5.5.5`
可达，而 `8.8.8.8`、`1.1.1.1` 和 slirp DNS 不可用；worker recipe 因此显式设置可达
resolver，并将 Docker 安装、daemon 和 package 校验作为 ready 前置条件。

```text
fixed worker SHA256:
b92a7f2bf2429be5692608d9edb2296034dfa05cb8038b1ff87a168fa00666d6

docker: /usr/bin/docker
dockerd: /usr/bin/dockerd
docker.io: 29.1.3
worker_ready: yes
validation VM boot_seconds: 10.853
qemu-img check: No errors were found on the image
teardown: completed
```

该验证只检查 worker readiness，不是第二次 benchmark run。

# 本地门禁

最终证据：

```text
PYTHONPATH=. pytest -q tests/: 102 passed, 4 skipped
RUN_DOCKER_ISOLATION_TESTS=1 PYTHONPATH=. pytest -q: 106 passed
make lint: PASS
bundle validator: bench-001/002/004/005/006/100 VALID
git diff --check: PASS
```

四个普通 skip 是显式 Docker isolation probes，同一组已通过 opt-in 执行。测试覆盖 artifact
determinism/provenance/tamper rejection、launcher boundary、adapter routing、worker
provisioning、release rejection、VM teardown 和 JSON round-trip regression。

# 远端清理

收集证据后删除 Plan 009 临时树、control/runtime image、容器、qcow2、formal output 与
background-task 状态。最终审计：

```text
/tmp/bio-reproducer-plan009-83ce804: absent
matching containers: 0
bio-reproducer-vm-control:plan009: absent
bio-reproducer-runtime:plan009: absent
qemu processes: 0
remote project status hash:
b42dec57ee3a21c0d45a0488369da3f225960142fe3856b6461c6483b3b403a3
```

该 hash 与 Plan 008 报告中的既有值完全一致；远端 `~/bio-reproducer` 未被修改。

# 验收状态

| 条目 | 状态 | 证据 |
|------|------|------|
| SA-001 | PASS | 相同输入的 manifest 与 tree digest 确定一致 |
| SA-002 | PASS | Symlink、generated state、非法 secret 与 tampering 均被测试拒绝 |
| SA-003 | PASS | Launcher contract 固定四个 guest 路径和 VM-local Docker |
| SA-004 | PASS | Manifest 固定 loopflow、loop/Pixi、runtime 与七个 skills provenance |
| SA-005 | PASS | Formal adapter 使用 `/system/run-system`；Docker 保持 validation-only |
| SA-006 | PASS with blocked outcome | 唯一 bench-001 run 生成真实 formal ExecutionEnvelope 与 BLOCKED submission |
| SA-007 | PASS | 非零退出保留实际 stderr/submission，teardown 全部完成 |
| SA-008 | PASS | 本地门禁、bundle 校验、qcow2 校验与远端 residue audit 通过 |

# 后续边界

下一个执行容器应使用 fixed worker 与已合入的 artifact contract 再做一个最小 formal smoke，
验证 loopflow 真正启动后的 system capability。它必须生成新的 submission，不得改写本 Plan
唯一 blocked 观测；仍不需要运行全部 entry 或建立 baseline。
