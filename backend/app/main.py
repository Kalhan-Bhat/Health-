"""FastAPI application entry point.

Run with:  uvicorn app.main:app --reload --port 8000   (from the backend/ folder)

Hard rule: the app exposes exactly two application endpoints:
    POST /api/analyze-report
    POST /api/ask
`tests/test_routes.py` enforces this.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.errors import register_exception_handlers
from app.routes import analyze, ask
from app.services.rag.embedder import get_embedder
from app.services.rag.index_store import store as index_store

settings = get_settings()

logging.basicConfig(
    level=settings.LOG_LEVEL.upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("medbridge")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Startup checks. Runs once when the server starts."""
    if not settings.has_api_key:
        # Fail fast with a clear message instead of failing on the first request.
        msg = "GROQ_API_KEY is not set. Copy backend/.env.example to backend/.env and add your key."
        logger.error(msg)
        raise RuntimeError(msg)
    logger.info("MedBridge API starting (env=%s, model=%s)", settings.APP_ENV, settings.GROQ_MODEL)

    # Load the knowledge-base index and warm up the embedding model once.
    # If this fails, /api/ask returns 503 INDEX_NOT_READY but /api/analyze-report still works.
    if index_store.load(settings.index_path, settings.EMBEDDING_MODEL):
        try:
            get_embedder(settings.EMBEDDING_MODEL).embed(["warm-up"])
        except Exception:
            logger.exception("Could not load the embedding model; /api/ask is disabled")
            index_store.ready = False
    yield


# Interactive API docs are framework routes, not application endpoints.
# They are only switched on in development (spec §6).
docs_enabled = settings.APP_ENV == "development"
app = FastAPI(
    title="MedBridge API",
    version="1.0.0",
    docs_url="/docs" if docs_enabled else None,
    redoc_url=None,
    openapi_url="/openapi.json" if docs_enabled else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

register_exception_handlers(app)

# The only two application routers.
app.include_router(analyze.router, prefix="/api")
app.include_router(ask.router, prefix="/api")
