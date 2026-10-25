"""Aegis sample API: the first workload for our delivery platform."""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Aegis Sample API", version="0.1.0")


class HealthResponse(BaseModel):
    status: Literal["ok"]


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Report process health; no external dependencies exist in Phase 1."""
    return HealthResponse(status="ok")
