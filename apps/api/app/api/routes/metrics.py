from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import LlmCall
from app.schemas.api import CallMetric, CallMetricList

router = APIRouter()


@router.get("/calls", response_model=CallMetricList)
async def list_calls(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> CallMetricList:
    total = await db.scalar(select(func.count()).select_from(LlmCall))
    result = await db.scalars(
        select(LlmCall)
        .order_by(LlmCall.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = [
        CallMetric(
            request_id=item.request_id,
            operation=item.operation,
            model=item.model,
            input_tokens=item.input_tokens,
            output_tokens=item.output_tokens,
            estimated_cost=float(item.estimated_cost),
            currency=item.currency,
            latency_ms=item.latency_ms,
            first_token_ms=item.first_token_ms,
            success=item.success,
            created_at=item.created_at,
        )
        for item in result
    ]
    return CallMetricList(items=items, total=total or 0)

