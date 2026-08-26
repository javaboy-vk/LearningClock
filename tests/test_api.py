# =============================================================================
# File Name : test_api.py
# Artifact  : LearningClock - HTTP API Tests
# Author    : javaboy-vk
# Date      : 2026-08-25
# Version   : v0.1.0
# Purpose:
#   Verifies readiness, Swagger UI, ReDoc, and the generated OpenAPI contract.
# =============================================================================

import asyncio
import json
from pathlib import Path

from learningclock import __version__
from learningclock.api import app


def asgi_get(path: str) -> tuple[int, bytes]:
    """Send one dependency-free GET request directly through the ASGI contract."""

    messages = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
        "root_path": "",
        "headers": [(b"host", b"testserver")],
        "client": ("127.0.0.1", 50000),
        "server": ("testserver", 80),
        "state": {},
    }
    asyncio.run(app(scope, receive, send))
    response_start = next(message for message in messages if message["type"] == "http.response.start")
    body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )
    return response_start["status"], body


def test_health_reports_ready_and_current_version():

    status, body = asgi_get("/health")

    assert status == 200
    assert json.loads(body) == {"status": "ready", "version": __version__}


def test_openapi_schema_describes_the_health_contract():

    status, body = asgi_get("/openapi.json")

    assert status == 200
    schema = json.loads(body)
    assert schema["info"]["title"] == "LearningClock API"
    assert schema["info"]["version"] == __version__
    assert schema["paths"]["/health"]["get"]["operationId"] == "get_health"


def test_interactive_api_documentation_is_available():

    swagger_status, swagger_body = asgi_get("/docs")
    redoc_status, redoc_body = asgi_get("/redoc")

    assert swagger_status == 200
    assert b"Swagger UI" in swagger_body
    assert redoc_status == 200
    assert b"ReDoc" in redoc_body


def test_tracked_openapi_schema_matches_the_application():

    schema_path = Path(__file__).resolve().parents[1] / "docs" / "openapi.json"

    assert json.loads(schema_path.read_text(encoding="utf-8")) == app.openapi()
