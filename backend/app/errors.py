"""Uniform error handling.

Every error the API returns has the same shape (spec §7):

    {"error": {"code": "SOME_CODE", "message": "Human readable text", "details": {}}}

Route and service code raises `AppError`; the handlers below turn it into that JSON.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("medbridge.errors")


class AppError(Exception):
    """An expected, user-facing error with a stable machine-readable code."""

    def __init__(
        self,
        code: str,
        status_code: int,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.message = message
        self.details = details or {}


def error_body(code: str, message: str, details: dict[str, Any] | None = None) -> dict:
    """Build the uniform error envelope."""
    return {"error": {"code": code, "message": message, "details": details or {}}}


async def _app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code, content=error_body(exc.code, exc.message, exc.details)
    )


async def _validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Wrap FastAPI/Pydantic validation errors in our envelope.

    Special case: a missing `file` field on the upload endpoint becomes 400 NO_FILE,
    as the API contract (§7.1) requires.
    """
    errors = exc.errors()
    for err in errors:
        loc = err.get("loc", ())
        if err.get("type") == "missing" and "file" in loc:
            return JSONResponse(
                status_code=400,
                content=error_body("NO_FILE", "Please choose a PDF file to upload."),
            )

    # Only return field locations and messages, never the submitted values
    # (they could contain report data).
    simplified = [
        {"field": ".".join(str(p) for p in e.get("loc", ())), "message": e.get("msg", "")}
        for e in errors
    ]
    return JSONResponse(
        status_code=422,
        content=error_body(
            "VALIDATION_ERROR",
            "Some of the information sent was not valid.",
            {"errors": simplified},
        ),
    )


async def _http_error_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Framework errors such as 404 (unknown URL) or 405 (wrong method)."""
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(f"HTTP_{exc.status_code}", str(exc.detail)),
    )


async def _unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    # The stack trace goes to the server log only, never to the client.
    logger.exception("Unhandled error: %s", type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content=error_body("INTERNAL_ERROR", "Something went wrong on our side. Please try again."),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _app_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, _http_error_handler)
    app.add_exception_handler(Exception, _unhandled_error_handler)
