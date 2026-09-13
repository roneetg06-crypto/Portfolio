import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings

# Router imports
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.profile import router as profile_router
from app.api.schemes import router as schemes_router
from app.api.knowledge import router as knowledge_router
from app.api.documents import router as documents_router
from app.api.automation import router as automation_router
from app.api.notifications import router as notifications_router

# Database initialization
from app.db.session import engine, Base
from app.db.models import User  # register User model with Base

logger = logging.getLogger(__name__)

if engine:
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.warning(f"[DB] Could not automatically create tables on startup: {e}")

app = FastAPI(title="AI Bureaucracy Copilot API")

# Explicit CORS configuration
origins = [
    origin.strip()
    for origin in settings.FRONTEND_ORIGIN.split(",")
    if origin.strip()
]
origins.extend(["http://localhost:5174", "http://localhost:8001"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [f"{err['loc'][-1]}: {err['msg']}" for err in exc.errors()]
    return JSONResponse(
        status_code=422,
        content={"error": "Validation failed: " + "; ".join(errors)},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc) or "Internal server error"},
    )


# Register all API routers
app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(profile_router, prefix="/api")
app.include_router(schemes_router, prefix="/api")
app.include_router(knowledge_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(automation_router, prefix="/api")
app.include_router(notifications_router, prefix="/api")
