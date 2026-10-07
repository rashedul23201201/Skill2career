"""API routers package."""

from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.admin import router as admin_router
from app.routers.course import router as course_router

__all__ = ["health_router", "auth_router", "admin_router", "course_router"]

