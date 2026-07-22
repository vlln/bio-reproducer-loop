## 当前系统状态

| 字段 | 值 |
|------|-----|
| **当前阶段** | `TEST_INFRA`（Plan 003/004/005 已完成） |
| **设计评估** | ADR-0007/0008 accepted；Spec v3、Interface 0001 与 AC-0003 active |
| **基建评估** | 独立 evaluator、测试分域、bundle/fidelity review 与 Docker runtime isolation 已通过；实际 L4 image 留在 Plan 002 |
| **系统测试** | 73 个确定性测试与 4 个显式真实 Docker probe 通过；12 个 component 与 2 个 handoff 真实 LLM smoke 有效通过；开发期不建立 tracked baseline |

Runner/Curator 在可信宿主侧校验并 stage InputBundle；被测系统只能在 Docker sandbox
中读取 `/input` 并写入 `/workspace`、`/output`。仓库、oracle、其他 entry、历史结果与
Docker socket 均不挂载。当前剩余 benchmark 基建工作是 Plan 002 的实际系统/L4 镜像。

## 子目录

| 路径 | 用途 |
|------|------|
| [vision.md](vision.md) | 全局顶层愿景 |
| [spec/](spec/) | Spec 需求规格（用户故事、模块划分、数据模型、非功能指标） |
| [interface/](interface/) | 接口定义（入参/出参/错误码） |
| [adr/](adr/) | 架构决策记录 |
| [plans/](plans/) | 任务执行计划 |
| [ac/](ac/) | 验收标准 |
