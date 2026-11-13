"""Uniform error responses.

The frontend already reads FastAPI's ``detail`` field, so the envelope keeps it
and adds a stable machine-readable ``code``. Request-validation errors also
expose the original field errors under ``errors``.
"""

from __future__ import annotations

from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

STATUS_CODES: dict[int, str] = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    413: "payload_too_large",
    422: "validation_error",
    500: "internal_error",
    503: "service_unavailable",
}


async def http_exception_handler(
    _request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": jsonable_encoder(exc.detail),
            "code": STATUS_CODES.get(exc.status_code, "http_error"),
        },
        headers=exc.headers,
    )


async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "detail": "请求参数校验失败",
            "code": "validation_error",
            "errors": jsonable_encoder(exc.errors()),
        },
    )


__all__ = [
    "STATUS_CODES",
    "http_exception_handler",
    "validation_exception_handler",
]
