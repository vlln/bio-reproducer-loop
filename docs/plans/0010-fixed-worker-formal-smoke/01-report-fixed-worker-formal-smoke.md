---
title: Report 010 — Fixed Worker Formal Smoke
description: 记录 fixed worker、opaque artifact、bench-001 formal smoke、release-check、teardown 与清理证据。
type: report
status: complete
created: 2026-07-27T00:00:00Z
---

# 结论

Plan 010 执行完成，但验收未通过。Fixed worker 的 Docker readiness、qcow2 完整性、冷启动与
teardown 均成立；唯一一次 `bench-001` formal run 生成了真实 protocol-v2 submission，但
system artifact 在启动 loopflow 前因跨 Docker image store 的 image identity 不稳定而返回
`BLOCKED`。该观测不建立 baseline，也不得在本 Plan 内重跑。

background task 自身返回成功只表示 Runner 成功保存了 submission，不表示被测系统成功。
`release-check` 返回 `FORMAL` 只证明 execution envelope 满足 formal provenance contract；
submission 的业务结果仍是 `BLOCKED/system`。

# 远端门禁与制品

所有执行位于 `gs@172.16.209.237` 的 Plan 专属临时树，未修改远端
`~/bio-reproducer`。受控 source commit 为
`debfca44a236ac3b252abe46279be83e4b64c0f5`。

```text
ordinary tests: 102 passed, 4 skipped
Docker opt-in tests: 106 passed
make lint: PASS
bundle validation: bench-001/002/004/005/006/100 VALID

worker qcow2 SHA256:
5624301cf03b4d31ec81d5ada2fdaa514b5e00404b95f6342f223205bcb907f4

runtime archive SHA256:
3ffaee0b2ff801a1f8fc57f2089a2858d82f631a81b496c298bdd0542ab3ec62

build-host runtime image ID:
sha256:b5ac039a6fb22a82ceea2a299904dc718d48c396adee1dbe20bf0df3b0d5aaed

system artifact tree digest:
sha256:c7df09836f53203413f0084e332021e7f9b65e6d8a3e215881ed45381e4a4c67
```

Runtime 自检确认 `loop`、Claude Code 2.1.126、MIP 0.2.0、Java 和 Nextflow 26.04.6
可用。`qemu-img check` 未发现错误。

# Fixed Worker Readiness

正式运行前的独立 VM probe 检查 Docker CLI、active daemon、`docker.io` package、ready
marker 与 `docker info`。该 probe 不调用 benchmark 或 LLM：

```text
docker: /usr/bin/docker
worker_ready: yes
boot_seconds: 10.986
teardown.status: completed
worker_absent / overlay_absent / secrets_revoked: true / true / true
```

两次更早的 probe 调用分别在 VM 启动前被 mount-root `EBUSY` 和错误 tree digest 拦截；另一次
在 VM 启动前被 required-secret name-set 门禁拦截。它们不构成 benchmark run。

# 唯一 Formal Run

唯一 submission 为 `bench-001/run_01/submission.json`：

```text
submission_id: bench-001-20260727T115951Z
claimed_verdict: BLOCKED
error_code / blocked_reason: EXECUTION_BLOCKED / system
error: loopflow exited with code 125
purpose / isolation / provider: formal / disposable-vm / qemu-kvm
network_policy: controlled-egress
duration_seconds / boot_seconds: 88 / 10.943
artifacts: 0
worker: sha256:5624301cf03b4d31ec81d5ada2fdaa514b5e00404b95f6342f223205bcb907f4
system: sha256:c7df09836f53203413f0084e332021e7f9b65e6d8a3e215881ed45381e4a4c67
teardown.status: completed
worker_absent / overlay_absent / secrets_revoked: true / true / true
```

stderr 的决定性错误是：

```text
docker: Error response from daemon: No such image:
sha256:b5ac039a6fb22a82ceea2a299904dc718d48c396adee1dbe20bf0df3b0d5aaed
```

`release-check` 输出 `FORMAL`。这符合当前 gate 的职责：它拒绝不合法 provenance、
infrastructure-blocked 和 teardown 不完整的 submission，但允许形式合法的 system-blocked
观测被报告；它没有把 verdict 改成成功。

# 根因诊断

Runtime build 使用 image ID 执行 `docker save`，archive 的 Docker manifest 因而包含
`RepoTags: null`。构建机 inspect 使用 config ID `b5ac...`，但相同 archive 在 fresh worker 的
Docker 29/containerd image store 中加载为：

```text
Loaded image ID: sha256:aac9ca2fd3f6a8ea4bff9a161a668bb999ca90a7e3d641bfb46fd465db8eafdc
REPOSITORY / TAG: <none> / <none>
inspect sha256:b5ac...: No such image
diagnostic teardown: completed
```

因此 build-host image ID 不是可跨 image store 使用的 guest locator。Archive SHA256 仍然
正确固定内容，缺陷位于 launcher identity contract。后续修复应让 archive 携带固定、内部专用
tag，并由 launcher 使用该 tag；manifest 继续记录 archive digest 和构建侧 image identity
作为 provenance。修复需增加真实 load/run probe，不能只在同一 host daemon 上 inspect。

# 验收状态

| 条目 | 状态 | 证据 |
|------|------|------|
| FS-001 | PASS | Fixed worker readiness、qcow2 digest/check 与 teardown 通过 |
| FS-002 | PASS | Runtime/archive/artifact 从固定输入重建并通过 digest/self-check |
| FS-003 | FAIL | formal boundary 成立，但 runtime image 启动失败，loopflow 未实际启动 |
| FS-004 | FAIL | submission 正确保留 BLOCKED 结果，但未到达 system/scientific execution |
| FS-005 | PASS | release-check 接受 formal provenance；verdict 仍为 BLOCKED/system |
| FS-006 | PASS | formal 与 diagnostic VM teardown 均完整；最终 residue 见下节 |
| FS-007 | PASS | 仅运行 bench-001 一次；无其他 entry、baseline 或 Plan 009 覆盖 |
| FS-008 | PASS | 远端 tests、Docker probes、lint、validators 通过；Plan worktree diff check 通过 |

# 远端清理

Plan 010 专属 `/tmp` 树、control/runtime images、临时容器与 QEMU 进程均已删除。部分
container/guest 输出为 root-owned，最终使用已缓存的 `ubuntu:22.04` 只挂载 Plan 根目录完成
删除，没有挂载或修改远端 home 项目。

```text
/tmp/bio-reproducer-plan010-6b14699: absent
matching containers: 0
bio-reproducer-vm-control:plan010: absent
bio-reproducer-runtime:plan010: absent
qemu processes: 0
remote home status hash before/after cleanup:
c3797cbac763f0ed8b1387951572efe771964ec2fc6832c00afb28ddce98b4ae
```

本轮使用 `git status --short --untracked-files=all | sha256sum` 计算 home hash；清理前后结果
一致。远端受控 source 是不含 `.git` 的 commit archive，因此最终文档 whitespace 检查在
Plan worktree 执行，而确定性代码门禁全部在远端 archive 上执行。

# 后续边界

Plan 010 按 devloop 规则标记 `done`，但不满足进入下一阶段的门禁。新的最小 TEST_INFRA Plan
负责修复 archive 内部 image reference、增加 fresh-daemon load/run 证据，再正式 smoke 一次
`bench-001`。不得修改或覆盖本 Plan 与 Plan 009 的 BLOCKED 历史观测。
