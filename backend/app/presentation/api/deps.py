"""Dependency Injection برای FastAPI."""

from typing import Annotated

from fastapi import Depends, Request

from app.domain.ports.exchange import ExchangePort


def get_exchange(request: Request) -> ExchangePort:
    """Exchange را از state اپ برمی‌گرداند (در lifespan ست شده)."""
    return request.app.state.exchange


ExchangeDep = Annotated[ExchangePort, Depends(get_exchange)]
