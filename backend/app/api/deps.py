"""Shared FastAPI dependencies."""

from __future__ import annotations

from fastapi import Query
from pydantic import BaseModel


class StatsFilters(BaseModel):
    """Filters accepted by every statistics endpoint."""

    job_type: str | None = None
    education: str | None = None
    experience: str | None = None
    city: str | None = None


def get_stats_filters(
    job_type: str | None = Query(None, description="岗位类别"),
    education: str | None = Query(None, description="学历要求"),
    experience: str | None = Query(None, description="经验要求"),
    city: str | None = Query(None, description="城市"),
) -> StatsFilters:
    return StatsFilters(
        job_type=job_type,
        education=education,
        experience=experience,
        city=city,
    )


__all__ = ["StatsFilters", "get_stats_filters"]
