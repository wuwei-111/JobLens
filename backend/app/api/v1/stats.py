"""Statistics endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import StatsFilters, get_stats_filters
from app.db.session import get_db
from app.schemas.quality import QualityStatsOut
from app.schemas.stats import (
    CrossDimension,
    CrossStatsOut,
    EducationStatsOut,
    ExperienceStatsOut,
    OverviewOut,
    SalaryStatsOut,
    SkillsStatsOut,
)
from app.services import stats as stats_service
from app.services.quality import get_quality_stats

router = APIRouter()


@router.get("/overview", response_model=OverviewOut, summary="数据总览")
def overview(db: Session = Depends(get_db)) -> OverviewOut:
    return stats_service.get_overview(db)


@router.get("/quality", response_model=QualityStatsOut, summary="数据质量摘要")
def quality_stats(db: Session = Depends(get_db)) -> QualityStatsOut:
    return get_quality_stats(db)


@router.get(
    "/cross",
    response_model=CrossStatsOut,
    summary="交叉统计",
    description=(
        "按一个维度分组，统计另一个维度的分布。可用维度："
        "job_type / education / experience / city；共用学历、经验、岗位类别、城市筛选。"
    ),
)
def cross_stats(
    row: CrossDimension = Query(..., description="行维度"),
    column: CrossDimension = Query(..., description="列维度"),
    filters: StatsFilters = Depends(get_stats_filters),
    db: Session = Depends(get_db),
) -> CrossStatsOut:
    return stats_service.get_cross_stats(
        db, row=row, column=column, **filters.model_dump()
    )


@router.get("/education", response_model=EducationStatsOut, summary="学历要求统计")
def education_stats(
    filters: StatsFilters = Depends(get_stats_filters),
    db: Session = Depends(get_db),
) -> EducationStatsOut:
    return stats_service.get_education_stats(db, **filters.model_dump())


@router.get("/experience", response_model=ExperienceStatsOut, summary="经验要求统计")
def experience_stats(
    filters: StatsFilters = Depends(get_stats_filters),
    db: Session = Depends(get_db),
) -> ExperienceStatsOut:
    return stats_service.get_experience_stats(db, **filters.model_dump())


@router.get("/skills", response_model=SkillsStatsOut, summary="技能需求统计")
def skills_stats(
    filters: StatsFilters = Depends(get_stats_filters),
    limit: int = Query(20, ge=1, le=100, description="总体排行榜返回的技能数"),
    per_type_limit: int = Query(8, ge=1, le=50, description="每个岗位类别返回的技能数"),
    db: Session = Depends(get_db),
) -> SkillsStatsOut:
    return stats_service.get_skills_stats(
        db,
        limit=limit,
        per_type_limit=per_type_limit,
        **filters.model_dump(),
    )


@router.get("/salary", response_model=SalaryStatsOut, summary="薪资统计")
def salary_stats(
    filters: StatsFilters = Depends(get_stats_filters),
    db: Session = Depends(get_db),
) -> SalaryStatsOut:
    return stats_service.get_salary_stats(db, **filters.model_dump())
