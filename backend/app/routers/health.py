from typing import Dict
from fastapi import APIRouter, status
from app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health", status_code=status.HTTP_200_OK, summary="API Health Check")
def health_check() -> Dict[str, str]:
    """Return health status of the backend API service."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "version": "1.0.0"
    }
