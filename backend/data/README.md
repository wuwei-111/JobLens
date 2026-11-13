# 数据目录

| 路径 | 用途 | 是否入库 |
| --- | --- | --- |
| `raw/` | 原始 / 半清洗 JSON 数据集 | 是（仅 JSON） |
| `processed/` | 清洗后的中间文件 | 否（.gitignore） |
| `joblens.db` | SQLite 数据库（运行后生成） | 否 |

## shanghai_graduate_jobs_2026-11-13.json

**当前正式数据集：上海计算机类应届生公开校招岗位，280 条，采集于 2026-11-13。**

- 来源：牛客网校园招聘，逐条保留 `source_url` 与采集时间；
- 城市均为上海，岗位类别 9 类，覆盖 65 家企业；
- 薪资：134 条有明确月薪，146 条“面议”（薪资有效率为 47.9%）；
- 离线检查 280/280 可导入；独立核对 825/825 项与 API 一致；
- 这是阶段性样本，后续还会合并其他数据；页面结论只适用于当前样本。

重建数据库并导入：

```bash
# 在 backend 目录、已激活虚拟环境时
python -m scripts.reset_db data/raw/shanghai_graduate_jobs_2026-11-13.json --yes
```

追加/更新（不删库）：

```bash
python -m scripts.import_sample data/raw/shanghai_graduate_jobs_2026-11-13.json --on-conflict update
```

## sample_jobs.json

**这是虚构的演示数据，共 10 条，仅用于开发、页面展示与接口联调。**

- 企业名称均带「（虚构）」，链接指向 example.com。
- 不得用这些数据撰写新闻结论。
- `npm run dev` 在数据库为空时优先导入上海真实数据；仅当真实文件缺失时才导入本文件。已有数据时不会覆盖。
- 正式数据采集完成后，应新增真实数据文件（如 `jobs_hangzhou_2026-11.json`），并在
  `docs/data-dictionary.md` 中记录采集口径、时间与来源。

## 导入方式

```bash
# 在 backend 目录、已激活虚拟环境时
python -m scripts.import_sample
# 或指定文件
python -m scripts.import_sample data/raw/sample_jobs.json --on-conflict update
```

## 入库前检查

```bash
# 离线检查，不启动服务、不写库
python -m scripts.check_dataset data/raw/sample_jobs.json
# 输出完整 JSON 报告
python -m scripts.check_dataset data/raw/sample_jobs.json --json > quality.json
```

正式数据还应通过 `POST /api/v1/imports/validate` 预检，并在导入后查看
`GET /api/v1/imports/batches` 与 `GET /api/v1/stats/quality`。

## 入库后统计核对

```bash
# 需后端已启动，且已导入同一数据集
python -m scripts.verify_stats
python -m scripts.verify_stats --json > verify.json
```

脚本从原始 JSON 独立重算学历、经验、技能、薪资，逐项与 API 对比；上海真实数据当前
825/825 项一致，演示数据 359/359 项一致。

## 重建与性能

```bash
# 字段/索引变化后：先停止 API，再重建数据库并导入
python -m scripts.reset_db --yes

# 500 条临时数据下的接口延迟（不碰本目录的数据库）
python -m scripts.benchmark_api
```

`reports/` 保存上海真实数据（`shanghai-*`）与 10 条演示数据（`demo-*`）的核对与导出报告，说明见
[`reports/README.md`](reports/README.md)。
