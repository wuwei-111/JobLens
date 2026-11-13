"""Dataset import, preflight validation and batch history endpoints."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import settings
from app.db.session import get_db
from app.models import ImportBatch, JobPosting
from app.schemas.error import ErrorResponse
from app.schemas.import_ import (
    ImportBatchOut,
    ImportResult,
    OnConflict,
    ValidationReport,
)
from app.services.importer import import_dataset
from app.services.validation import validate_dataset

router = APIRouter()


async def _read_json_upload(file: UploadFile) -> Any:
    """Shared upload checks for import and preflight."""
    if file.filename and not file.filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="仅支持 .json 文件")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="文件为空")
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"文件超过大小上限（{settings.max_upload_bytes} 字节）",
        )

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="文件必须是 UTF-8 编码") from exc

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"JSON 解析失败：第 {exc.lineno} 行第 {exc.colno} 列 — {exc.msg}",
        ) from exc


@router.post(
    "/validate",
    response_model=ValidationReport,
    summary="预检 JSON 数据集（不入库）",
    description=(
        "执行与导入相同的字段校验、枚举检查、薪资与技能质量检查，并报告已有 id "
        "数量；不会写入 SQLite。适合正式导入前先跑一遍。"
    ),
    responses={
        400: {"model": ErrorResponse, "description": "文件格式、编码或 JSON 结构错误"},
        413: {"model": ErrorResponse, "description": "文件超过上传上限"},
        422: {"model": ErrorResponse, "description": "请求参数校验失败"},
    },
)
async def validate_json(
    file: UploadFile = File(..., description="JSON 数据集文件"),
    db: Session = Depends(get_db),
) -> ValidationReport:
    payload = await _read_json_upload(file)
    existing_ids = set(db.scalars(select(JobPosting.id)).all())
    try:
        return validate_dataset(payload, existing_ids=existing_ids)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/json",
    response_model=ImportResult,
    summary="导入 JSON 招聘数据集",
    description=(
        "上传格式见 docs/data-dictionary.md。重复 id 默认跳过，可用 on_conflict "
        "选择 skip/update/fail。单次上传上限由 JOBLENS_MAX_UPLOAD_BYTES 控制。"
    ),
    responses={
        400: {"model": ErrorResponse, "description": "文件格式、编码或 JSON 结构错误"},
        413: {"model": ErrorResponse, "description": "文件超过上传上限"},
        422: {"model": ErrorResponse, "description": "请求参数校验失败"},
    },
)
async def import_json(
    file: UploadFile = File(..., description="JSON 数据集文件"),
    on_conflict: OnConflict = Query(
        "skip", description="重复 id 的处理方式：skip / update / fail"
    ),
    db: Session = Depends(get_db),
) -> ImportResult:
    payload = await _read_json_upload(file)
    try:
        return import_dataset(
            db,
            payload,
            on_conflict=on_conflict,
            source_file=file.filename,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/batches",
    response_model=list[ImportBatchOut],
    summary="最近导入批次",
    description="按时间倒序返回导入批次摘要，用于复现与交付材料。",
)
def list_batches(
    limit: int = Query(20, ge=1, le=100, description="返回条数"),
    db: Session = Depends(get_db),
) -> list[ImportBatch]:
    return list(
        db.scalars(
            select(ImportBatch)
            .order_by(ImportBatch.created_at.desc(), ImportBatch.id.desc())
            .limit(limit)
        ).all()
    )
