from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.curves import router as curves_router
from app.api.physics import router as physics_router
from app.api.routes import router
from app.logging_config import configure_logging

configure_logging()
logger = configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("API started")
    yield


app = FastAPI(
    title="esp-core",
    version="1C",
    summary="ESP educativa. Anatomía 1A, bomba 1B y hidráulica estática 1C.",
    lifespan=lifespan,
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
)
app.include_router(router, prefix="/api/v1")
app.include_router(physics_router, prefix="/api/v1")
app.include_router(curves_router, prefix="/api/v1")
