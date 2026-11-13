"""Shared SQL filter construction for job queries and statistics."""

from __future__ import annotations

from sqlalchemy import ColumnElement, or_

from app.models import JobPosting


def build_job_conditions(
    *,
    job_type: str | None = None,
    education: str | None = None,
    experience: str | None = None,
    city: str | None = None,
    salary_min: int | None = None,
    salary_max: int | None = None,
    q: str | None = None,
) -> list[ColumnElement[bool]]:
    """Return SQLAlchemy conditions for the shared job filters.

    Salary overlap semantics: a job matches when its salary range intersects
    the requested range. Jobs with unknown salary never match a salary filter.
    """
    conditions: list[ColumnElement[bool]] = []

    if job_type:
        conditions.append(JobPosting.job_type == job_type)
    if education:
        conditions.append(JobPosting.education == education)
    if experience:
        conditions.append(JobPosting.experience == experience)
    if city:
        conditions.append(JobPosting.city == city)
    if salary_min is not None:
        conditions.append(JobPosting.salary_max.is_not(None))
        conditions.append(JobPosting.salary_max >= salary_min)
    if salary_max is not None:
        conditions.append(JobPosting.salary_min.is_not(None))
        conditions.append(JobPosting.salary_min <= salary_max)
    if q:
        keyword = f"%{q.strip()}%"
        if q.strip():
            conditions.append(
                or_(
                    JobPosting.position.ilike(keyword),
                    JobPosting.company.ilike(keyword),
                )
            )

    return conditions


__all__ = ["build_job_conditions"]
