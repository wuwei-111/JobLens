"""Schemas for JSON dataset import."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

OnConflict = Literal["skip", "update", "fail"]


class ImportErrorItem(BaseModel):
    """A record that could not be imported."""

    row: int = Field(description="记录在 JSON records 数组中的序号，从 1 开始")
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
