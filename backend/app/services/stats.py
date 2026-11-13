"""Statistics computed on the backend so every page uses the same caliber.

Definitions (also documented in ``docs/architecture.md``):

* Salary values use the midpoint of ``salary_min`` / ``salary_max``. Records
  with both bounds NULL ("面议") are excluded from salary statistics.
* Skill frequency = number of jobs containing the skill / number of filtered
  jobs. It is a job ratio, not a raw keyword occurrence count.
* All ratios use an explicitly returned denominator.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models import JobPosting, JobSkill
from app.schemas.stats import (
    CountItem,
    EducationStatsOut,
    ExperienceStatsOut,
    FreshGraduateStats,
    GroupedCounts,
    JobTypeSkillGroup,
    OverviewOut,
    SalaryBin,
    SalaryGroup,
    SalaryStatsOut,
    SalarySummary,
    SkillCategoryItem,
    SkillItem,
    SkillsStatsOut,
)
from app.services.filters import build_job_conditions
from app.services.skills import categorize_skill

EDUCATION_ORDER = [
    "不限",
    "大专",
    "本科",
    "本科及以上",
    "硕士",
    "硕士及以上",
    "博士",
    "其他",
    "未知",
]
EXPERIENCE_ORDER = ["不限", "应届生", "1年以内", "1-3年", "3-5年", "5年以上", "其他", "未知"]

# Fixed histogram bins make salary distributions comparable across pages.
SALARY_BINS: list[tuple[int | None, int | None, str]] = [
    (None, 8_000, "8K以下"),
    (8_000, 12_000, "8-12K"),
    (12_000, 16_000, "12-16K"),
    (16_000, 20_000, "16-20K"),
    (20_000, 30_000, "20-30K"),
    (30_000, None, "30K以上"),
]

_JOB_COLUMNS = [
    "id",
    "company",
    "position",
    "job_type",
    "city",
    "education",
    "experience",
    "is_fresh_graduate",
    "salary_min",
    "salary_max",
]


def _ratio(count: int, total: int) -> float:
    return round(count / total, 4) if total else 0.0


def _round(value: float) -> float:
    return round(float(value), 2)


def _load_jobs_frame(db: Session, **filters: Any) -> pd.DataFrame:
    conditions = build_job_conditions(
        job_type=filters.get("job_type"),
        education=filters.get("education"),
        experience=filters.get("experience"),
        city=filters.get("city"),
    )
    stmt = select(
        JobPosting.id,
        JobPosting.company,
        JobPosting.position,
        JobPosting.job_type,
        JobPosting.city,
        JobPosting.education,
        JobPosting.experience,
        JobPosting.is_fresh_graduate,
        JobPosting.salary_min,
        JobPosting.salary_max,
    ).where(*conditions)

    rows = [dict(row._mapping) for row in db.execute(stmt).all()]
    frame = pd.DataFrame(rows, columns=_JOB_COLUMNS)

    if frame.empty:
        frame["salary_mid"] = pd.Series(dtype="float64")
    else:
        salary = frame[["salary_min", "salary_max"]].apply(pd.to_numeric, errors="coerce")
        frame["salary_mid"] = salary.mean(axis=1, skipna=True)
        frame["is_fresh_graduate"] = (
            frame["is_fresh_graduate"].fillna(False).astype(bool)
        )
    return frame


def _count_items(
    series: pd.Series,
    total: int,
    order: list[str] | None = None,
) -> list[CountItem]:
    if total == 0:
        return []
    counts = series.fillna("未知").astype(str).value_counts()
    items = [
        CountItem(name=str(name), count=int(count), ratio=_ratio(int(count), total))
        for name, count in counts.items()
    ]
    if order:
        position = {name: index for index, name in enumerate(order)}
        items.sort(key=lambda item: (position.get(item.name, len(order)), -item.count))
    else:
        items.sort(key=lambda item: (-item.count, item.name))
    return items


def _group_distribution(
    frame: pd.DataFrame,
    group_column: str,
    value_column: str,
) -> list[GroupedCounts]:
    if frame.empty:
        return []
    groups: list[GroupedCounts] = []
    for group_name, group in frame.groupby(group_column, dropna=False):
        total = len(group)
        groups.append(
            GroupedCounts(
                group="未知" if pd.isna(group_name) else str(group_name),
                total=total,
                distribution=_count_items(group[value_column], total),
            )
        )
    groups.sort(key=lambda item: item.total, reverse=True)
    return groups


def _salary_summary(values: pd.Series) -> SalarySummary:
    values = pd.to_numeric(values, errors="coerce").dropna()
    if values.empty:
        return SalarySummary(
            count=0, avg=None, median=None, p25=None, p75=None, min=None, max=None
        )
    return SalarySummary(
        count=int(values.size),
        avg=_round(values.mean()),
        median=_round(values.median()),
        p25=_round(values.quantile(0.25)),
        p75=_round(values.quantile(0.75)),
        min=_round(values.min()),
        max=_round(values.max()),
    )


def _salary_distribution(frame: pd.DataFrame) -> list[SalaryBin]:
    values = pd.to_numeric(frame["salary_mid"], errors="coerce").dropna()
    total = int(values.size)
    bins: list[SalaryBin] = []
    for lower, upper, label in SALARY_BINS:
        if lower is None:
            mask = values < upper
        elif upper is None:
            mask = values >= lower
        else:
            mask = (values >= lower) & (values < upper)
        count = int(mask.sum())
        bins.append(
            SalaryBin(
                label=label,
                range_min=lower,
                range_max=upper,
                count=count,
                ratio=_ratio(count, total),
            )
        )
    return bins


def _salary_groups(frame: pd.DataFrame, column: str) -> list[SalaryGroup]:
    if frame.empty:
        return []
    groups: list[SalaryGroup] = []
    for group_name, group in frame.groupby(column, dropna=False):
        summary = _salary_summary(group["salary_mid"])
        if summary.count == 0:
            continue
        groups.append(
            SalaryGroup(
                group="未知" if pd.isna(group_name) else str(group_name),
                **summary.model_dump(),
            )
        )
    groups.sort(key=lambda item: item.count, reverse=True)
    return groups


def get_overview(db: Session) -> OverviewOut:
    frame = _load_jobs_frame(db)
    total = len(frame)
    salary = _salary_summary(frame["salary_mid"])
    fresh_count = int(frame["is_fresh_graduate"].sum()) if total else 0
    total_skills = db.scalar(select(func.count(distinct(JobSkill.skill_name)))) or 0
    last_collected_at = db.scalar(select(func.max(JobPosting.collected_at)))

    return OverviewOut(
        total_jobs=total,
        total_companies=int(frame["company"].nunique()) if total else 0,
        total_cities=int(frame["city"].nunique()) if total else 0,
        total_job_types=int(frame["job_type"].nunique()) if total else 0,
        total_skills=int(total_skills),
        salary_available=salary.count,
        salary_avg=salary.avg,
        salary_median=salary.median,
        fresh_graduate_count=fresh_count,
        fresh_graduate_ratio=_ratio(fresh_count, total),
        last_collected_at=last_collected_at,
    )


def get_education_stats(db: Session, **filters: Any) -> EducationStatsOut:
    frame = _load_jobs_frame(db, **filters)
    total = len(frame)
    return EducationStatsOut(
        total=total,
        breakdown=_count_items(frame["education"], total, EDUCATION_ORDER),
        by_job_type=_group_distribution(frame, "job_type", "education"),
    )


def get_experience_stats(db: Session, **filters: Any) -> ExperienceStatsOut:
    frame = _load_jobs_frame(db, **filters)
    total = len(frame)
    fresh_frame = frame[frame["is_fresh_graduate"]] if total else frame
    fresh_count = len(fresh_frame)

    return ExperienceStatsOut(
        total=total,
        breakdown=_count_items(frame["experience"], total, EXPERIENCE_ORDER),
        by_job_type=_group_distribution(frame, "job_type", "experience"),
        fresh_graduate=FreshGraduateStats(
            count=fresh_count,
            ratio=_ratio(fresh_count, total),
            breakdown=_count_items(
                fresh_frame["experience"], fresh_count, EXPERIENCE_ORDER
            ),
        ),
    )


def get_skills_stats(
    db: Session,
    *,
    limit: int = 20,
    per_type_limit: int = 8,
    **filters: Any,
) -> SkillsStatsOut:
    conditions = build_job_conditions(
        job_type=filters.get("job_type"),
        education=filters.get("education"),
        experience=filters.get("experience"),
        city=filters.get("city"),
    )

    total_jobs = db.scalar(
        select(func.count(JobPosting.id)).where(*conditions)
    ) or 0
    total_skills = db.scalar(
        select(func.count(distinct(JobSkill.skill_name)))
        .select_from(JobSkill)
        .join(JobPosting, JobPosting.id == JobSkill.job_id)
        .where(*conditions)
    ) or 0

    rows = db.execute(
        select(
            JobPosting.job_type,
            JobSkill.skill_name,
            func.count(distinct(JobSkill.job_id)).label("job_count"),
        )
        .select_from(JobSkill)
        .join(JobPosting, JobPosting.id == JobSkill.job_id)
        .where(*conditions)
        .group_by(JobPosting.job_type, JobSkill.skill_name)
    ).all()

    overall: dict[str, int] = {}
    by_type: dict[str, list[tuple[str, int]]] = {}
    for job_type, skill_name, job_count in rows:
        count = int(job_count)
        overall[skill_name] = overall.get(skill_name, 0) + count
        by_type.setdefault(job_type, []).append((skill_name, count))

    ranked = sorted(overall.items(), key=lambda item: (-item[1], item[0].casefold()))
    items = [
        SkillItem(
            skill=skill,
            category=categorize_skill(skill),
            count=count,
            ratio=_ratio(count, total_jobs),
        )
        for skill, count in ranked[:limit]
    ]

    type_totals = {
        row[0]: int(row[1])
        for row in db.execute(
            select(JobPosting.job_type, func.count(JobPosting.id))
            .where(*conditions)
            .group_by(JobPosting.job_type)
        ).all()
    }

    groups: list[JobTypeSkillGroup] = []
    for job_type, skills in by_type.items():
        group_total = int(type_totals.get(job_type, 0))
        ranked_skills = sorted(skills, key=lambda item: (-item[1], item[0].casefold()))
        groups.append(
            JobTypeSkillGroup(
                job_type=job_type,
                total_jobs=group_total,
                skills=[
                    SkillItem(
                        skill=skill,
                        category=categorize_skill(skill),
                        count=count,
                        ratio=_ratio(count, group_total),
                    )
                    for skill, count in ranked_skills[:per_type_limit]
                ],
            )
        )
    groups.sort(key=lambda item: item.total_jobs, reverse=True)

    # Category coverage counts distinct jobs, not skill tags: a job that lists
    # three databases still counts once under 数据库. Categories overlap, so
    # their counts must not be added up to the total number of jobs.
    category_jobs: dict[str, set[str]] = {}
    pair_rows = db.execute(
        select(JobSkill.job_id, JobSkill.skill_name)
        .select_from(JobSkill)
        .join(JobPosting, JobPosting.id == JobSkill.job_id)
        .where(*conditions)
        .distinct()
    ).all()
    for job_id, skill_name in pair_rows:
        category_jobs.setdefault(categorize_skill(skill_name), set()).add(job_id)

    categories = [
        SkillCategoryItem(
            category=category,
            count=len(job_ids),
            ratio=_ratio(len(job_ids), total_jobs),
        )
        for category, job_ids in sorted(
            category_jobs.items(), key=lambda item: (-len(item[1]), item[0])
        )
    ]

    return SkillsStatsOut(
        total_jobs=total_jobs,
        total_skills=int(total_skills),
        items=items,
        categories=categories,
        by_job_type=groups,
    )


def get_salary_stats(db: Session, **filters: Any) -> SalaryStatsOut:
    frame = _load_jobs_frame(db, **filters)
    overall = _salary_summary(frame["salary_mid"])
    return SalaryStatsOut(
        total_jobs=len(frame),
        salary_available=overall.count,
        overall=overall,
        distribution=_salary_distribution(frame),
        by_job_type=_salary_groups(frame, "job_type"),
        by_education=_salary_groups(frame, "education"),
        by_experience=_salary_groups(frame, "experience"),
    )


__all__ = [
    "EDUCATION_ORDER",
    "EXPERIENCE_ORDER",
    "SALARY_BINS",
    "get_education_stats",
    "get_experience_stats",
    "get_overview",
    "get_salary_stats",
    "get_skills_stats",
]
