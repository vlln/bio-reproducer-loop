# Phase 产物契约测试 fixture（单元 02：Data phase）

来源：远端校准持久资产区 `/storeData/gs/claroai-calibration/runs/`（gs@172.16.209.237），
与 ADR-0011 验证 3 所用归档一致。测试不联网、不依赖远端存在。

| fixture | 来源 | 处理 | 契约用例 |
|---------|------|------|---------|
| `bench-234/p4_gse136831.log` | bench-234 `04_data/p4_gse136831.log` | 原文拷贝（88 B，2 行） | 传输层失败 + 回退工具缺失 → `not_attempted` |
| `bench-234/p4_gse289881.log` | bench-234 `04_data/p4_gse289881.log` | **裁剪**：原始 229,833 字符，滤除 curl 进度条行，仅保留终态信号行（`curl: (56)`、`Download complete` ×2、`Resuming from byte`、`ls -l`），440 字符 | 中途失败但续传完成 → `completed` |
| `bench-217/data_manifest.md` | bench-217 `04_data/data_manifest.md` | 原文拷贝（970 B） | 无获取日志/无校验文件 → 无证据（不得判外部不可得） |

裁剪说明：`p4_gse289881.log` 的进度条（`\r` 分隔的 `% Total`/`Progress:` 行）对终态
判定无信息量，故不保留；判定信号全部保留。`bench-217` 归档实际有 `04_data/` 目录，
但仅含散文 `data_manifest.md`（BLOCKED）+ 空 `raw_data/`/`reference/`，无任何 .log 与
校验文件——这正是 ADR-0011 §2.1 的「有目录但无证据」反例。
