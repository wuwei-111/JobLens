"""Database-level quality summary.

The offline preflight checks a candidate JSON file; this module checks what is
actually stored in SQLite. Both share the same canonical vocabulary so the
data-notes page and the delivery report can cite one set of definitions.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import JobPosting, JobSkill
from app.schemas.quality import QualityStatsOut, ValueCount
from app.services.validation import (
    CANONICAL_EDUCATION,
    CANONICAL_EXPERIENCE,
    SALARY_HIGH,
    SALARY_LOW,
)


def _count_where(db: Session, *conditions) -> int:
    return int(
        db.scalar(select(func.count(JobPosting.id)).where(*conditions)) or 0
    )


def _value_counts(db: Session, column, canonical: set[str]) -> list[ValueCount]:
    rows = db.execute(
        select(column, func.count(JobPosting.id))
        .group_by(column)
        .order_by(func.count(JobPosting.id).desc())
    ).all()
    return [
        ValueCount(value=str(value), count=int(count))
        for value, count in rows
        if value not in canonical
    ]


def get_quality_stats(db: Session) -> QualityStatsOut:
    total_jobs = int(
        db.scalar(select(func.count(JobPosting.id))) or 0
    )
    salary_missing = _count_where(
        db,
        JobPosting.salary_min.is_(None),
        JobPosting.salary_max.is_(None),
    )
    salary_single_bound = _count_where(
        db,
        (
            JobPosting.salary_min.is_(None)
            & JobPosting.salary_max.is_not(None)
        )
        | (
            JobPosting.salary_min.is_not(None)
            & JobPosting.salary_max.is_(None)
        ),
    )
    salary_invalid_range = _count_where(
        db,
        JobPosting.salary_min.is_not(None),
        JobPosting.salary_max.is_not(None),
        JobPosting.salary_min > JobPosting.salary_max,
    )
    salary_outliers = _count_where(
        db,
        (JobPosting.salary_min < SALARY_LOW)
        | (JobPosting.salary_min > SALARY_HIGH)
        | (JobPosting.salary_max < SALARY_LOW)
        | (JobPosting.salary_max > SALARY_HIGH),
    )

    unknown_education = _value_counts(db, JobPosting.education, CANONICAL_EDUCATION)
    unknown_experience = _value_counts(
        db, JobPosting.experience, CANONICAL_EXPERIENCE
    )

    jobs_without_skills = int(
        db.scalar(
            select(func.count(JobPosting.id))
            .outerjoin(JobSkill, JobSkill.job_id == JobPosting.id)
            .where(JobSkill.id.is_(None))
        )
        or 0
    )

    # The same posting may legitimately appear in several city datasets (a
    # multi-city campus posting). Only flag duplicates within the same city.
    duplicate_url_rows = db.execute(
        select(JobPosting.source_url, func.count(JobPosting.id))
        .where(JobPosting.source_url != "")
        .group_by(JobPosting.source_url, JobPosting.city)
        .having(func.count(JobPosting.id) > 1)
    ).all()
    duplicate_counts: dict[str, int] = {}
    for url, count in duplicate_url_rows:
        key = str(url)
        duplicate_counts[key] = max(duplicate_counts.get(key, 0), int(count))
    duplicate_source_urls = [
        ValueCount(value=url, count=count)
        for url, count in sorted(
            duplicate_counts.items(), key=lambda item: (-item[1], item[0])
        )[:20]
    ]

    demo_records = int(
        db.scalar(
            select(func.count(JobPosting.id)).where(
                JobPosting.source.contains("演示")
                | JobPosting.source.contains("虚构")
                | JobPosting.source_url.contains("example.com")
            )
        )
        or 0
    )

    total_companies = int(
        db.scalar(select(func.count(func.distinct(JobPosting.company)))) or 0
    )
    total_cities = int(
        db.scalar(select(func.count(func.distinct(JobPosting.city)))) or 0
    )
    sources = [
        str(value)
        for value in db.scalars(
            select(JobPosting.source)
            .where(JobPosting.source != "")
            .distinct()
            .order_by(JobPosting.source)
        ).all()
    ]
    collected_from = db.scalar(select(func.min(JobPosting.collected_at)))
    collected_to = db.scalar(select(func.max(JobPosting.collected_at)))

    warnings: list[str] = []
    salary_available = total_jobs - salary_missing
    if salary_missing:
        warnings.append(f"薪资面议（两端为空）：{salary_missing} 条")
    if salary_single_bound:
        warnings.append(f"只有单边薪资：{salary_single_bound} 条")
    if salary_invalid_range:
        warnings.append(f"薪资下限大于上限：{salary_invalid_range} 条")
    if salary_outliers:
        warnings.append(
            f"薪资疑似异常（<{SALARY_LOW} 或 >{SALARY_HIGH}）：{salary_outliers} 条"
        )
    if unknown_education:
        warnings.append(
            f"未知学历值：{len(unknown_education)} 个取值 / "
            f"{sum(item.count for item in unknown_education)} 条，需人工复核"
        )
    if unknown_experience:
        warnings.append(
            f"未知经验值：{len(unknown_experience)} 个取值 / "
            f"{sum(item.count for item in unknown_experience)} 条，"
            "多为未归一的 JD 原文摘句，需人工复核"
        )
    if jobs_without_skills:
        warnings.append(f"没有任何技能标签的岗位：{jobs_without_skills} 条")
    if duplicate_source_urls:
        warnings.append(
            f"同一城市内来源链接重复：{len(duplicate_source_urls)} 个链接"
        )
    if demo_records:
        warnings.append(
            f"演示/虚构记录 {demo_records} 条；这些数据不能用于新闻结论"
        )

    return QualityStatsOut(
        total_jobs=total_jobs,
        salary_available=salary_available,
        salary_missing=salary_missing,
        salary_single_bound=salary_single_bound,
        salary_invalid_range=salary_invalid_range,
        salary_outliers=salary_outliers,
        unknown_education=unknown_education,
        unknown_experience=unknown_experience,
        jobs_without_skills=jobs_without_skills,
        duplicate_source_urls=duplicate_source_urls,
        demo_records=demo_records,
        total_companies=total_companies,
        total_cities=total_cities,
        sources=sources,
        collected_from=collected_from,
        collected_to=collected_to,
        warnings=warnings,
    )


__all__ = ["get_quality_stats"]
