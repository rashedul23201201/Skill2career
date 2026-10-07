"""Master API Router for SKILL2CAREER Platform.
Registers and aggregates all domain routers under API v1 versioning.
"""
from fastapi import APIRouter
from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.admin import router as admin_router
from app.routers.course import router as course_router

api_router = APIRouter()

# Sprint 1 Foundation & Governance
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(admin_router)

# Sprint 2 LMS Track (SKL-53: Course Management)
api_router.include_router(course_router)

__all__ = ["api_router"]
