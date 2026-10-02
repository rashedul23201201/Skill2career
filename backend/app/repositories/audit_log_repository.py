from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from app.models.audit_log import AuditLog


class AuditLogRepository:
    """Repository handling database operations for AuditLog entity."""

    @staticmethod
    def create(
        db: Session,
        admin_id: Optional[int],
        target_user_id: Optional[int],
        action: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """Create and persist a new security or administrative audit log."""
        record = AuditLog(
            admin_id=admin_id,
            target_user_id=target_user_id,
            action=action,
            details=details,
            ip_address=ip_address,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_recent(db: Session, limit: int = 20) -> List[AuditLog]:
        """Fetch the most recent audit logs ordered by creation timestamp."""
        statement = (
            select(AuditLog)
            .options(joinedload(AuditLog.admin), joinedload(AuditLog.target_user))
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        return list(db.execute(statement).scalars().all())
