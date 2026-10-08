"""API routers package."""

from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.admin import router as admin_router
from app.routers.learner import router as learner_router
from app.routers.company import router as company_router
from app.routers.instructor import router as instructor_router
from app.routers.course import router as course_router
from app.routers.job import router as job_router
from app.routers.api_router import api_router

__all__ = [
    "health_router",
    "auth_router",
    "admin_router",
    "learner_router",
    "company_router",
    "instructor_router",
    "course_router",
    "job_router",
    "api_router",
]
