"""Uniform error envelope used by the API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class ErrorResponse(BaseModel):
    """Every handled API error keeps FastAPI's ``detail`` field and adds a code.

    ``errors`` is present for request-validation failures, where FastAPI
    normally returns a list of field-level errors.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "detail": "招聘记录不存在",
                    "code": "not_found",
                },
                {
                    "detail": "请求参数校验失败",
                    "code": "validation_error",
                    "errors": [{"loc": ["query", "page"], "msg": "Input should be >= 1"}],
                },
            ]
        }
    )

    detail: str | list[Any] | dict[str, Any]
    code: str
    errors: list[Any] | None = None
