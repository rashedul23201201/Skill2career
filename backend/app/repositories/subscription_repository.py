from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.subscription import (
    SubscriptionPlan,
    UserSubscription,
    PaymentTransaction,
    SubscriptionStatus,
    SubscriptionPlanCode,
    SubscriptionBillingCycle,
    PaymentStatus,
)


class SubscriptionRepository:
    """Repository handling database access for subscriptions, plans, and transaction ledger."""

    def ensure_seed_plans(self, db: Session) -> None:
        """Seed default FREE, PRO_MONTHLY, and PRO_YEARLY plans if they do not exist."""
        default_plans = [
            {
                "name": "Free",
                "code": SubscriptionPlanCode.FREE.value,
                "description": "Essential resources for initial preparation and self-guided revision.",
                "price": 0.00,
                "billing_cycle": SubscriptionBillingCycle.FREE.value,
                "features": [
                    "Free courses",
                    "Limited mock tests",
                    "Forum access",
                ],
                "is_active": True,
            },
            {
                "name": "Monthly",
                "code": SubscriptionPlanCode.PRO_MONTHLY.value,
                "description": "Complete monthly access for dedicated BCS, bank, and tech job seekers.",
                "price": 499.00,
                "billing_cycle": SubscriptionBillingCycle.MONTHLY.value,
                "features": [
                    "Full course access",
                    "Mock tests",
                    "Interview preparation",
                    "Advanced analytics",
                ],
                "is_active": True,
            },
            {
                "name": "Yearly",
                "code": SubscriptionPlanCode.PRO_YEARLY.value,
                "description": "Best value for sustained 12-month career transformation and continuous exam series.",
                "price": 4999.00,
                "billing_cycle": SubscriptionBillingCycle.YEARLY.value,
                "features": [
                    "Full course access",
                    "Mock tests",
                    "Interview preparation",
                    "Advanced analytics",
                    "Priority support",
                ],
                "is_active": True,
            },
        ]

        for p_data in default_plans:
            existing = db.query(SubscriptionPlan).filter(SubscriptionPlan.code == p_data["code"]).first()
            if not existing:
                plan = SubscriptionPlan(**p_data)
                db.add(plan)
        db.commit()

    def get_all_plans(self, db: Session, active_only: bool = True) -> List[SubscriptionPlan]:
        query = db.query(SubscriptionPlan)
        if active_only:
            query = query.filter(SubscriptionPlan.is_active == True)
        return query.order_by(SubscriptionPlan.price.asc()).all()

    def get_plan_by_id(self, db: Session, plan_id: int) -> Optional[SubscriptionPlan]:
        return db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()

    def get_plan_by_code(self, db: Session, code: str) -> Optional[SubscriptionPlan]:
        clean_code = str(code).strip().upper()
        return db.query(SubscriptionPlan).filter(SubscriptionPlan.code == clean_code).first()

    def get_active_subscription(self, db: Session, user_id: int) -> Optional[UserSubscription]:
        """Fetch current active subscription for a given user."""
        return (
            db.query(UserSubscription)
            .filter(
                UserSubscription.user_id == user_id,
                UserSubscription.status == SubscriptionStatus.ACTIVE.value,
            )
            .order_by(desc(UserSubscription.created_at))
            .first()
        )

    def get_subscriptions_by_user(self, db: Session, user_id: int) -> List[UserSubscription]:
        return (
            db.query(UserSubscription)
            .filter(UserSubscription.user_id == user_id)
            .order_by(desc(UserSubscription.created_at))
            .all()
        )

    def deactivate_user_active_subscriptions(self, db: Session, user_id: int) -> None:
        """Mark any existing ACTIVE subscriptions as CANCELLED before activating a new tier."""
        now = datetime.now(timezone.utc)
        active_subs = (
            db.query(UserSubscription)
            .filter(
                UserSubscription.user_id == user_id,
                UserSubscription.status == SubscriptionStatus.ACTIVE.value,
            )
            .all()
        )
        for sub in active_subs:
            sub.status = SubscriptionStatus.CANCELLED.value
            sub.auto_renew = False
            sub.updated_at = now
        db.flush()

    def create_user_subscription(self, db: Session, subscription: UserSubscription) -> UserSubscription:
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        return subscription

    def get_subscription_by_id(self, db: Session, subscription_id: int) -> Optional[UserSubscription]:
        return db.query(UserSubscription).filter(UserSubscription.id == subscription_id).first()

    def create_transaction(self, db: Session, transaction: PaymentTransaction) -> PaymentTransaction:
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return transaction

    def get_user_transactions(self, db: Session, user_id: int) -> List[PaymentTransaction]:
        return (
            db.query(PaymentTransaction)
            .filter(PaymentTransaction.user_id == user_id)
            .order_by(desc(PaymentTransaction.created_at))
            .all()
        )

    def get_all_transactions(self, db: Session, limit: int = 50, offset: int = 0) -> List[PaymentTransaction]:
        return (
            db.query(PaymentTransaction)
            .order_by(desc(PaymentTransaction.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_transaction_by_ref(self, db: Session, transaction_ref: str) -> Optional[PaymentTransaction]:
        return (
            db.query(PaymentTransaction)
            .filter(PaymentTransaction.transaction_ref == transaction_ref.strip())
            .first()
        )

    def get_transaction_by_id(self, db: Session, transaction_id: int) -> Optional[PaymentTransaction]:
        return (
            db.query(PaymentTransaction)
            .filter(PaymentTransaction.id == transaction_id)
            .first()
        )
