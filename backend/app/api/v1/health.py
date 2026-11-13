"""Health check endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core import settings
from app.db.session import get_db

router = APIRouter()


class HealthOut(BaseModel):
    status: str
    database: str
    version: str


@router.get("/health", response_model=HealthOut, summary="健康检查")
def health(db: Session = Depends(get_db)) -> HealthOut:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:  # pragma: no cover - requires broken DB
        raise HTTPException(status_code=503, detail="数据库不可用") from exc
    return HealthOut(status="ok", database="ok", version=settings.app_version)
