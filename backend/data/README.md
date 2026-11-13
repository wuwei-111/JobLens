# 数据目录

| 路径 | 用途 | 是否入库 |
| --- | --- | --- |
| `raw/` | 原始 / 半清洗 JSON 数据集 | 是（仅 JSON） |
| `processed/` | 清洗后的中间文件 | 否（.gitignore） |
| `joblens.db` | SQLite 数据库（运行后生成） | 否 |

## sample_jobs.json

**这是虚构的演示数据，共 40 条，仅用于开发与接口联调。**

- 企业名称均带「（虚构）」，链接指向 example.com。
- 不得用这些数据撰写新闻结论。
- 正式数据采集完成后，应新增真实数据文件（如 `jobs_hangzhou_2026-11.json`），并在
  `docs/data-dictionary.md` 中记录采集口径、时间与来源。

## 导入方式

```bash
# 在 backend 目录、已激活虚拟环境时
python -m scripts.import_sample
# 或指定文件
python -m scripts.import_sample data/raw/sample_jobs.json --on-conflict update
```
