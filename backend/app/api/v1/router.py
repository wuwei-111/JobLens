"""Aggregate all v1 routers."""

from fastapi import APIRouter

from app.api.v1 import health, imports, jobs, meta, stats

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(imports.router, prefix="/imports", tags=["imports"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(meta.router, prefix="/meta", tags=["meta"])
