---
title: Plan 004 — InputBundle 材料真实性
description: 冻结 L3/L4/L5 分层输入契约，审计现有 entry，并重建 manifest、资源 provenance 和层级校验。
type: plan
status: pending
created: 2026-07-20T00:00:00Z
---

# 目标

修复“统一目录结构演变为统一且简化的科学输入”这一设计缺陷。保留 ADR-0005 的
Input/Submission/Oracle 信任边界，但让 L3、L4、L5 对论文原件、补充材料、代码、数据
和在线资源承担不同且可验证的完整性要求。

# 执行路线

## 阶段 1：设计冻结

- 审查 ADR-0007 的分层 InputBundle 决策。
- 审查 Spec 001 v3、Interface 0001 修订和 AC-0003。
- 明确 public manifest 与 private oracle/robustness intent 的边界。
- 审查通过后将 Spec/Interface/AC promote 为 active，ADR promote 为 accepted。

## 阶段 2：Manifest 基建

- 定义可机器校验的 InputBundle manifest schema。
- 实现 path、hash、authority、derived_from、transform 和 availability 校验。
- 实现 L3/L4/L5 level validator 和 forbidden oracle-key 检查。
- Runner 在调用被测系统前执行 validator，并保持 oracle 隔离。
- 覆盖 AC-0006/0007 的确定性测试。

## 阶段 3：L3 Entry 修复

- 为 bench-001/002/004/005/006 建立 manifest。
- 对论文引用的 figures、supplementary、code 和 accession 逐项处置。
- 明确 constructed、synthetic、intentionally unavailable 和 derived resource。
- 删除未声明重复文件；故障恢复资源必须具有清晰公开语义和私有注入记录。

## 阶段 4：bench-003 L4 重建

- 获取真实原始论文 PDF/XML/HTML 和全部可获得 supplementary。
- 核查论文真实方法链、代码公开情况、GSE52778 和 airway 数据关系。
- 冻结原始数据或受审查 descriptor；为任何裁剪数据提供转换 provenance。
- 基于真实论文 scope 重建 claims/rubric，不沿用当前 DESeq2 摘要任务的假设。
- bench-003 通过 L4 fidelity gate 前不得建立 baseline 或对外宣称 L4 完成。

## 阶段 5：重新验证

- 全量运行确定性 tests 和 manifest lint。
- 人工审查六个 cited-resource inventory。
- 仅在 entry、oracle 和协议进入 RC 后重新执行 benchmark 并建立 baseline。

# 非目标

- 本设计单元不下载或修改论文材料。
- 不把 supplementary、代码缺失自动判为系统失败。
- 不在 public manifest 中加入 expected results、rubric 或故障注入原因。
- 不保留当前 bench-003 的内部开发 baseline。

# 完成条件

- ADR-0007 accepted，Spec/Interface/AC active。
- AC-0006/0007 具有确定性自动化门禁。
- 六个 entry 均有通过校验且经人工审查的 manifest。
- bench-003 的真实论文材料和复现 scope 通过 L4 审查。
- Plan Report 记录每项 AC 的 PASS/FAIL 和残余风险。
