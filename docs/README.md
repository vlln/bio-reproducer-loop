## 当前系统状态

| 字段 | 值 |
|------|-----|
| **当前阶段** | `TEST_INFRA`（VM worker backend pending） |
| **设计评估** | ADR-0009 accepted；Spec v4、Interface 0001 与 AC-0004 active |
| **基建评估** | Plan 006 已验证 QEMU/KVM disposable VM；Docker sandbox 已降为 validation backend，正式 VM runner 尚未实现 |
| **系统测试** | 73 个确定性测试与 4 个显式真实 Docker probe 通过；12 个 component 与 2 个 handoff 真实 LLM smoke 有效通过；开发期不建立 tracked baseline |

正式契约要求 Runner/Curator 在可信控制面校验并 stage InputBundle，被测系统在每次
新建的 QEMU/KVM disposable VM 中读取只读 `/input` 并写入 `/workspace`、`/output`。Guest 可以
使用 root 与 VM-local Docker，但仓库、oracle、其他 entry、历史结果和 host runtime
socket 不进入 VM。Worker 使用预构建最小 image 与 fresh qcow2 overlay，cold boot 目标
小于 60 秒；下一步创建 VM runner 的 TEST_INFRA Plan。

## 子目录

| 路径 | 用途 |
|------|------|
| [vision.md](vision.md) | 全局顶层愿景 |
| [spec/](spec/) | Spec 需求规格（用户故事、模块划分、数据模型、非功能指标） |
| [interface/](interface/) | 接口定义（入参/出参/错误码） |
| [adr/](adr/) | 架构决策记录 |
| [plans/](plans/) | 任务执行计划 |
| [ac/](ac/) | 验收标准 |
