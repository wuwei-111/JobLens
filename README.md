# JobLens

> 《学历之外，企业还看重什么？——基于某城市计算机类应届毕业生招聘岗位的数据调查》

一个以**数据分析和新闻叙事**为核心的交互式数据新闻作品。系统将招聘信息整理为结构化数据集，通过 FastAPI 提供查询与统计接口，并由 Vue 3 + ECharts 完成交互式展示。

> 当前状态：**初始框架已完成**（数据库、导入、查询、核心统计接口可运行）。页面视觉与完整图表尚在开发中，进度见 [docs/TODO.md](docs/TODO.md)。

## 技术栈

| 层 | 技术 | 说明 |
| --- | --- | --- |
| 数据 | JSON → SQLite | 原始 JSON 保留，SQLite 存储规范化数据 |
| 后端 | Python 3.12+ / FastAPI / SQLAlchemy 2 | 导入、查询、统计接口 |
| 统计 | Pandas / SQL 聚合 | 统计口径统一放在后端 |
| 前端 | Vue 3 + Vite + TypeScript | 前后端分离 |
| 可视化 | ECharts | 图表统一由后端统计数据驱动 |
| 测试 | Pytest / HTTPX | 后端接口与导入测试 |

## 目录结构

```
JobLens/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口、CORS、生命周期
│   │   ├── core/                # 配置
│   │   ├── db/                  # 引擎、会话、建表
│   │   ├── models/              # job_postings / job_skills
│   │   ├── schemas/             # Pydantic 请求/响应模型
│   │   ├── api/v1/              # health / imports / jobs / stats / meta
│   │   ├── services/            # 导入、规范化、统计
│   │   └── ...
│   ├── data/raw/                # 原始 JSON（sample_jobs.json 为虚构演示数据）
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

### 1. 后端

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

启动后：

- API 文档（Swagger）：<http://127.0.0.1:8000/docs>
- 健康检查：<http://127.0.0.1:8000/api/v1/health>

### 2. 导入演示数据

方式一：在 Swagger 页面调用 `POST /api/v1/imports/json`，上传 `backend/data/raw/sample_jobs.json`。

方式二（Windows 请使用 `curl.exe`）：

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/imports/json?on_conflict=skip" \
  -F "file=@backend/data/raw/sample_jobs.json"
```

> `sample_jobs.json` 是**虚构的演示数据**，仅用于开发调试，不能用于新闻结论。

### 3. 前端

```bash
cd frontend
npm install
npm run dev
```

前端默认运行在 <http://localhost:5173>，通过 Vite 代理访问 `/api` → `http://127.0.0.1:8000`。

### 4. 测试

```bash
cd backend
pytest
```

## 已实现 / 待实现

已实现：

- SQLite 两张表：`job_postings`、`job_skills`
- JSON 导入：格式校验、字段规范化、重复记录跳过/更新、错误明细
- 招聘数据分页查询与筛选（岗位类型、学历、经验、城市、薪资、关键词）
- 统计接口：总览、学历、经验、技能、薪资
- 筛选元数据接口（岗位类型 / 学历 / 经验 / 城市 / 技能）
- 22 个后端测试与 GitHub Actions CI，前端路由与 API 客户端骨架

待实现：真实数据采集、完整前端页面与图表、数据说明页内容、报告与部署。详见 [docs/TODO.md](docs/TODO.md)。

## 文档

- [项目大纲](大纲.md)
- [任务清单 docs/TODO.md](docs/TODO.md)
- [系统架构与 API docs/architecture.md](docs/architecture.md)
- [数据字典 docs/data-dictionary.md](docs/data-dictionary.md)

## 数据与结论边界

本作品的数据仅来自特定城市、特定时间段、公开渠道的招聘样本，**不能代表全国就业市场**。所有新闻结论必须由实际数据计算得出，并标注样本量与统计口径。
