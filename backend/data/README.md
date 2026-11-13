# 数据目录

| 路径 | 用途 | 是否入库 |
| --- | --- | --- |
| `raw/` | 原始 / 半清洗 JSON 数据集 | 是（仅 JSON） |
| `processed/` | 清洗后的中间文件 | 否（.gitignore） |
| `joblens.db` | SQLite 数据库（运行后生成） | 否 |

## 当前正式数据集（五城合并，1021 条）

**北京、上海、深圳、杭州、成都计算机类应届生公开校招岗位，采集于 2026-11-13。**

| 文件 | 城市 | 条数 | 来源 |
| --- | --- | --- | --- |
| `raw/shanghai_graduate_jobs_2026-11-13.json` | 上海 | 280 | 牛客网校园招聘 |
| `raw/hangzhou_graduate_jobs_2026-11-13_expanded.json` | 杭州 | 228 | 牛客网 + 国家大学生就业服务平台 |
| `raw/beijing_graduate_jobs_2026-11-13.json` | 北京 | 224 | 牛客网校园招聘 |
| `raw/shenzhen_graduate_jobs_2026-11-13_expanded.json` | 深圳 | 157 | 牛客网 + 国家大学生就业服务平台 |
| `raw/chengdu_graduate_jobs_2026-11-13_expanded.json` | 成都 | 132 | 牛客网 + 国家大学生就业服务平台 |

合并口径：

- 1021 条记录，覆盖 5 个城市、224 家企业、18 个岗位类别、109 个技能词；
- 每条保留 `source_url` 与采集时间；来源为牛客网校园招聘 828 条、国家大学生就业服务平台 193 条；
- 记录 id 带城市前缀（`sh_` / `bj_` / `sz_` / `hz_` / `cd_`），原始平台 id 保存在 `source_job_id`；
- 同一岗位在多个城市发布时，每个城市各保留一条，因此全库 id 唯一（1021/1021），但同一 `source_url` 可能出现在多个城市；
- 薪资：573 条有明确月薪，448 条“面议”（薪资有效率 56.1%）；
- 离线检查 1021/1021 可导入；独立核对 1218/1218 项与 API 一致；
- 学历、经验为可复核的自动规则编码。15 条记录的经验字段保留了超过 30 字的原文摘句，统计中按原值单列，需人工复核；
- 这是阶段性便利样本，页面结论只适用于当前样本。

重建数据库并导入全部五份数据：

```bash
# 在 backend 目录、已激活虚拟环境时
python -m scripts.reset_db --yes
```

追加/更新单个文件（不删库）：

```bash
python -m scripts.import_sample data/raw/beijing_graduate_jobs_2026-11-13.json --on-conflict update
```

## sample_jobs.json

**这是虚构的演示数据，共 10 条，仅用于开发、页面展示与接口联调。**

- 企业名称均带「（虚构）」，链接指向 example.com。
- 不得用这些数据撰写新闻结论。
- `npm run dev` 在数据库为空时按文件名顺序导入 `data/raw/` 下全部 `*_graduate_jobs_*.json`；仅当没有任何真实数据文件时才导入本文件。已有数据时不会覆盖。

## 导入方式

```bash
# 在 backend 目录、已激活虚拟环境时
python -m scripts.import_sample
# 或指定文件
python -m scripts.import_sample data/raw/beijing_graduate_jobs_2026-11-13.json --on-conflict update
```

## 入库前检查

```bash
# 离线检查，不启动服务、不写库
python -m scripts.check_dataset data/raw/beijing_graduate_jobs_2026-11-13.json
# 输出完整 JSON 报告
python -m scripts.check_dataset data/raw/beijing_graduate_jobs_2026-11-13.json --json > data/reports/beijing-quality.json
```

正式数据还应通过 `POST /api/v1/imports/validate` 预检，并在导入后查看
`GET /api/v1/imports/batches` 与 `GET /api/v1/stats/quality`。

## 入库后统计核对

```bash
# 需后端已启动，且已导入同一批数据集
python -m scripts.verify_stats
# 默认合并 data/raw/ 下全部真实数据；也可只传指定文件
python -m scripts.verify_stats data/raw/shanghai_graduate_jobs_2026-11-13.json --json > shanghai-verify.json
```

脚本从原始 JSON 独立重算学历、经验、技能、薪资，逐项与 API 对比；五城合并数据当前
1218/1218 项一致，演示数据 359/359 项一致。

## 重建与性能

```bash
# 字段/索引变化后：先停止 API，再重建数据库并导入全部真实数据
python -m scripts.reset_db --yes

# 500 条临时数据下的接口延迟（不碰本目录的数据库）
python -m scripts.benchmark_api
```

`reports/` 保存五城合并数据（`all-cities-*`）、各城市离线质量报告（`*-quality.json`）与
10 条演示数据（`demo-*`）的核对与导出报告，说明见
[`reports/README.md`](reports/README.md)。
