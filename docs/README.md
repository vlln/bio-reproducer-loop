## 当前系统状态

| 字段 | 值 |
|------|-----|
| **当前阶段** | `SYSTEM_TEST`（完成，待发布决策）（v0.2.0 已发布；本轮迭代 BL-011 ClaroAI-Bench 接入：35 个 L5 审计 entry 落地、137 测试全绿、35-entry 评分冒烟全过；**BL-012 校准完成**：bench-200 完整运行 verdict=BLOCKED 与作者 D2=0/D3=1 一致，35 篇批量校准分析转录一致；RELEASE 门禁需人类批准） |
| **设计评估** | ADR-0009/0010 accepted；Spec v5、Interface 0001/0002 与 AC-0004/0009 active |
| **基建评估** | Plan 008 已实现 QEMU/KVM worker、ExecutionEnvelope、release gate 与 pinned worker recipe；`gs` success/timeout smoke 通过；Plan 013 修复 launcher 三处缺陷（skills 挂载、非 root 运行、HOME 权限） |
| **系统测试** | Plan 013 正式 smoke：`bench-001` 在 QEMU/KVM disposable VM 中全 7 阶段真实跑通，claimed_verdict REPRODUCED、93/100，release-check FORMAL，teardown 完整；合并态 125 个确定性测试与 4 个显式 Docker probe 通过；不建立 tracked baseline（按 Plan 013 约定） |

正式契约要求 Runner/Curator 在可信控制面校验并 stage InputBundle，被测系统在每次
新建的 QEMU/KVM disposable VM 中读取只读 `/input` 并写入 `/workspace`、`/output`。Guest 可以
使用 root 与 VM-local Docker，但仓库、oracle、其他 entry、历史结果和 host runtime
socket 不进入 VM。Worker 使用预构建最小 image 与 fresh qcow2 overlay，实测 cold boot
约 10-11 秒。Opaque system artifact 现在同时记录构建侧 config ID 和 archive 内部 tag；
launcher 使用经结构校验的 tag，fresh daemon load/run gate 已通过。完整 MinerU/R 等依赖不
进入 worker base。

## 子目录

| 路径 | 用途 |
|------|------|
| [vision.md](vision.md) | 全局顶层愿景 |
| [spec/](spec/) | Spec 需求规格（用户故事、模块划分、数据模型、非功能指标） |
| [interface/](interface/) | 接口定义（入参/出参/错误码） |
| [adr/](adr/) | 架构决策记录 |
| [plans/](plans/) | 任务执行计划 |
| [ac/](ac/) | 验收标准 |
