"""Response schemas for statistics endpoints.

All ratios are 0-1 decimals rounded to 4 places and always use an explicit
denominator. See ``docs/architecture.md`` for the statistical definitions.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class CountItem(BaseModel):
    name: str
    count: int
    ratio: float


class GroupedCounts(BaseModel):
    group: str
    total: int
    distribution: list[CountItem]


class OverviewOut(BaseModel):
    total_jobs: int
    total_companies: int
    total_cities: int
    total_job_types: int
    total_skills: int
    salary_available: int = Field(description="薪资有效的岗位数（排除面议/缺失）")
    salary_avg: float | None = Field(description="月薪区间中点的平均值，单位元/月")
    salary_median: float | None = Field(description="月薪区间中点的中位数，单位元/月")
    fresh_graduate_count: int
    fresh_graduate_ratio: float
    last_collected_at: date | None


class EducationStatsOut(BaseModel):
    total: int
    breakdown: list[CountItem]
    by_job_type: list[GroupedCounts]


class FreshGraduateStats(BaseModel):
    count: int
    ratio: float
    breakdown: list[CountItem]


class ExperienceStatsOut(BaseModel):
    total: int
    breakdown: list[CountItem]
    by_job_type: list[GroupedCounts]
    fresh_graduate: FreshGraduateStats


class SkillItem(BaseModel):
    skill: str
    category: str
    count: int = Field(description="包含该技能的岗位数")
    ratio: float = Field(description="包含该技能的岗位数 / 总岗位数")


class SkillCategoryItem(BaseModel):
    category: str
    count: int = Field(description="至少包含一项该类别技能的岗位数")
    ratio: float = Field(description="岗位数 / 总岗位数；各类别可重叠，不可相加")


class JobTypeSkillGroup(BaseModel):
    job_type: str
    total_jobs: int
    skills: list[SkillItem]


class SkillsStatsOut(BaseModel):
    total_jobs: int
    total_skills: int
    items: list[SkillItem]
    categories: list[SkillCategoryItem]
    by_job_type: list[JobTypeSkillGroup]


class SalarySummary(BaseModel):
    count: int
    avg: float | None
    median: float | None
    p25: float | None
    p75: float | None
    min: float | None
    max: float | None


class SalaryBin(BaseModel):
    label: str
    range_min: int | None
    range_max: int | None
    count: int
    ratio: float


class SalaryGroup(SalarySummary):
    group: str


class SalaryStatsOut(BaseModel):
    total_jobs: int
    salary_available: int
    overall: SalarySummary
    distribution: list[SalaryBin]
    by_job_type: list[SalaryGroup]
    by_education: list[SalaryGroup]
    by_experience: list[SalaryGroup]
