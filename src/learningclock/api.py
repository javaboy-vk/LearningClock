# =============================================================================
# File Name : api.py
# Artifact  : LearningClock - HTTP API
# Author    : javaboy-vk
# Date      : 2026-08-25
# Version   : v0.1.0
# Purpose:
#   Exposes the LearningClock HTTP contract and automatic OpenAPI documentation.
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


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Check API readiness",
    operation_id="get_health",
)
def health() -> HealthResponse:
    """Return the API readiness state and current LearningClock version."""

    return HealthResponse(status="ready", version=__version__)
