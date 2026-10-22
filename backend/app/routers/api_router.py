"""Centralized API router aggregating all modular application routers."""

from fastapi import APIRouter

from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.admin import router as admin_router
from app.routers.learner import router as learner_router
from app.routers.company import router as company_router
from app.routers.instructor import router as instructor_router
from app.routers.course import router as course_router
from app.routers.lesson import router as lesson_router
from app.routers.job import router as job_router
from app.routers.mock_test import router as mock_test_router
from app.routers.screening import router as screening_router
from app.routers.attempt import router as attempt_router
from app.routers.forum import router as forum_router
from app.routers.enrollment import router as enrollment_router
from app.routers.application import router as application_router
from app.routers.interview import router as interview_router
from app.routers.subscription import router as subscription_router
from app.routers.transaction import router as transaction_router, admin_router as admin_transaction_router
from app.routers.payment import router as payment_router
from app.routers.moderation import router as moderation_router
from app.routers.company_dashboard import router as company_dashboard_router
from app.routers.chat import router as chat_router, ws_router

api_router = APIRouter()

# Register modular sub-routers
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(admin_router)
api_router.include_router(moderation_router)
api_router.include_router(learner_router)
api_router.include_router(company_router)
api_router.include_router(instructor_router)
api_router.include_router(course_router)
api_router.include_router(lesson_router)
api_router.include_router(job_router)
api_router.include_router(mock_test_router)
api_router.include_router(screening_router)
api_router.include_router(attempt_router)
api_router.include_router(forum_router)
api_router.include_router(enrollment_router)
api_router.include_router(application_router)
api_router.include_router(interview_router)
api_router.include_router(subscription_router)
api_router.include_router(transaction_router)
api_router.include_router(admin_transaction_router)
api_router.include_router(payment_router)
api_router.include_router(company_dashboard_router)
api_router.include_router(chat_router)
api_router.include_router(ws_router)

router = api_router

__all__ = ["api_router", "router"]
