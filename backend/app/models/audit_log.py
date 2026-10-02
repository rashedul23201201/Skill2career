from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import String, DateTime, Integer, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class AuditLog(Base):
    """Database model for tracking administrative actions, role overrides, and security events (SKL-50/SKL-24)."""
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    target_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        index=True
    )

    admin = relationship("User", foreign_keys=[admin_id])
    target_user = relationship("User", foreign_keys=[target_user_id])

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} action='{self.action}' admin_id={self.admin_id} target={self.target_user_id}>"
