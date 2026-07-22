## 当前系统状态

| 字段 | 值 |
|------|-----|
| **当前阶段** | `DESIGN`（VM runtime architecture revision） |
| **设计评估** | ADR-0009、Spec v4、Interface 0001 与 AC-0004 proposed，等待内容审查 |
| **基建评估** | Plan 006 已验证 disposable VM 可行；现有 Docker sandbox 降为 validation backend，VM runner 尚未实现 |
| **系统测试** | 73 个确定性测试与 4 个显式真实 Docker probe 通过；12 个 component 与 2 个 handoff 真实 LLM smoke 有效通过；开发期不建立 tracked baseline |

正式设计草案要求 Runner/Curator 在可信控制面校验并 stage InputBundle，被测系统在每次
新建的 disposable VM 中读取只读 `/input` 并写入 `/workspace`、`/output`。Guest 可以
使用 root 与 VM-local Docker，但仓库、oracle、其他 entry、历史结果和 host runtime
socket 不进入 VM。设计冻结后才能创建 VM runner 的 TEST_INFRA Plan。

## 子目录

| 路径 | 用途 |
|------|------|
| [vision.md](vision.md) | 全局顶层愿景 |
| [spec/](spec/) | Spec 需求规格（用户故事、模块划分、数据模型、非功能指标） |
| [interface/](interface/) | 接口定义（入参/出参/错误码） |
| [adr/](adr/) | 架构决策记录 |
| [plans/](plans/) | 任务执行计划 |
| [ac/](ac/) | 验收标准 |
