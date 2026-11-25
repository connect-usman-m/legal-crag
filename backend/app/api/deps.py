from dataclasses import dataclass
from typing import Any

from fastapi import Header, HTTPException, Request

from app.core.config import Settings


@dataclass
class Runtime:
    settings: Settings
    graph: Any = None
    embedder: Any = None
    reranker: Any = None
    chroma: Any = None
    faiss: Any = None


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_runtime(request: Request) -> Runtime:
    return request.app.state.runtime


def require_demo_key(
    request: Request,
    x_api_key: str | None = Header(default=None),
) -> None:
    settings = request.app.state.settings
    if settings.demo_api_key and x_api_key != settings.demo_api_key:
        raise HTTPException(status_code=401, detail="Demo key missing or invalid")
