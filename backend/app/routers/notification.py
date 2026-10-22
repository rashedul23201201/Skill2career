import logging
from typing import Optional
from fastapi import (
    APIRouter,
    Depends,
    Query,
    Path,
    status,
)
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import ApiResponse
from app.schemas.notification import (
    NotificationListResponse,
    NotificationMarkReadResponse,
    NotificationUnreadCountResponse,
)
from app.services.notification_service import notification_service

logger = logging.getLogger("notification.router")

router = APIRouter(prefix="/notifications", tags=["Notification System (SKL-17)"])


@router.get(
    "",
    response_model=ApiResponse[NotificationListResponse],
    status_code=status.HTTP_200_OK,
    summary="List authenticated user's notifications (SKL-17 AC-2, AC-5)",
)
def list_my_notifications(
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=20, ge=1, le=100, description="Page size"),
    is_read: Optional[bool] = Query(default=None, description="Filter by read/unread status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[NotificationListResponse]:
    """Retrieve paginated notifications and total unread count for the calling user.
    Guarantees tenant isolation: users only see their own notifications (AC-5).
    """
    result = notification_service.list_user_notifications(
        db=db,
        current_user=current_user,
        is_read=is_read,
        page=page,
        size=size,
    )
    return ApiResponse[NotificationListResponse](
        success=True,
        message="Notifications retrieved successfully",
        data=result,
    )


@router.get(
    "/unread-count",
    response_model=ApiResponse[NotificationUnreadCountResponse],
    status_code=status.HTTP_200_OK,
    summary="Get unread notification count badge (SKL-17)",
)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[NotificationUnreadCountResponse]:
    """Retrieve fast count of unread notifications for navbar indicator."""
    count = notification_service.get_user_unread_count(db=db, current_user=current_user)
    return ApiResponse[NotificationUnreadCountResponse](
        success=True,
        message="Unread notification count retrieved",
        data=NotificationUnreadCountResponse(unread_count=count),
    )


@router.patch(
    "/mark-all-read",
    response_model=ApiResponse[NotificationMarkReadResponse],
    status_code=status.HTTP_200_OK,
    summary="Mark all notifications as read (SKL-17 AC-3)",
)
def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[NotificationMarkReadResponse]:
    """Mark all unread notifications for the calling user as read."""
    result = notification_service.mark_all_as_read(db=db, current_user=current_user)
    return ApiResponse[NotificationMarkReadResponse](
        success=True,
        message="All notifications marked as read",
        data=result,
    )


@router.patch(
    "/{notification_id}/read",
    response_model=ApiResponse[NotificationMarkReadResponse],
    status_code=status.HTTP_200_OK,
    summary="Mark specific notification as read (SKL-17 AC-3, AC-5)",
)
def mark_notification_as_read(
    notification_id: int = Path(..., gt=0, description="Target notification ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[NotificationMarkReadResponse]:
    """Mark a specific notification as read. Validates that the notification belongs to the calling user."""
    result = notification_service.mark_as_read(
        db=db,
        current_user=current_user,
        notification_id=notification_id,
    )
    return ApiResponse[NotificationMarkReadResponse](
        success=True,
        message="Notification marked as read",
        data=result,
    )
