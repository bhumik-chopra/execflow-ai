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
from routers.auth import router as auth_router, authenticated
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
app.include_router(router)
app.include_router(api_router)
app.include_router(auth_router)


@app.middleware("http")
async def require_session(request: Request, call_next):
    path = request.url.path.rstrip("/")
    origin = request.headers.get("origin")
    if request.method not in {"GET", "HEAD", "OPTIONS"} and origin and origin not in allowed_origins:
        return JSONResponse(status_code=403, content={"detail": "This origin is not allowed."})
    protected = path.startswith("/api/") or path == "/context"
    public = path in {"/api/auth/login", "/api/auth/logout", "/api/health"}
    if protected and not public and request.method != "OPTIONS" and not authenticated(request):
        return JSONResponse(status_code=401, content={"detail": "Please sign in to continue."})
    response = await call_next(request)
    if protected:
        response.headers["Cache-Control"] = "no-store"
    return response


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


# Register last so CORS also wraps early authentication/error responses.
allowed_origins = list(dict.fromkeys([
    "http://localhost:5173", "http://127.0.0.1:5173",
    get_settings().frontend_url.rstrip("/"),
]))
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)
