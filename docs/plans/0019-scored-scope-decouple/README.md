# 0019-scored-scope-decouple

## 子任务状态表

| Plan | 状态 | Report |
|------|------|--------|
| [01-plan-scored-scope-decouple.md](01-plan-scored-scope-decouple.md) | done | [01-report-scored-scope-decouple.md](01-report-scored-scope-decouple.md) |

## 概述

修正 0016 的设计缺陷：benchmark 协议不携带 bio-reproducer 特有概念。`metadata.yaml`
的 `scope` 字段改名引擎无关的 `scored_scope`（ADR-0008 结构化声明），翻译留在 adapter
（唯一引擎耦合层）边界；benchmark 版本 2.0.0 → 2.1.0，loop 侧 `scope` arg 不变。
