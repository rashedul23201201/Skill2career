from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import require_admin, require_role, get_current_user
from app.models.user import User, UserRole
from app.schemas.auth import ApiResponse
from app.schemas.moderation import (
    ModerationDecisionRequest,
    ModerationItemResponse,
    PendingModerationResponse,
    ContentModerationLogResponse,
)
from app.services.moderation_service import ModerationService

router = APIRouter(prefix="/admin/moderation", tags=["Content Moderation (SKL-25)"])
moderation_service = ModerationService()


@router.get(
    "/pending",
    response_model=ApiResponse[PendingModerationResponse],
    status_code=status.HTTP_200_OK,
    summary="Get queue of courses and mock tests pending moderation review (SKL-25)",
)
def get_pending_moderation(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> ApiResponse[PendingModerationResponse]:
    """Retrieve all submissions awaiting review by administrative staff."""
    result = moderation_service.get_pending_moderation(db)
    return ApiResponse[PendingModerationResponse](
        success=True,
        message="Pending moderation queue retrieved successfully",
        data=result,
    )


@router.get(
    "/items",
    response_model=ApiResponse[List[ModerationItemResponse]],
    status_code=status.HTTP_200_OK,
    summary="List moderatable items with status and type filters (SKL-25)",
)
def list_moderation_items(
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by status (e.g. PENDING_REVIEW, APPROVED, RESTRICTED)"),
    content_type: Optional[str] = Query(default=None, description="Filter by type (COURSE, MOCK_TEST)"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> ApiResponse[List[ModerationItemResponse]]:
    """Fetch items across all moderation stages with optional type/status filters."""
    items = moderation_service.get_all_moderation_items(
        db=db, status=status_filter, content_type=content_type
    )
    return ApiResponse[List[ModerationItemResponse]](
        success=True,
        message="Moderation items retrieved successfully",
        data=items,
    )


@router.get(
    "/stats",
    response_model=ApiResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Get moderation summary counters for dashboard metrics (SKL-25)",
)
def get_moderation_stats(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> ApiResponse[Dict[str, Any]]:
    """Retrieve counts of pending, approved, and restricted courses and mock tests."""
    stats = moderation_service.get_moderation_stats(db)
    return ApiResponse[Dict[str, Any]](
        success=True,
        message="Moderation stats retrieved successfully",
        data=stats,
    )


@router.get(
    "/courses/{course_id}/preview",
    response_model=ApiResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Inspect complete course curriculum and metadata for moderation (SKL-25)",
)
def get_course_preview(
    course_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> ApiResponse[Dict[str, Any]]:
    """Detailed preview of course curriculum for administrative slide-over drawer."""
    preview = moderation_service.get_course_preview(db, course_id=course_id)
    return ApiResponse[Dict[str, Any]](
        success=True,
        message="Course preview retrieved successfully",
        data=preview,
    )


@router.get(
    "/mock-tests/{test_id}/preview",
    response_model=ApiResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Inspect complete mock test questions and answer keys for moderation (SKL-25)",
)
def get_mock_test_preview(
    test_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> ApiResponse[Dict[str, Any]]:
    """Detailed preview of test questions for administrative slide-over drawer."""
    preview = moderation_service.get_mock_test_preview(db, test_id=test_id)
    return ApiResponse[Dict[str, Any]](
        success=True,
        message="Mock test preview retrieved successfully",
        data=preview,
    )


@router.post(
    "/courses/{course_id}/approve",
    response_model=ApiResponse[ModerationItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Approve course for public catalog publication (SKL-25)",
)
def approve_course(
    course_id: int,
    decision: ModerationDecisionRequest = ModerationDecisionRequest(),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> ApiResponse[ModerationItemResponse]:
    """Approve a course, making it discoverable in the public catalog."""
    updated = moderation_service.approve_course(
        db=db, course_id=course_id, admin_user=admin_user, notes=decision.notes or decision.reason
    )
    return ApiResponse[ModerationItemResponse](
        success=True,
        message="Course approved successfully",
        data=updated,
    )


@router.post(
    "/courses/{course_id}/restrict",
    response_model=ApiResponse[ModerationItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Restrict course from public catalog (SKL-25)",
)
def restrict_course(
    course_id: int,
    decision: ModerationDecisionRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> ApiResponse[ModerationItemResponse]:
    """Restrict a course due to policy violations or quality non-compliance."""
    reason = decision.reason or decision.notes or ""
    updated = moderation_service.restrict_course(
        db=db, course_id=course_id, admin_user=admin_user, reason=reason
    )
    return ApiResponse[ModerationItemResponse](
        success=True,
        message="Course restricted successfully",
        data=updated,
    )


@router.post(
    "/mock-tests/{test_id}/approve",
    response_model=ApiResponse[ModerationItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Approve mock test for assessment catalog (SKL-25)",
)
def approve_mock_test(
    test_id: int,
    decision: ModerationDecisionRequest = ModerationDecisionRequest(),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> ApiResponse[ModerationItemResponse]:
    """Approve a mock test, making it discoverable for learner attempts."""
    updated = moderation_service.approve_mock_test(
        db=db, test_id=test_id, admin_user=admin_user, notes=decision.notes or decision.reason
    )
    return ApiResponse[ModerationItemResponse](
        success=True,
        message="Mock test approved successfully",
        data=updated,
    )


@router.post(
    "/mock-tests/{test_id}/restrict",
    response_model=ApiResponse[ModerationItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Restrict mock test from assessment catalog (SKL-25)",
)
def restrict_mock_test(
    test_id: int,
    decision: ModerationDecisionRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> ApiResponse[ModerationItemResponse]:
    """Restrict a mock test due to policy violations or inaccurate question sets."""
    reason = decision.reason or decision.notes or ""
    updated = moderation_service.restrict_mock_test(
        db=db, test_id=test_id, admin_user=admin_user, reason=reason
    )
    return ApiResponse[ModerationItemResponse](
        success=True,
        message="Mock test restricted successfully",
        data=updated,
    )


@router.get(
    "/logs",
    response_model=ApiResponse[List[ContentModerationLogResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get recent content moderation audit log events (SKL-25)",
)
def get_moderation_logs(
    limit: int = Query(default=50, ge=1, le=200),
    content_type: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> ApiResponse[List[ContentModerationLogResponse]]:
    """Retrieve chronological audit trail of administrative moderation decisions."""
    logs = moderation_service.get_moderation_logs(db=db, limit=limit, content_type=content_type)
    return ApiResponse[List[ContentModerationLogResponse]](
        success=True,
        message="Moderation audit logs retrieved successfully",
        data=logs,
    )
