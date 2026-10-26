"""Aegis sample API: the first workload for our delivery platform."""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Aegis Sample API", version="0.2.0")


class HealthResponse(BaseModel):
    status: Literal["ok"]


class VersionResponse(BaseModel):
    version: str


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Report process health; no external dependencies exist in Phase 1."""
    return HealthResponse(status="ok")


@app.get("/version", response_model=VersionResponse)
async def version() -> VersionResponse:
    """Identify the application version served by this running instance."""
    return VersionResponse(version=app.version)
