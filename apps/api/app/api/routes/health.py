import redis.asyncio as redis
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine
from app.schemas.api import HealthResponse, ReadinessResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service=settings.app_name, version="0.1.0")


@router.get("/ready", response_model=ReadinessResponse)
async def ready() -> ReadinessResponse:
    database_status = "ok"
    redis_status = "ok"

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:
        database_status = "unavailable"

    client = redis.from_url(settings.redis_url)
    try:
        await client.ping()
    except Exception:
        redis_status = "unavailable"
    finally:
        await client.aclose()

    if database_status != "ok" or redis_status != "ok":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "database": database_status,
                "redis": redis_status,
            },
        )

    return ReadinessResponse(
        status="ready",
        database=database_status,
        redis=redis_status,
        vector_store=settings.vector_store,
        model_configured=settings.demo_mode
        or bool(settings.embedding_api_key and settings.llm_api_key),
        model_mode="demo" if settings.demo_mode else "live",
    )
