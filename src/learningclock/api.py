# =============================================================================
# File Name : api.py
# Artifact  : LearningClock - HTTP API
# Author    : javaboy-vk
# Date      : 2026-08-25
# Version   : v0.1.1
# Purpose:
#   Exposes the LearningClock HTTP contract and automatic OpenAPI documentation.
#
# HTTP contract:
#   GET /health returns a typed HealthResponse with readiness and the package
#   version. FastAPI derives /openapi.json, /docs, and /redoc from the same app
#   object; scripts/export_openapi.py persists that runtime schema for review.
#
# Boundary contract:
#   The API is a readiness and integration surface. It does not start the
#   Tkinter UI, discover clock configurations, mutate CSV data, or control a
#   running LearningClock process.
# =============================================================================

from __future__ import annotations

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from learningclock import __version__


class HealthResponse(BaseModel):
    """Readiness response returned by the LearningClock API."""

    status: Literal["ready"]
    version: str


app = FastAPI(
    title="LearningClock API",
    version=__version__,
    description="HTTP API for LearningClock runtime and integration checks.",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)


# Source documentation: Returns readiness and version metadata for health checks and API clients.
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Check API readiness",
    description="Return the API readiness state and current LearningClock version.",
    operation_id="get_health",
)
def health() -> HealthResponse:
    return HealthResponse(status="ready", version=__version__)
