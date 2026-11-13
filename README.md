# JobLens

> 《学历之外，企业还看重什么？——基于某城市计算机类应届毕业生招聘岗位的数据调查》

一个以**数据分析和新闻叙事**为核心的交互式数据新闻作品。系统将招聘信息整理为结构化数据集，通过 FastAPI 提供查询与统计接口，并由 Vue 3 + ECharts 完成交互式展示。

> 当前状态：**北京、上海、深圳、杭州、成都五城共 1021 条真实校招数据已合并入库，JSON → SQLite → FastAPI → Vue/ECharts 全链路已打通**。数据库、导入/预检/质量/交叉/导出接口可用；首页为单页长滚动专题，详情页支持四维筛选与 URL 状态、技能→岗位抽屉；数据说明页展示实时质量摘要、来源与导入批次。演示模式根据 `/stats/quality` 自动切换，当前已自动隐藏。该数据集是阶段性便利样本，进度见 [docs/TODO.md](docs/TODO.md)。

## 技术栈

| 层 | 技术 | 说明 |
| --- | --- | --- |
| 数据 | JSON → SQLite | 原始 JSON 保留，SQLite 存储规范化数据 |
| 后端 | Python 3.12+ / FastAPI / SQLAlchemy 2 | 导入、查询、统计接口 |
| 统计 | Pandas / SQL 聚合 | 统计口径统一放在后端 |
| 前端 | Vue 3 + Vite + TypeScript | 前后端分离 |
| 可视化 | ECharts | 图表统一由后端统计数据驱动 |
| 设计 | 数字新闻杂志风 | 纸白 `#F7F6F2` / 墨 `#20252B` / 橙红 `#E76F51` / 深蓝 `#315A7D` / 青绿 `#4C9A86` |
| 测试 | Pytest / HTTPX | 后端接口与导入测试 |

## 目录结构

```
JobLens/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口、CORS、生命周期
│   │   ├── core/                # 配置
│   │   ├── db/                  # 引擎、会话、建表
│   │   ├── models/              # job_postings / job_skills / import_batches
│   │   ├── schemas/             # Pydantic 请求/响应模型
│   │   ├── api/v1/              # health / imports / jobs / stats / meta / exports
│   │   ├── services/            # 导入、预检、规范化、统计、质量
│   │   └── ...
│   ├── data/raw/                # 原始 JSON（五城 1021 条真实数据；sample_jobs.json 为 10 条虚构演示数据）
│   ├── data/reports/            # 数据交付报告（真实数据 + 演示数据，质量/批次/核对/CSV）
│   ├── scripts/                 # 导入、检查、核对、重建、性能基准
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/                 # Axios 客户端与接口封装
│   │   ├── components/charts/   # ECharts 封装组件
│   │   ├── router/              # 5 个页面路由
│   │   ├── views/               # 首页 / 学历经验 / 技能 / 薪资 / 数据说明
│   │   ├── types/               # 与后端对齐的类型定义
│   │   └── styles/
│   ├── vite.config.ts
│   └── package.json
├── docs/
│   ├── TODO.md                  # 详细任务清单（开发主看板）
│   ├── architecture.md          # 架构、数据库、API、统计口径
│   └── data-dictionary.md       # 数据字段与规范化规则
└── .github/workflows/ci.yml     # 后端测试 + 前端构建
```

## 快速开始

### 一键启动（推荐）

前置要求：Node.js ≥ 20、Python ≥ 3.12（`python` 命令需在 PATH 中）。在项目根目录执行：

```bash
npm run dev
```

首次运行会自动完成：创建 `backend/.venv`、安装 Python 依赖、安装前端依赖。数据库为空时会按文件名顺序导入 `backend/data/raw/` 下全部真实数据集；真实文件缺失时才回退到 10 条虚构演示数据。已有数据不会被覆盖。随后同时启动前后端。

- 前端页面：<http://localhost:5173>
- 后端 API 文档：<http://127.0.0.1:8000/docs>
- 健康检查：<http://127.0.0.1:8000/api/v1/health>

按 `Ctrl+C` 会同时停止两个服务。Windows 也可以双击根目录的 `dev.bat`。

只启动单个服务：

```bash
npm run dev:backend
npm run dev:frontend
```

### 手动启动（调试用）

#### 后端

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env          # Windows 可用 copy .env.example .env
uvicorn app.main:app --reload
```

#### 前端

```bash
cd frontend
npm install
npm run dev
```

前端默认运行在 <http://localhost:5173>，通过 Vite 代理访问 `/api` → `http://127.0.0.1:8000`。

### 导入数据

当前正式数据集为 `backend/data/raw/` 下的五份城市 JSON，采集于 2026-11-13，合并共 **1021 条**：

| 文件 | 城市 | 条数 |
| --- | --- | --- |
| `shanghai_graduate_jobs_2026-11-13.json` | 上海 | 280 |
| `hangzhou_graduate_jobs_2026-11-13_expanded.json` | 杭州 | 228 |
| `beijing_graduate_jobs_2026-11-13.json` | 北京 | 224 |
| `shenzhen_graduate_jobs_2026-11-13_expanded.json` | 深圳 | 157 |
| `chengdu_graduate_jobs_2026-11-13_expanded.json` | 成都 | 132 |

记录 id 带城市前缀（`sh_` / `bj_` / `sz_` / `hz_` / `cd_`），原始平台 id 保存在 `source_job_id`；同一岗位在多个城市发布时，每个城市各保留一条。

重建数据库并导入全部五份数据（会删除现有 SQLite 数据库，先停止 API）：

```bash
cd backend
python -m scripts.reset_db --yes
```

也可以只导入指定文件：

```bash
python -m scripts.reset_db data/raw/beijing_graduate_jobs_2026-11-13.json --yes
```

只追加/更新、不删库时，可以走接口：

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/imports/json?on_conflict=update" \
  -F "file=@backend/data/raw/shanghai_graduate_jobs_2026-11-13.json"
```

也可以使用命令行脚本（自动建表，默认读取演示数据；正式数据请传路径）：

```bash
cd backend
python -m scripts.import_sample data/raw/shanghai_graduate_jobs_2026-11-13.json --on-conflict update
```

> `sample_jobs.json` 仍是 **10 条虚构演示数据**，只用于开发调试与页面展示，不能用于新闻结论。真实数据导入后，`/stats/quality` 的 `demo_records` 为 0，前端演示提示会自动消失。

> **Git 数据边界**：SQLite 数据库 `backend/data/joblens.db` 不进入 Git（`.gitignore` 已忽略 `*.db`）。仓库只跟踪原始 JSON 与生成报告；数据库由 `scripts/reset_db.py` 或导入接口重建，避免把运行期数据库混进版本库。

### 正式数据检查

正式数据入库前，先跑离线检查和预检接口：

```bash
cd backend
python -m scripts.check_dataset data/raw/beijing_graduate_jobs_2026-11-13.json --json > data/reports/beijing-quality.json
# 每份城市数据各跑一次；`data/reports/*-quality.json` 已保存五城结果
```

服务启动后也可以调用：

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/imports/validate" \
  -F "file=@data/raw/beijing_graduate_jobs_2026-11-13.json"
```

预检只读、不写库，会报告缺失字段、未知学历/经验、薪资异常、空技能、重复链接、演示记录，以及数据库中已有的 id 数量。确认后按上面的导入方式入库，并用 `GET /api/v1/imports/batches` 与 `GET /api/v1/stats/quality` 查看批次和质量摘要。

### 统计口径交叉核对

导入后运行独立核对脚本。它从原始 JSON 用 Pandas 重算学历、经验、技能、薪资，再逐项与运行中的 API 比对：

```bash
cd backend
# 默认合并 data/raw/ 下全部真实数据（与 reset_db / seed_if_empty 一致）
python -m scripts.verify_stats --json > data/reports/all-cities-verify.json
# 也可以只核对指定文件
python -m scripts.verify_stats data/raw/shanghai_graduate_jobs_2026-11-13.json --json > shanghai-verify.json
# 演示数据
python -m scripts.verify_stats data/raw/sample_jobs.json --json > data/reports/demo-verify.json
```

五城 1021 条当前 **1218/1218** 项一致（`failed=0`）；演示数据为 359/359。交付时以 `data/reports/all-cities-verify.json` 为准。

### 数据库重建与性能基准

字段或索引变化时（课程项目不使用 Alembic），停止 API 后重建数据库并重新导入：

```bash
cd backend
# 五城正式数据（默认导入 data/raw/ 下全部 *_graduate_jobs_*.json）
python -m scripts.reset_db --yes
# 只导入演示数据
python -m scripts.reset_db data/raw/sample_jobs.json --yes
```

500 条数据下的接口性能基准（使用临时数据库，不会改动现有数据）：

```bash
python -m scripts.benchmark_api
```

500 条临时数据下所有接口 median 与 p95 均低于 300ms（最慢的 CSV 导出 p95 约 58ms）。

### 交叉统计与 CSV 导出

```bash
# 岗位类别 × 学历
curl "http://127.0.0.1:8000/api/v1/stats/cross?row=job_type&column=education"

# 按筛选条件导出全部岗位
curl "http://127.0.0.1:8000/api/v1/exports/jobs.csv" -o jobs.csv
```

### 交付报告

`backend/data/reports/` 已生成五城合并数据的导入批次、总览、城市 × 学历交叉、CSV 与统计核对报告（`all-cities-*`），以及每份城市数据的离线质量报告（`shanghai-` / `beijing-` / `shenzhen-` / `hangzhou-` / `chengdu-quality.json`）；10 条虚构演示数据的对应报告保留为 `demo-*`。生成方式与注意事项见 [backend/data/reports/README.md](backend/data/reports/README.md)。

### 测试

```bash
# 后端
cd backend
pytest

# 前端（Vitest）
cd frontend
npm run test:unit
```

## 已实现 / 待实现

已实现：

- SQLite 两张表：`job_postings`、`job_skills`
- JSON 导入：格式校验、字段规范化、重复记录跳过/更新、错误明细
- 招聘数据分页查询与筛选（岗位类型、学历、经验、城市、薪资、关键词）
- 统计接口：总览、学历、经验、技能、薪资
- 筛选元数据接口（岗位类型 / 学历 / 经验 / 城市 / 技能）
- 一键启动脚本 `npm run dev`（自动准备环境、数据库为空时优先导入真实数据、同时启动前后端）
- 首页单页长滚动专题：Hero、样本档案、数据概览、章节索引、学历 / 经验 / 技能 / 薪资四章叙事、结论与边界、阅读进度条
- 四个详情页与 ECharts 图表：学历构成、学历 × 岗位类别矩阵、经验分布、技能排行、技能类别、技能矩阵、薪资直方图、岗位薪资区间、学历/经验薪资对照
- 四维筛选（岗位类别 / 学历 / 经验 / 城市）与 URL query 同步；无结果时提供清除入口；图表 / 数据表切换
- 技能点击 → 岗位抽屉：技能条形、数据表技能名、首页技能词墙均可打开匹配岗位；抽屉支持键盘焦点与 Esc 关闭
- 数据说明页：实时质量摘要、质量警告、最近导入批次、CSV 下载；演示模式根据 `/stats/quality` 自动切换，城市与样本量动态读取
- 数据质量工具：离线检查脚本 `scripts/check_dataset.py`、只读预检 `POST /imports/validate`、导入批次 `GET /imports/batches`、质量摘要 `GET /stats/quality`
- 统计交叉核对脚本 `scripts/verify_stats.py`：Pandas 独立重算并与 API 逐项比对
- 交叉统计 `GET /stats/cross`、CSV 导出 `GET /exports/jobs.csv`、统一错误响应（`detail` + `code` + `errors`）
- 数据库重建脚本 `scripts/reset_db.py`、500 条性能基准 `scripts/benchmark_api.py`、复合索引
- ECharts 按需加载 + 路由懒加载：主包约 171KB，图表共享块约 493KB
- 五城 1021 条真实数据已合并导入；独立核对 1218/1218 项一致，`/stats/quality` 显示 `demo_records=0`
- 53 个后端测试、11 个前端 Vitest 测试与 GitHub Actions CI

待实现：逐页最终人工复核、可选 Playwright 冒烟与 Firefox 复核、创作报告与部署。详见 [docs/TODO.md](docs/TODO.md)。

## 文档

- [项目大纲](大纲.md)
- [任务清单 docs/TODO.md](docs/TODO.md)
- [系统架构与 API docs/architecture.md](docs/architecture.md)
- [数据字典 docs/data-dictionary.md](docs/data-dictionary.md)

## 数据与结论边界

本作品的数据仅来自特定城市、特定时间段、公开渠道的招聘样本，**不能代表全国就业市场**。所有新闻结论必须由实际数据计算得出，并标注样本量与统计口径。

当前五城数据共 1021 条，覆盖上海、杭州、北京、深圳、成都；其中 448 条薪资为“面议”，薪资统计的有效样本为 573 条（56.1%）。薪资结论只描述**披露了薪资的岗位**，不能外推到全部岗位；技能为空或超过 10 项的记录也保留原始信息，不强行补齐。同一岗位在多个城市发布时按城市各计一次，因此城市间比较应按城市分层阅读，不能把 1021 条当作 1021 个互不相同的岗位。
