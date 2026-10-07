"""Centralized API router aggregating all modular application routers."""

from fastapi import APIRouter

from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.admin import router as admin_router
from app.routers.learner import router as learner_router
from app.routers.company import router as company_router
from app.routers.instructor import router as instructor_router
from app.routers.course import router as course_router

api_router = APIRouter()

# Register modular sub-routers
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(admin_router)
api_router.include_router(learner_router)
api_router.include_router(company_router)
api_router.include_router(instructor_router)
api_router.include_router(course_router)

router = api_router

__all__ = ["api_router", "router"]
