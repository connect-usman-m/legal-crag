import logging
from contextlib import asynccontextmanager
from typing import Any, cast
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.deps import Runtime
from app.api.routes_meta import router as meta_router
from app.api.routes_query import compare_router, query_router
from app.core.config import Settings
from app.schemas.api import ErrorResponse

logger = logging.getLogger("lexgate")


def create_app(settings: Settings | None = None, runtime: Runtime | None = None) -> FastAPI:
    config = settings or Settings()
    active = runtime or Runtime(config)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        from app.graph.builder import build_graph
        from app.retrieval.embedder import get_model
        from app.retrieval.reranker import get_cross_encoder

        active.graph = build_graph(config)
        active.embedder = get_model(config.embed_model)
        active.reranker = get_cross_encoder(config.rerank_model)
        app.state.runtime = active
        yield

    app = FastAPI(title="LexGate API", lifespan=lifespan)
    app.state.settings = config
    app.state.runtime = active
    limiter = Limiter(key_func=get_remote_address, default_limits=[config.rate_limit])
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, cast(Any, _rate_limit_exceeded_handler))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(query_router)
    app.include_router(compare_router)
    app.include_router(meta_router)

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request.state.request_id = str(uuid4())
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("Unhandled request error")
            return _error("internal_error", "Internal server error", request, 500)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        return _error("validation_error", "Invalid request", request, 422)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        if exc.status_code == 401:
            name = "unauthorized"
        elif exc.status_code == 429:
            name = "rate_limited"
        elif exc.status_code == 503:
            name = "index_not_ready"
        elif exc.status_code == 504:
            name = "timeout"
        else:
            name = "internal_error"
        return _error(name, str(exc.detail), request, exc.status_code)

    return app


def _error(name: str, message: str, request: Request, status: int) -> JSONResponse:
    body = ErrorResponse(
        error=cast(Any, name),
        message=message,
        request_id=getattr(request.state, "request_id", str(uuid4())),
    )
    return JSONResponse(status_code=status, content=body.model_dump())


app = create_app()
