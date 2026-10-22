import logging
from typing import Optional, List, Tuple
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BadRequestException,
    NotFoundException,
    ForbiddenException,
)
from app.models.notification import Notification
from app.models.user import User
from app.repositories.notification_repository import NotificationRepository
from app.repositories.user_repository import UserRepository
from app.services.email_service import email_service
from app.services.websocket_manager import connection_manager
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationMarkReadResponse,
)

logger = logging.getLogger("notification.service")

# Events that mandate email delivery when not explicitly overridden
HIGH_PRIORITY_EMAIL_EVENTS = {
    "APPLICATION_UPDATE",
    "INTERVIEW_INVITE",
    "INTERVIEW_CONFIRMED",
    "PAYMENT_SUCCESS",
}


class NotificationService:
    """Service orchestrating event-driven notifications, persistence, real-time alerts, and email delivery (SKL-17)."""

    def __init__(self):
        self.notification_repo = NotificationRepository()
        self.user_repo = UserRepository()

    async def create_notification(
        self,
        db: Session,
        recipient_id: int,
        event_type: str,
        title: str,
        message: str,
        link_url: Optional[str] = None,
        send_email: Optional[bool] = None,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> Notification:
        """Create and persist a notification, dispatching real-time WebSocket alert and email delivery (AC-1, AC-4).
        
        Handles error cases:
        - Recipient user ID not found or account deactivated.
        - Invalid notification data or missing mandatory event parameters.
        - Notification database storage failure.
        - SMTP delivery errors logged without aborting HTTP transaction.
        """
        # 1. Validate mandatory fields (Error Cases Handled)
        if not event_type or not str(event_type).strip():
            raise BadRequestException("Missing mandatory event_type for notification")
        if not title or not str(title).strip():
            raise BadRequestException("Missing mandatory title for notification")
        if not message or not str(message).strip():
            raise BadRequestException("Missing mandatory message content for notification")

        cleaned_event_type = str(event_type).strip()
        cleaned_title = str(title).strip()[:150]
        cleaned_message = str(message).strip()
        cleaned_link_url = str(link_url).strip()[:255] if link_url else None

        # 2. Validate recipient account existence and active state (Error Cases Handled)
        recipient = self.user_repo.get_by_id(db, recipient_id)
        if not recipient:
            logger.warning("Notification rejected: recipient ID %d not found", recipient_id)
            raise NotFoundException(f"Recipient user with ID {recipient_id} not found")

        if not recipient.is_active:
            logger.warning("Notification rejected: recipient ID %d account is deactivated", recipient_id)
            raise BadRequestException("Cannot dispatch notification to a deactivated account")

        # 3. Determine if email delivery should be attempted
        should_email = (
            send_email
            if send_email is not None
            else (cleaned_event_type.upper() in HIGH_PRIORITY_EMAIL_EVENTS)
        )

        # 4. Persist in MySQL notifications table (AC-1)
        notification = Notification(
            recipient_id=recipient.id,
            event_type=cleaned_event_type,
            title=cleaned_title,
            message=cleaned_message,
            link_url=cleaned_link_url,
            is_read=False,
            email_sent=False,
        )

        try:
            persisted = self.notification_repo.create(db, notification)
        except Exception as exc:
            logger.error("Database storage failure for notification (recipient: %d): %s", recipient.id, exc)
            db.rollback()
            raise BadRequestException("Failed to persist notification in database")

        # 5. Push real-time WebSocket alert if recipient is online
        try:
            if connection_manager.is_user_online(recipient.id):
                ws_payload = {
                    "type": "NOTIFICATION",
                    "data": {
                        "id": persisted.id,
                        "recipient_id": persisted.recipient_id,
                        "event_type": persisted.event_type,
                        "title": persisted.title,
                        "message": persisted.message,
                        "link_url": persisted.link_url,
                        "created_at": persisted.created_at.isoformat(),
                    },
                }
                await connection_manager.send_personal_message(recipient.id, ws_payload)
        except Exception as ws_exc:
            logger.warning(
                "Failed to send real-time notification via WebSocket to user %d: %s",
                recipient.id,
                ws_exc,
            )

        # 6. Attempt email delivery for configured events (AC-4)
        if should_email and recipient.email:
            recipient_full_name = f"{recipient.first_name} {recipient.last_name}".strip() or "Valued Member"
            email_subject = f"[Skill2Career] {cleaned_title}"

            def _dispatch_email():
                success = email_service.send_notification_email(
                    to_email=recipient.email,
                    recipient_name=recipient_full_name,
                    subject=email_subject,
                    event_type=cleaned_event_type,
                    title=cleaned_title,
                    message=cleaned_message,
                    link_url=cleaned_link_url,
                )
                if success:
                    try:
                        self.notification_repo.update_email_status(
                            db, persisted.id, email_sent=True
                        )
                    except Exception as err:
                        logger.warning("Failed to update email_sent status in DB: %s", err)

            if background_tasks:
                background_tasks.add_task(_dispatch_email)
            else:
                _dispatch_email()

        return persisted

    def list_user_notifications(
        self,
        db: Session,
        current_user: User,
        is_read: Optional[bool] = None,
        page: int = 1,
        size: int = 20,
    ) -> NotificationListResponse:
        """List authenticated user's notifications with pagination and unread counts (AC-2, AC-5).
        Enforces tenant isolation: only the calling user's records are retrieved.
        """
        if page < 1:
            page = 1
        if size < 1 or size > 100:
            size = 20

        items, total, unread_count = self.notification_repo.list_for_user(
            db=db,
            user_id=current_user.id,
            is_read=is_read,
            page=page,
            size=size,
        )

        return NotificationListResponse(
            items=[NotificationResponse.model_validate(n) for n in items],
            total=total,
            page=page,
            size=size,
            unread_count=unread_count,
        )

    def get_user_unread_count(self, db: Session, current_user: User) -> int:
        """Retrieve total unread notification count for the authenticated user."""
        return self.notification_repo.get_unread_count(db=db, user_id=current_user.id)

    def mark_as_read(
        self,
        db: Session,
        current_user: User,
        notification_id: int,
    ) -> NotificationMarkReadResponse:
        """Mark a specific notification as read with RBAC ownership check (AC-3, AC-5).
        
        Error Cases Handled:
        - Notification ID not found -> 404
        - Unauthorized user attempting to access or modify another user's notifications -> 403 Forbidden
        """
        notification = self.notification_repo.get_by_id(db, notification_id)
        if not notification:
            raise NotFoundException(f"Notification with ID {notification_id} not found")

        # Strict security check: prevent user A from modifying user B's notifications (AC-5)
        if notification.recipient_id != current_user.id:
            logger.warning(
                "Security alert: User %d attempted to modify notification %d belonging to user %d",
                current_user.id,
                notification_id,
                notification.recipient_id,
            )
            raise ForbiddenException("You are not authorized to access or modify this notification")

        updated = self.notification_repo.mark_as_read(
            db=db, notification_id=notification_id, user_id=current_user.id
        )
        remaining_unread = self.notification_repo.get_unread_count(db=db, user_id=current_user.id)

        return NotificationMarkReadResponse(
            id=notification_id,
            is_read=True,
            updated_count=1 if updated else 0,
            unread_count=remaining_unread,
        )

    def mark_all_as_read(
        self,
        db: Session,
        current_user: User,
    ) -> NotificationMarkReadResponse:
        """Mark all unread notifications for the authenticated user as read (AC-3, AC-5)."""
        updated_count = self.notification_repo.mark_all_as_read(db=db, user_id=current_user.id)
        return NotificationMarkReadResponse(
            id=None,
            is_read=True,
            updated_count=updated_count,
            unread_count=0,
        )


# Global singleton instance
notification_service = NotificationService()
