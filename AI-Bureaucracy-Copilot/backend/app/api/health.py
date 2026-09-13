from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/health")
def get_health():
    return {
        "status": "ok",
        "service": "ai-bureaucracy-copilot-backend",
        "environment": settings.ENVIRONMENT,
    }
