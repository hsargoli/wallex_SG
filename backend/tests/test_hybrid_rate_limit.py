"""Test that hybrid rate limit (user:ip) is actually applied."""
import pytest
from fastapi import Request
from app.core.rate_limit import get_user_and_ip


def test_get_user_and_ip_with_valid_jwt():
    from app.core.auth import create_user_token
    token = create_user_token("user-123", "a@b.com")
    
    scope = {
        "type": "http",
        "headers": [(b"authorization", f"Bearer {token}".encode())],
        "client": ("127.0.0.1", 1234),
    }
    req = Request(scope)
    key = get_user_and_ip(req)
    assert key.startswith("user-123:")
    assert key.endswith("127.0.0.1")


def test_get_user_and_ip_without_jwt():
    scope = {
        "type": "http",
        "headers": [],
        "client": ("127.0.0.1", 1234),
    }
    req = Request(scope)
    key = get_user_and_ip(req)
    assert key == "anon:127.0.0.1"


def test_get_user_and_ip_with_invalid_jwt():
    scope = {
        "type": "http",
        "headers": [(b"authorization", b"Bearer invalid.token.here")],
        "client": ("127.0.0.1", 1234),
    }
    req = Request(scope)
    key = get_user_and_ip(req)
    assert key == "anon:127.0.0.1"
