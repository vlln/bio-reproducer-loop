# ClaroAI 校准运行资产索引

> 防止遗忘与无法复用：记录远端持久资产位置、每篇运行产物、评估与复现命令。
> 更新时机：每完成一篇校准运行（BL-013），同步更新本文件与远端 README。

## 远端持久资产（`/storeData/gs/claroai-calibration/`，25T 持久盘）

```
claroai-calibration/
├── README.md            # 远端自描述（结构、产物、复现命令）
├── runs/
│   ├── bench-200/       # HDM 多组学（paper_01）→ BLOCKED（作者 D2=0/D3=1 一致），981M 含下载数据
│   ├── bench-220/       # SciTotalEnv 流行病学 → REPRODUCED 100（作者 D1-D3=2 一致）
│   └── bench-222/       # TorchXRayVision（arXiv）→ REPRODUCED 100（作者 D1-D3=2 一致）
├── scripts/
│   ├── bench-v3.sh      # 批量校准入口：bash bench-v3.sh <bench-NNN>
│   └── watch.sh         # 运行完成 watcher
└── system/              # 构建资产（后续 32 篇校准复用）
    ├── system-image.tar (2.0G) + .sha256/.image-id/.image-ref
    ├── summary.json     # 构建 provenance
    └── system-artifact/ (2.0G)  # opaque artifact（loop 源 + 技能 + launcher）
```

**注意**：远端 `/tmp/bl012/` 为临时运行区（/tmp 重启即失），运行中的 run 完成后须
`mv /tmp/bl012/run-bench-<id>-* /storeData/gs/claroai-calibration/runs/bench-<id>`
并更新本文件。

## 评估已完成 run（独立评分 vs 作者 ground truth）

```bash
# 本地（需先 scp run 产物，或直接在远端仓库执行）
PYTHONPATH=. python3.12 benchmarks/converters/claroai/evaluate_run.py \
  /storeData/gs/claroai-calibration/runs/bench-220 benchmarks/entries/bench-220
# 输出：verdict / score / checks（python_verify 解析 data_manifest + provision.md）
# 对照：claims.yaml 的 calibration 段（作者 D1-D3 分数，只作校准）
```

## 复现新 run

```bash
# 远端
bash /storeData/gs/claroai-calibration/scripts/bench-v3.sh bench-203
# 输出 /tmp/bl012/run-bench-203-<ts>/ → 完成后移入 runs/ 并登记
```

## 已完成校准对照（累计）

| entry | 论文 | 系统 verdict | evaluator | 作者 calibration | 一致性 |
|-------|------|-------------|-----------|------------------|--------|
| bench-200 | HDM 多组学 | BLOCKED | PARTIAL 50（D3 一致） | D1=2/D2=0/D3=1 | ✅ 结论一致（复现数据不可得） |
| bench-220 | SciTotalEnv epi | REPRODUCED 100 | REPRODUCED 100 | D1=2/D2=2/D3=2 | ✅ 全一致 |
| bench-222 | TorchXRayVision | REPRODUCED 100 | REPRODUCED 100 | D1=2/D2=2/D3=2 | ✅ 全一致 |

校准结论：作者 D2>0（数据可获取）论文系统成功复现，D2=0 论文 BLOCKED——
实证验证 claroai-bench"元数据分预测可复现性"（Spearman r=0.68）。

## 可复用资产（本地仓库）

| 资产 | 位置 | 用途 |
|------|------|------|
| 评估脚本 | `benchmarks/converters/claroai/evaluate_run.py` | 完成 run 的独立评分 |
| 批量运行脚本 | 远端 `scripts/bench-v3.sh`（源：本会话临时，已复制至远端持久目录） | 参数化校准入口 |
| verify 模板 | `converter.py` 内 `VERIFY_TEMPLATE`（表格泛化 + 规范化匹配） | 审计证据解析 |
| 校准报告 | `docs/plans/0023-claroai-calibration/`（bench-200）、`docs/plans/0024-claroai-calibration-batch/`（第一批） | 对照记录 |
