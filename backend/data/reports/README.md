# 数据交付报告

**生成日期：2026-11-13**

## 五城合并真实数据（`all-cities-*`）

这些文件由 `backend/data/raw/` 下五份城市 JSON 合并后的 **1021 条真实校招记录**生成，
是当前交付材料。数据库导入顺序为 北京 → 成都 → 杭州 → 上海 → 深圳（文件名排序）。

| 文件 | 内容 | 生成方式 |
| --- | --- | --- |
| `all-cities-quality-summary.json` | 已入库数据的质量摘要 | `GET /api/v1/stats/quality` |
| `all-cities-overview.json` | 数据总览（1021 条、5 城、224 家企业、12 个岗位类别） | `GET /api/v1/stats/overview` |
| `all-cities-batches.json` | 五条导入批次记录 | `GET /api/v1/imports/batches` |
| `all-cities-cross.json` | 城市 × 学历交叉统计 | `GET /api/v1/stats/cross?row=city&column=education` |
| `all-cities-jobs.csv` | 岗位 CSV 导出（UTF-8 BOM） | `GET /api/v1/exports/jobs.csv` |
| `all-cities-verify.json` | Pandas 独立重算与 API 的逐项核对（1218/1218 通过） | `python -m scripts.verify_stats --json` |

## 各城市离线质量报告（`*-quality.json`）

| 文件 | 数据集 | 记录数 |
| --- | --- | --- |
| `shanghai-quality.json` | 上海 | 280 |
| `hangzhou-quality.json` | 杭州 | 228 |
| `beijing-quality.json` | 北京 | 224 |
| `shenzhen-quality.json` | 深圳 | 157 |
| `chengdu-quality.json` | 成都 | 132 |

生成方式（每份文件各跑一次）：

```bash
python -m scripts.check_dataset data/raw/<city>_graduate_jobs_*.json --json > data/reports/<city>-quality.json
```

## 演示数据（`demo-*`）

这些文件由 `backend/data/raw/sample_jobs.json` 的 **10 条虚构演示记录**生成，
用于验证后端全链路并作为报告格式示例。**它们不是真实招聘结论，不能用于新闻稿件。**

| 文件 | 内容 | 生成方式 |
| --- | --- | --- |
| `demo-quality.json` | 离线数据集检查报告（字段、枚举、薪资、技能、重复链接） | `python -m scripts.check_dataset data/raw/sample_jobs.json --json` |
| `demo-quality-summary.json` | 已入库数据的质量摘要 | `GET /api/v1/stats/quality` |
| `demo-overview.json` | 数据总览 | `GET /api/v1/stats/overview` |
| `demo-batches.json` | 导入批次记录（文件、时间、成功/跳过/失败数） | `GET /api/v1/imports/batches` |
| `demo-cross.json` | 岗位类别 × 学历交叉统计 | `GET /api/v1/stats/cross?row=job_type&column=education` |
| `demo-jobs.csv` | 岗位 CSV 导出（UTF-8 BOM，Excel 可直接打开） | `GET /api/v1/exports/jobs.csv` |
| `demo-verify.json` | Pandas 独立重算与 API 的逐项核对报告 | `python -m scripts.verify_stats data/raw/sample_jobs.json --json` |

## 复现

先停止 API（Windows 下数据库文件会被占用），然后重建数据库并重启：

```bash
cd backend
# 五城真实数据（默认导入 data/raw/ 下全部 *_graduate_jobs_*.json）
python -m scripts.reset_db --yes
# 或只导入演示数据
python -m scripts.reset_db data/raw/sample_jobs.json --yes
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

再重新生成报告（另开终端，在 `backend/` 下）：

```bash
# 五城合并数据
python -m scripts.verify_stats --json > data/reports/all-cities-verify.json
curl -s http://127.0.0.1:8000/api/v1/stats/overview > data/reports/all-cities-overview.json
curl -s http://127.0.0.1:8000/api/v1/stats/quality > data/reports/all-cities-quality-summary.json
curl -s http://127.0.0.1:8000/api/v1/imports/batches > data/reports/all-cities-batches.json
curl -s "http://127.0.0.1:8000/api/v1/stats/cross?row=city&column=education" > data/reports/all-cities-cross.json
curl -s http://127.0.0.1:8000/api/v1/exports/jobs.csv > data/reports/all-cities-jobs.csv

# 各城市离线质量检查
for f in data/raw/*_graduate_jobs_*.json; do
  name=$(basename "$f" _graduate_jobs_*.json)
  python -m scripts.check_dataset "$f" --json > "data/reports/${name}-quality.json"
done

# 演示数据（可选）
python -m scripts.check_dataset data/raw/sample_jobs.json --json > data/reports/demo-quality.json
python -m scripts.verify_stats data/raw/sample_jobs.json --json > data/reports/demo-verify.json
```

`all-cities-verify.json` 与 `demo-verify.json` 的 `failed` 均应为 0。注意：
`verify_stats` 默认核对 `data/raw/` 下全部真实数据，因此运行前数据库必须包含同一批数据。

## 口径提示

- 记录 id 带城市前缀（`sh_` / `bj_` / `sz_` / `hz_` / `cd_`），原始平台 id 在 `source_job_id`。
- 同一岗位在多个城市发布时按城市各保留一条，因此同一 `source_url` 可能出现在多个城市；
  质量摘要只把**同一城市内**的重复链接视为异常。
- 五城共 1021 条，但不等同于 1021 个互不相同的岗位；城市间比较应说明这一点。
