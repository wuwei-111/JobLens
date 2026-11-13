"""Dataset import endpoints."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.core import settings
from app.db.session import get_db
from app.schemas.import_ import ImportResult, OnConflict
from app.services.importer import import_dataset

router = APIRouter()


@router.post(
    "/json",
    response_model=ImportResult,
    summary="导入 JSON 招聘数据集",
    description=(
        "上传格式见 docs/data-dictionary.md。重复 id 默认跳过，可用 on_conflict "
        "选择 skip/update/fail。单次上传上限由 JOBLENS_MAX_UPLOAD_BYTES 控制。"
    ),
)
async def import_json(
    file: UploadFile = File(..., description="JSON 数据集文件"),
    on_conflict: OnConflict = Query(
        "skip", description="重复 id 的处理方式：skip / update / fail"
    ),
    db: Session = Depends(get_db),
) -> ImportResult:
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
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"JSON 解析失败：第 {exc.lineno} 行第 {exc.colno} 列 — {exc.msg}",
        ) from exc

    try:
        return import_dataset(
            db,
            payload,
            on_conflict=on_conflict,
            source_file=file.filename,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
