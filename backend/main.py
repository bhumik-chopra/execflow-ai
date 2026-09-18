from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from database import DatabaseUnavailable, MongoDB
from routers.system import router
from services.llm import LLMError, LLMService
from services.repository import Repository
from services.engine import Engine, IngestionError, SourceConflict
from routers.api import router as api_router
from pymongo.errors import PyMongoError


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.mongodb = MongoDB(settings)
    app.state.llm = LLMService(settings)
    app.state.engine = Engine(Repository(app.state.mongodb), app.state.llm, settings.executive_user_name)
    try:
        yield
    finally:
        await app.state.llm.close()
        app.state.mongodb.close()


app = FastAPI(
    title="ExecFlow AI",
    description="Executive Commitment & Action Copilot — initial scaffold",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(router)
app.include_router(api_router)


@app.exception_handler(PyMongoError)
async def mongo_error_handler(request: Request, exc: PyMongoError):
    return JSONResponse(status_code=503, content={"detail": "MongoDB Atlas is currently unavailable. Retry after checking connectivity and credentials."})


@app.exception_handler(IngestionError)
async def ingestion_error_handler(request: Request, exc: IngestionError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message, "source_id": exc.source_id, "raw_source_saved": True, "retry": "Resubmit the same source to retry processing."})


@app.exception_handler(SourceConflict)
async def conflict_handler(request: Request, exc: SourceConflict):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(DatabaseUnavailable)
async def unavailable_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(LLMError)
async def llm_error_handler(
    request: Request, exc: LLMError
) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})
