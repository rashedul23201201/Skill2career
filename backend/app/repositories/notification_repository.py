from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy import select, func, and_, update, delete
from sqlalchemy.orm import Session

from app.models.notification import Notification


class NotificationRepository:
    """Persistence operations for notifications (SKL-17)."""

    @staticmethod
    def create(db: Session, notification: Notification) -> Notification:
        """Persist a new notification record in MySQL (AC-1)."""
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    @staticmethod
    def get_by_id(db: Session, notification_id: int) -> Optional[Notification]:
        """Fetch a notification record by primary key."""
        stmt = select(Notification).where(Notification.id == notification_id)
        return db.execute(stmt).scalars().first()

    @staticmethod
    def list_for_user(
        db: Session,
        user_id: int,
        is_read: Optional[bool] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[Notification], int, int]:
        """List notifications belonging to a specific recipient with pagination and unread counts (AC-2, AC-5).
        Returns (items, total_filtered, unread_count).
        """
        base_filters = [Notification.recipient_id == user_id]
        if is_read is not None:
            base_filters.append(Notification.is_read.is_(is_read))

        # Total matching filtered query
        total_stmt = select(func.count(Notification.id)).where(and_(*base_filters))
        total = db.execute(total_stmt).scalar() or 0

        # Unread count strictly for this user regardless of query filter
        unread_stmt = select(func.count(Notification.id)).where(
            and_(
                Notification.recipient_id == user_id,
                Notification.is_read.is_(False),
            )
        )
        unread_count = db.execute(unread_stmt).scalar() or 0

        # Paginated items ordered newest first
        offset = max(0, (page - 1) * size)
        items_stmt = (
            select(Notification)
            .where(and_(*base_filters))
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .offset(offset)
            .limit(size)
        )
        items = list(db.execute(items_stmt).scalars().all())

        return items, total, unread_count

    @staticmethod
    def get_unread_count(db: Session, user_id: int) -> int:
        """Count unread notifications for a user."""
        stmt = select(func.count(Notification.id)).where(
            and_(
                Notification.recipient_id == user_id,
                Notification.is_read.is_(False),
            )
        )
        return db.execute(stmt).scalar() or 0

    @staticmethod
    def mark_as_read(
        db: Session, notification_id: int, user_id: int
    ) -> Optional[Notification]:
        """Mark a specific notification as read, ensuring ownership (AC-3, AC-5)."""
        stmt = select(Notification).where(
            and_(
                Notification.id == notification_id,
                Notification.recipient_id == user_id,
            )
        )
        notification = db.execute(stmt).scalars().first()
        if not notification:
            return None

        if not notification.is_read:
            notification.is_read = True
            db.commit()
            db.refresh(notification)

        return notification

    @staticmethod
    def mark_all_as_read(db: Session, user_id: int) -> int:
        """Mark all unread notifications for a recipient as read (AC-3, AC-5)."""
        stmt = (
            update(Notification)
            .where(
                and_(
                    Notification.recipient_id == user_id,
                    Notification.is_read.is_(False),
                )
            )
            .values(is_read=True)
        )
        result = db.execute(stmt)
        db.commit()
        return result.rowcount

    @staticmethod
    def update_email_status(
        db: Session, notification_id: int, email_sent: bool
    ) -> Optional[Notification]:
        """Update email delivery status on the notification record."""
        notification = NotificationRepository.get_by_id(db, notification_id)
        if notification:
            notification.email_sent = email_sent
            db.commit()
            db.refresh(notification)
        return notification
