"""تبدیل ارورهای دامنه به پاسخ RFC-7807."""

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.domain.exceptions import (
    DomainError,
    ExchangeAuthError,
    ExchangeRateLimitError,
    ExchangeUnavailableError,
    InvalidSymbolError,
)

log = structlog.get_logger("http")


_STATUS_MAP = {
    ExchangeAuthError: 401,
    ExchangeRateLimitError: 429,
    ExchangeUnavailableError: 503,
    InvalidSymbolError: 404,
}


def _problem(*, status: int, code: str, detail: str, title: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "type": f"https://wallex.local/errors/{code}",
            "title": title,
            "status": status,
            "detail": detail,
            "code": code,
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle_domain(_: Request, exc: DomainError) -> JSONResponse:
        status = 400
        for cls, s in _STATUS_MAP.items():
            if isinstance(exc, cls):
                status = s
                break
        log.warning("domain_error", code=exc.code, detail=exc.message)
        return _problem(
            status=status,
            code=exc.code,
            detail=exc.message,
            title=exc.__class__.__name__,
        )
