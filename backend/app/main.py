from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import time
import uuid

from app.api.routes.ai_chat import router as ai_chat_router
from app.api.routes.route import router as route_router
from app.api.routes.search import router as search_router
from app.core.config import Settings
from app.core.logging import configure_logging


settings = Settings()
configure_logging(settings.log_level)
logger = logging.getLogger("app.http")
app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_frontend_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(ai_chat_router)
app.include_router(search_router)
app.include_router(route_router)


@app.middleware("http")
async def log_http_requests(request, call_next):
    request_id = uuid.uuid4().hex[:12]
    started_at = time.perf_counter()
    logger.info("http_request_start request_id=%s method=%s path=%s query=%s", request_id, request.method, request.url.path, request.url.query)

    response = await call_next(request)

    duration_ms = round((time.perf_counter() - started_at) * 1000, 1)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "http_request_complete request_id=%s method=%s path=%s status=%s duration_ms=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
