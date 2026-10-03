"""API routers package."""

from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.admin import router as admin_router
from app.routers.learner import router as learner_router
from app.routers.company import router as company_router

__all__ = ["health_router", "auth_router", "admin_router", "learner_router", "company_router"]
