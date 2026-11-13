"""Schemas for dataset quality checks and summaries."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class ValueCount(BaseModel):
    value: str
    count: int


class QualityStatsOut(BaseModel):
    """Dataset-level quality summary for the data notes page and delivery report."""

    total_jobs: int
    salary_available: int
    salary_missing: int = Field(description="salary_min 与 salary_max 都为空的岗位数")
    salary_single_bound: int = Field(description="只有一边薪资的岗位数")
    salary_invalid_range: int = Field(description="salary_min > salary_max 的岗位数")
    salary_outliers: int = Field(description="已知薪资 < 2000 或 > 100000 的岗位数")
    unknown_education: list[ValueCount] = Field(default_factory=list)
    unknown_experience: list[ValueCount] = Field(default_factory=list)
    jobs_without_skills: int
    duplicate_source_urls: list[ValueCount] = Field(default_factory=list)
    demo_records: int = Field(description="来源或链接显示为演示/虚构数据的岗位数")
    total_companies: int
    total_cities: int
    collected_from: date | None = None
    collected_to: date | None = None
    warnings: list[str] = Field(default_factory=list)
