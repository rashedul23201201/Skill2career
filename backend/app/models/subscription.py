import enum
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, Numeric, ForeignKey, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class SubscriptionPlanCode(str, enum.Enum):
    """Supported subscription plan tiers."""
    FREE = "FREE"
    PRO_MONTHLY = "PRO_MONTHLY"
    PRO_YEARLY = "PRO_YEARLY"


class SubscriptionBillingCycle(str, enum.Enum):
    """Subscription billing cadence."""
    FREE = "FREE"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


class SubscriptionStatus(str, enum.Enum):
    """User subscription status."""
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, enum.Enum):
    """Status of payment transactions."""
    SUCCESS = "SUCCESS"
    PENDING = "PENDING"
    FAILED = "FAILED"
    REVERSED = "REVERSED"


class SubscriptionPlan(Base):
    """Subscription plan tier catalog (SKL-19)."""
    __tablename__ = "subscription_plans"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    billing_cycle: Mapped[str] = mapped_column(String(50), default="MONTHLY", nullable=False)
    features: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    subscriptions = relationship("UserSubscription", back_populates="plan", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<SubscriptionPlan id={self.id} code='{self.code}' price={self.price}>"


class UserSubscription(Base):
    """User active or historical subscription record (SKL-19)."""
    __tablename__ = "user_subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("subscription_plans.id", ondelete="CASCADE"), nullable=False, index=True)

    status: Mapped[str] = mapped_column(String(50), default=SubscriptionStatus.ACTIVE.value, nullable=False, index=True)
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User", backref="user_subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")

    def __repr__(self) -> str:
        return f"<UserSubscription id={self.id} user_id={self.user_id} plan_id={self.plan_id} status='{self.status}'>"


class PaymentGatewayType(str, enum.Enum):
    """Supported payment gateway providers (SKL-20)."""
    SSLCOMMERZ = "SSLCOMMERZ"
    GLOBAL_GATEWAY = "GLOBAL_GATEWAY"
    SIMULATED = "SIMULATED"


class PaymentTransaction(Base):
    """Payment transaction record for ledger and verification (SKL-21 / SKL-20)."""
    __tablename__ = "payment_transactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    transaction_ref: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subscription_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("user_subscriptions.id", ondelete="SET NULL"), nullable=True, index=True
    )

    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="BDT", nullable=False)
    gateway: Mapped[str] = mapped_column(String(50), default="SIMULATED", nullable=False)
    gateway_type: Mapped[str] = mapped_column(String(50), default="SSLCOMMERZ", nullable=False)
    gateway_session_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    gateway_val_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    bank_tran_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    card_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default=PaymentStatus.SUCCESS.value, nullable=False, index=True)

    raw_response: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    user = relationship("User", foreign_keys=[user_id], backref="payment_transactions")
    subscription = relationship("UserSubscription", backref="transactions")

    def __repr__(self) -> str:
        return f"<PaymentTransaction id={self.id} ref='{self.transaction_ref}' amount={self.amount} status='{self.status}'>"
