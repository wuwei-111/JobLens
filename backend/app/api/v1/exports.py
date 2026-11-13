"""CSV exports for reports and offline checking."""

from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models import JobPosting
from app.schemas.error import ErrorResponse
from app.services.filters import build_job_conditions

router = APIRouter()

CSV_COLUMNS = [
    "id",
    "company",
    "position",
    "job_type",
    "city",
    "salary_min",
    "salary_max",
    "education",
    "experience",
    "is_fresh_graduate",
    "skills",
    "source",
    "source_url",
    "collected_at",
]


@router.get(
    "/jobs.csv",
    summary="导出岗位 CSV",
    description=(
        "按与 /jobs 相同的筛选条件导出全部匹配岗位。文件带 UTF-8 BOM，"
        "可直接用 Excel 打开；技能用分号分隔。"
    ),
    responses={422: {"model": ErrorResponse, "description": "查询参数校验失败"}},
)
def export_jobs_csv(
    job_type: str | None = Query(None, description="岗位类别"),
    education: str | None = Query(None, description="学历要求"),
    experience: str | None = Query(None, description="经验要求"),
    city: str | None = Query(None, description="城市"),
    skill: str | None = Query(None, description="技能名称（精确匹配）"),
    salary_min: int | None = Query(None, ge=0, description="期望月薪下限"),
    salary_max: int | None = Query(None, ge=0, description="期望月薪上限"),
    q: str | None = Query(None, description="按岗位名称或企业名称关键词搜索"),
    db: Session = Depends(get_db),
) -> Response:
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
    jobs = db.scalars(
        select(JobPosting)
        .where(*conditions)
        .options(selectinload(JobPosting.skills))
        .order_by(JobPosting.collected_at.desc(), JobPosting.id)
    ).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_COLUMNS)
    for job in jobs:
        writer.writerow(
            [
                job.id,
                job.company,
                job.position,
                job.job_type,
                job.city,
                job.salary_min if job.salary_min is not None else "",
                job.salary_max if job.salary_max is not None else "",
                job.education,
                job.experience,
                "是" if job.is_fresh_graduate else "否",
                "; ".join(skill.skill_name for skill in job.skills),
                job.source,
                job.source_url,
                job.collected_at.isoformat() if job.collected_at else "",
            ]
        )

    # UTF-8 BOM keeps Excel from misreading Chinese headers.
    content = "﻿" + buffer.getvalue()
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="joblens_jobs.csv"',
        },
    )
