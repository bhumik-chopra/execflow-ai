import asyncio
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Query, Request
from starlette.concurrency import run_in_threadpool

from schemas.system import DEFAULT_AS_OF, ContextResponse, HealthResponse
from config import get_settings


router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    mongodb_ok, groq_ok = await asyncio.gather(
        run_in_threadpool(request.app.state.mongodb.ping),
        request.app.state.llm.ping(),
    )
    return HealthResponse(
        mongodb="ok" if mongodb_ok else "unavailable",
        groq="configured" if groq_ok else "unavailable",
        groq_model=request.app.state.llm.model,
    )


@router.get("/context", response_model=ContextResponse)
def context(
    as_of: Annotated[
        datetime,
        Query(description="Assignment reference time; never defaults to the computer clock."),
    ] = DEFAULT_AS_OF,
) -> ContextResponse:
    settings = get_settings()
    return ContextResponse(as_of=as_of, user=settings.executive_user_name, role=settings.executive_user_role)
