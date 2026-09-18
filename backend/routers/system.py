import asyncio
from datetime import datetime

from fastapi import APIRouter, Query, Request
from starlette.concurrency import run_in_threadpool

from schemas.system import ContextResponse, HealthResponse
from config import get_settings


router = APIRouter(tags=["system"])


@router.get("/api/health", response_model=HealthResponse)
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


@router.get("/api/context", response_model=ContextResponse)
@router.get("/context", response_model=ContextResponse)
def context(
    as_of: datetime = Query(default_factory=datetime.now, description="Reference time; defaults to the current server local time."),
) -> ContextResponse:
    settings = get_settings()
    return ContextResponse(as_of=as_of, user=settings.executive_user_name, role=settings.executive_user_role)
