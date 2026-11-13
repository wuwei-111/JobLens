# 数据交付报告

**生成日期：2026-11-13**

## 上海真实数据（`shanghai-*`）

这些文件由 `backend/data/raw/shanghai_graduate_jobs_2026-11-13.json` 的
**280 条真实校招记录**生成，是当前交付材料。

| 文件 | 内容 | 生成方式 |
| --- | --- | --- |
| `shanghai-quality.json` | 离线数据集检查报告 | `python -m scripts.check_dataset data/raw/shanghai_graduate_jobs_2026-11-13.json --json` |
| `shanghai-quality-summary.json` | 已入库数据的质量摘要 | `GET /api/v1/stats/quality` |
| `shanghai-overview.json` | 数据总览 | `GET /api/v1/stats/overview` |
| `shanghai-batches.json` | 导入批次记录 | `GET /api/v1/imports/batches` |
| `shanghai-cross.json` | 岗位类别 × 学历交叉统计 | `GET /api/v1/stats/cross?row=job_type&column=education` |
| `shanghai-jobs.csv` | 岗位 CSV 导出（UTF-8 BOM） | `GET /api/v1/exports/jobs.csv` |
| `shanghai-verify.json` | Pandas 独立重算与 API 的逐项核对（825/825 通过） | `python -m scripts.verify_stats ... --json` |

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
| `demo-verify.json` | Pandas 独立重算与 API 的逐项核对报告 | `python -m scripts.verify_stats --json` |

## 复现

先停止 API（Windows 下数据库文件会被占用），然后重建数据库并重启：

```bash
cd backend
# 上海真实数据
python -m scripts.reset_db data/raw/shanghai_graduate_jobs_2026-11-13.json --yes
# 或演示数据
python -m scripts.reset_db --yes
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

再重新生成报告（另开终端，在 `backend/` 下）：

```bash
# 上海真实数据
DATA=data/raw/shanghai_graduate_jobs_2026-11-13.json
python -m scripts.check_dataset "$DATA" --json > data/reports/shanghai-quality.json
python -m scripts.verify_stats "$DATA" --json > data/reports/shanghai-verify.json
curl -s http://127.0.0.1:8000/api/v1/stats/overview > data/reports/shanghai-overview.json
curl -s http://127.0.0.1:8000/api/v1/stats/quality > data/reports/shanghai-quality-summary.json
curl -s http://127.0.0.1:8000/api/v1/imports/batches > data/reports/shanghai-batches.json
curl -s "http://127.0.0.1:8000/api/v1/stats/cross?row=job_type&column=education" > data/reports/shanghai-cross.json
curl -s http://127.0.0.1:8000/api/v1/exports/jobs.csv > data/reports/shanghai-jobs.csv

# 演示数据（可选）
python -m scripts.check_dataset data/raw/sample_jobs.json --json > data/reports/demo-quality.json
python -m scripts.verify_stats --json > data/reports/demo-verify.json
```

`shanghai-verify.json` 与 `demo-verify.json` 的 `failed` 均应为 0。后续合并新数据后，
用同一套命令重新生成并替换 `shanghai-*`（或按城市/批次另建前缀）。
