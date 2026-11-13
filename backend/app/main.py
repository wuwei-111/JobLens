"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.v1.router import api_router
from app.core import settings
from app.db.init_db import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Create tables on startup; schema migrations are intentionally out of
    # scope for this course project (see docs/TODO.md).
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "计算机类应届毕业生招聘数据新闻作品的后端服务："
        "JSON 导入、招聘查询、学历/经验/技能/薪资统计。"
    ),
    lifespan=lifespan,
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")
