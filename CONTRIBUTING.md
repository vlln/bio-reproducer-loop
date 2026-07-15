## 一、开发环境

- [pixi](https://pixi.sh) — 环境和依赖管理
- [loopflow](https://github.com/vlln/loopflow) — workflow 运行时

**构建/配置入口：**

| 文件 | 用途 |
|------|------|
| `loops/bio-reproducer/pixi.toml` | 环境依赖声明 |
| `loops/bio-reproducer/workflow.py` | 工作流入口 |
| `pyproject.toml` | 本项目 Python 包配置 |

---

## 二、代码风格

- 格式化：遵循 PEP 8
- 命名：
  - 文件：snake_case
  - 变量/函数：snake_case
  - 类/接口：PascalCase
  - 常量：UPPER_SNAKE_CASE

---

## 三、Commit 规则

### 格式

```
<type>(<scope>): <简短描述>
```

| type | 说明 |
|------|------|
| feat | 新功能 |
| fix | Bug 修复 |
| docs | 文档变更（必须独立提交，不与代码混合） |
| refactor | 重构 |
| test | 测试相关 |
| chore | 构建/工具/依赖 |

### devloop 约定

- 文档变更和代码变更永远分开 commit
- 阶段推进伴随独立 commit，前缀 `docs(state):`
- 文档 commit 格式：`docs(<scope>): <简述>`

---

## 四、分支策略

遵循 Gitflow：

```
main     ─────●──────────●────→  (tag: v0.1.0, v0.2.0)
              ↑          ↑
release  ──── v0.1.0 ─── v0.2.0
              ↑          ↑
develop  ────●──●──●──●──●──→  (持续集成)
              ↑  ↑  ↑
             ci/ feat/ fix/
```

| 分支 | 用途 | 从哪拉 | 合并到哪 |
|------|------|--------|---------|
| `main` | 仅含 release 节点，始终可部署 | — | — |
| `develop` | 持续集成分支 | `main` | — |
| `feat/*` `refactor/*` `perf/*` | 功能开发 | `develop` | `develop` |
| `ci/*` `test/*` `build/*` | 基建搭建 | `develop` | `develop` |
| `fix/*` | 集成修复 | `develop` | `develop` |
| `spike/*` | ADR 技术验证 | `develop` | 不合并（保留） |
| `release/*` | 版本发布 | `develop` | `main` + `develop` |
| `hotfix/*` | 生产热修复 | `main` | `main` + `develop` |

一个执行容器 = 一个分支，编号与执行容器对应。

---

## 五、版本策略

版本格式遵循 `MAJOR.MINOR.PATCH`（X.Y.Z），参考 [Semantic Versioning](https://semver.org/)：

| 段 | 何时升 | 示例 |
|----|--------|------|
| MAJOR | 不兼容的 API 变更 | `0.1.0 → 1.0.0` |
| MINOR | 新增功能，向后兼容 | `0.1.0 → 0.2.0` |
| PATCH | 向后兼容的 bug 修复 | `0.1.0 → 0.1.1` |

MAJOR=0 期间（0.x.y）：MINOR 升功能，PATCH 修 bug。

---

## 六、测试

### 测试命令

| 命令 | 用途 |
|------|------|
| `pytest tests/unit/` | L1 单元测试 |
| `pytest tests/integration/` | L2 集成测试 |

### 测试目录

| 层级 | 目录路径 | 说明 |
|------|---------|------|
| L1 单元测试 | `tests/unit/` | 单 Phase Agent 可靠性 |
| L2 集成测试 | `tests/integration/` | 跨 Phase 信息流 |

---

## 七、PR 流程

- 从功能分支发起 PR 到 `develop`
- PR 描述需包含关联的 AC 编号
- CI 必须通过（L1 + L2）
- 至少一人 Review 通过后合并

---

## 八、许可证

MIT