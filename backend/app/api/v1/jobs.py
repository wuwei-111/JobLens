"""Job posting query endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models import JobPosting
from app.schemas.error import ErrorResponse
from app.schemas.job import JobListResponse, JobOut
from app.services.filters import build_job_conditions

router = APIRouter()


def _to_job_out(job: JobPosting) -> JobOut:
    return JobOut(
        id=job.id,
        company=job.company,
        position=job.position,
        job_type=job.job_type,
        city=job.city,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        education=job.education,
        experience=job.experience,
        is_fresh_graduate=job.is_fresh_graduate,
        description=job.description,
        source=job.source,
        source_url=job.source_url,
        collected_at=job.collected_at,
        skills=[skill.skill_name for skill in job.skills],
    )


@router.get("", response_model=JobListResponse, summary="分页查询招聘岗位")
def list_jobs(
    job_type: str | None = Query(None, description="岗位类别"),
    education: str | None = Query(None, description="学历要求"),
    experience: str | None = Query(None, description="经验要求"),
    city: str | None = Query(None, description="城市"),
    skill: str | None = Query(None, description="技能名称（精确匹配）"),
    salary_min: int | None = Query(None, ge=0, description="期望月薪下限"),
    salary_max: int | None = Query(None, ge=0, description="期望月薪上限"),
    q: str | None = Query(None, description="按岗位名称或企业名称关键词搜索"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> JobListResponse:
    conditions = build_job_conditions(
        job_type=job_type,
        education=education,
        experience=experience,
        city=city,
        skill=skill,
        salary_min=salary_min,
        salary_max=salary_max,
        q=q,
    )

    total = db.scalar(
        select(func.count()).select_from(JobPosting).where(*conditions)
    ) or 0

    stmt = (
        select(JobPosting)
        .where(*conditions)
        .options(selectinload(JobPosting.skills))
        .order_by(JobPosting.collected_at.desc(), JobPosting.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    jobs = db.scalars(stmt).all()

    return JobListResponse(
        total=int(total),
        page=page,
        page_size=page_size,
        items=[_to_job_out(job) for job in jobs],
    )


@router.get(
    "/{job_id}",
    response_model=JobOut,
    summary="查询单个招聘岗位",
    responses={404: {"model": ErrorResponse, "description": "岗位不存在"}},
)
def get_job(job_id: str, db: Session = Depends(get_db)) -> JobOut:
    job = db.get(JobPosting, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="招聘记录不存在")
    return _to_job_out(job)
