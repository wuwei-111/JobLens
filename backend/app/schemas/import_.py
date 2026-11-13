"""Schemas for JSON dataset import and preflight validation."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.quality import ValueCount

OnConflict = Literal["skip", "update", "fail"]


class ImportErrorItem(BaseModel):
    """A record that could not be imported, or a dataset warning."""

    row: int | None = Field(
        default=None,
        description="记录在 JSON records 数组中的序号，从 1 开始；汇总警告为空",
    )
    record_id: str | None = None
    message: str


class ImportResult(BaseModel):
    dataset_name: str = ""
    source_file: str | None = None
    total_records: int
    imported: int
    updated: int
    skipped: int
    failed: int
    errors: list[ImportErrorItem] = Field(default_factory=list)
    batch_id: int | None = Field(
        default=None, description="本次导入写入 import_batches 的批次 id"
    )


class ImportBatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dataset_name: str
    source_file: str | None
    on_conflict: str
    total_records: int
    imported: int
    updated: int
    skipped: int
    failed: int
    created_at: datetime


class ValidationReport(BaseModel):
    """Read-only preflight result for one JSON dataset."""

    dataset_name: str = ""
    total_records: int
    valid_records: int
    invalid_records: int
    duplicate_ids: int = 0
    existing_in_database: int = Field(
        default=0, description="id 已存在于数据库、导入时将按冲突策略处理的记录数"
    )
    missing_fields: dict[str, int] = Field(default_factory=dict)
    salary_missing: int = 0
    salary_single_bound: int = 0
    salary_outliers: int = 0
    unknown_education: list[ValueCount] = Field(default_factory=list)
    unknown_experience: list[ValueCount] = Field(default_factory=list)
    empty_skills: int = 0
    over_limit_skills: int = Field(
        default=0, description="技能数超过 10 项的记录数（数据规范上限）"
    )
    duplicate_skill_entries: int = 0
    duplicate_source_urls: list[ValueCount] = Field(default_factory=list)
    demo_records: int = 0
    errors: list[ImportErrorItem] = Field(default_factory=list)
    warnings: list[ImportErrorItem] = Field(default_factory=list)
    warning_count: int = Field(default=0, description="警告总数（warnings 可能被截断）")
