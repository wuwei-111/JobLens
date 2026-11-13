"""Metadata used to build frontend filters."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import JobPosting, JobSkill
from app.schemas.job import FilterMeta
from app.services.stats import EDUCATION_ORDER, EXPERIENCE_ORDER

router = APIRouter()


def _sort_by_order(values: list[str], order: list[str]) -> list[str]:
    position = {name: index for index, name in enumerate(order)}
    return sorted(values, key=lambda value: (position.get(value, len(order)), value))


@router.get("/filters", response_model=FilterMeta, summary="筛选项元数据")
def filter_meta(db: Session = Depends(get_db)) -> FilterMeta:
    job_types = [
        name
        for name in db.scalars(
            select(JobPosting.job_type)
            .group_by(JobPosting.job_type)
            .order_by(func.count(JobPosting.id).desc(), JobPosting.job_type)
        ).all()
        if name
    ]
    educations = [
        name
        for name in db.scalars(select(JobPosting.education).distinct()).all()
        if name
    ]
    experiences = [
        name
        for name in db.scalars(select(JobPosting.experience).distinct()).all()
        if name
    ]
    cities = [
        name
        for name in db.scalars(
            select(JobPosting.city)
            .group_by(JobPosting.city)
            .order_by(func.count(JobPosting.id).desc(), JobPosting.city)
        ).all()
        if name
    ]
    skills = [
        name
        for name in db.scalars(
            select(JobSkill.skill_name)
            .group_by(JobSkill.skill_name)
            .order_by(func.count(JobSkill.job_id).desc(), JobSkill.skill_name)
            .limit(300)
        ).all()
        if name
    ]

    return FilterMeta(
        job_types=job_types,
        educations=_sort_by_order(educations, EDUCATION_ORDER),
        experiences=_sort_by_order(experiences, EXPERIENCE_ORDER),
        cities=cities,
        skills=skills,
    )
