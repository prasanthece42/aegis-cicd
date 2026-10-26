"""Aegis sample API: the first workload for our delivery platform."""

from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Aegis Sample API", version="0.3.0")
static_directory = Path(__file__).resolve().parent / "static"
app.mount("/assets", StaticFiles(directory=static_directory), name="assets")


class HealthResponse(BaseModel):
    status: Literal["ok"]


class VersionResponse(BaseModel):
    version: str


@app.get("/", response_class=FileResponse, include_in_schema=False)
async def home() -> FileResponse:
    """Serve the test UI from the same application image as the API."""
    return FileResponse(static_directory / "index.html", headers={"Cache-Control": "no-cache"})


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Report process health; no external dependencies exist in Phase 1."""
    return HealthResponse(status="ok")


@app.get("/version", response_model=VersionResponse)
async def version() -> VersionResponse:
    """Identify the application version served by this running instance."""
    return VersionResponse(version=app.version)
