import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException, BadRequestException, ForbiddenException
from app.models.user import User, UserRole
from app.models.subscription import (
    SubscriptionPlan,
    UserSubscription,
    PaymentTransaction,
    SubscriptionStatus,
    SubscriptionPlanCode,
    SubscriptionBillingCycle,
    PaymentStatus,
)
from app.repositories.subscription_repository import SubscriptionRepository
from app.schemas.subscription import (
    SubscriptionPlanResponse,
    UserSubscriptionResponse,
    SelectPlanRequest,
    EntitlementsResponse,
    PaymentTransactionResponse,
    TransactionVerifyRequest,
    InvoiceResponse,
)


def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class SubscriptionService:
    """Core domain service for subscription plans, entitlement checks, and financial records."""

    def __init__(self, subscription_repo: Optional[SubscriptionRepository] = None):
        self.repo = subscription_repo or SubscriptionRepository()

    def _to_plan_response(self, plan: SubscriptionPlan) -> SubscriptionPlanResponse:
        return SubscriptionPlanResponse(
            id=plan.id,
            name=plan.name,
            code=plan.code,
            description=plan.description,
            price=float(plan.price),
            billing_cycle=plan.billing_cycle,
            features=plan.features or [],
            is_active=plan.is_active,
            created_at=plan.created_at,
        )

    def _to_user_subscription_response(self, sub: UserSubscription) -> UserSubscriptionResponse:
        is_pro = False
        plan_resp = None
        if sub.plan:
            plan_resp = self._to_plan_response(sub.plan)
            if sub.plan.code in [SubscriptionPlanCode.PRO_MONTHLY.value, SubscriptionPlanCode.PRO_YEARLY.value]:
                if sub.status == SubscriptionStatus.ACTIVE.value:
                    now = datetime.now(timezone.utc)
                    expires = _ensure_utc(sub.expires_at)
                    if expires is None or expires > now:
                        is_pro = True

        return UserSubscriptionResponse(
            id=sub.id,
            user_id=sub.user_id,
            plan_id=sub.plan_id,
            plan=plan_resp,
            status=sub.status,
            starts_at=sub.starts_at,
            expires_at=sub.expires_at,
            auto_renew=sub.auto_renew,
            is_pro=is_pro,
            created_at=sub.created_at,
        )

    def _to_transaction_response(self, txn: PaymentTransaction) -> PaymentTransactionResponse:
        plan_name = None
        if txn.subscription and txn.subscription.plan:
            plan_name = txn.subscription.plan.name
        elif txn.raw_response and isinstance(txn.raw_response, dict):
            plan_name = txn.raw_response.get("plan_name") or txn.raw_response.get("plan_code")

        user_email = None
        user_name = None
        if txn.user:
            user_email = txn.user.email
            user_name = f"{txn.user.first_name} {txn.user.last_name}".strip()

        return PaymentTransactionResponse(
            id=txn.id,
            transaction_ref=txn.transaction_ref,
            user_id=txn.user_id,
            subscription_id=txn.subscription_id,
            plan_name=plan_name,
            user_email=user_email,
            user_name=user_name,
            amount=float(txn.amount),
            currency=txn.currency,
            gateway=txn.gateway,
            gateway_type=getattr(txn, "gateway_type", "SSLCOMMERZ"),
            gateway_session_key=getattr(txn, "gateway_session_key", None),
            gateway_val_id=getattr(txn, "gateway_val_id", None),
            bank_tran_id=getattr(txn, "bank_tran_id", None),
            card_type=getattr(txn, "card_type", None),
            error_reason=getattr(txn, "error_reason", None),
            status=txn.status,
            raw_response=txn.raw_response,
            verified_at=txn.verified_at,
            created_at=txn.created_at,
        )

    def get_plans(self, db: Session) -> List[SubscriptionPlanResponse]:
        """Fetch all public active subscription tier plans."""
        self.repo.ensure_seed_plans(db)
        plans = self.repo.get_all_plans(db, active_only=True)
        return [self._to_plan_response(p) for p in plans]

    def get_my_subscription(self, db: Session, current_user: User) -> UserSubscriptionResponse:
        """Fetch authenticated user's current subscription tier with automatic fallback to Free."""
        self.repo.ensure_seed_plans(db)
        active_sub = self.repo.get_active_subscription(db, current_user.id)

        now = datetime.now(timezone.utc)
        if active_sub:
            expires = _ensure_utc(active_sub.expires_at)
            if expires and expires < now:
                active_sub.status = SubscriptionStatus.EXPIRED.value
                active_sub.auto_renew = False
                db.commit()
                db.refresh(active_sub)
                active_sub = None

        if not active_sub:
            free_plan = self.repo.get_plan_by_code(db, SubscriptionPlanCode.FREE.value)
            if not free_plan:
                self.repo.ensure_seed_plans(db)
                free_plan = self.repo.get_plan_by_code(db, SubscriptionPlanCode.FREE.value)

            new_sub = UserSubscription(
                user_id=current_user.id,
                plan_id=free_plan.id,
                status=SubscriptionStatus.ACTIVE.value,
                starts_at=now,
                expires_at=None,
                auto_renew=False,
            )
            active_sub = self.repo.create_user_subscription(db, new_sub)

        return self._to_user_subscription_response(active_sub)

    def select_plan(self, db: Session, current_user: User, request: SelectPlanRequest) -> UserSubscriptionResponse:
        """Subscribe or change current plan tier."""
        self.repo.ensure_seed_plans(db)

        plan: Optional[SubscriptionPlan] = None
        if request.plan_code:
            plan = self.repo.get_plan_by_code(db, request.plan_code)
        elif request.plan_id:
            plan = self.repo.get_plan_by_id(db, request.plan_id)

        if not plan or not plan.is_active:
            raise NotFoundException("Subscription plan not found or currently inactive")

        now = datetime.now(timezone.utc)

        # Calculate billing cycle and expiration
        clean_code = plan.code.upper()
        if clean_code == SubscriptionPlanCode.FREE.value:
            expires_at = None
            auto_renew = False
        elif clean_code == SubscriptionPlanCode.PRO_MONTHLY.value:
            expires_at = now + timedelta(days=30)
            auto_renew = True
        elif clean_code == SubscriptionPlanCode.PRO_YEARLY.value:
            expires_at = now + timedelta(days=365)
            auto_renew = True
        else:
            expires_at = now + timedelta(days=30)
            auto_renew = True

        # Deactivate existing active subscriptions
        self.repo.deactivate_user_active_subscriptions(db, current_user.id)

        # Create new active subscription
        new_sub = UserSubscription(
            user_id=current_user.id,
            plan_id=plan.id,
            status=SubscriptionStatus.ACTIVE.value,
            starts_at=now,
            expires_at=expires_at,
            auto_renew=auto_renew,
        )
        created_sub = self.repo.create_user_subscription(db, new_sub)

        # If paid plan, generate financial transaction record
        if float(plan.price) > 0:
            random_suffix = uuid.uuid4().hex[:6].upper()
            txn_ref = f"TXN-{int(time.time())}-{random_suffix}"
            txn = PaymentTransaction(
                transaction_ref=txn_ref,
                user_id=current_user.id,
                subscription_id=created_sub.id,
                amount=plan.price,
                currency="BDT",
                gateway=request.payment_gateway or "SIMULATED",
                status=PaymentStatus.SUCCESS.value,
                raw_response={
                    "plan_id": plan.id,
                    "plan_code": plan.code,
                    "plan_name": f"{plan.name} Plan",
                    "payment_method": request.payment_method or "bKash Auto-Debit",
                    "status": "APPROVED",
                },
                verified_at=now,
            )
            self.repo.create_transaction(db, txn)

        return self._to_user_subscription_response(created_sub)

    def check_has_active_pro(self, db: Session, user_id: int) -> bool:
        """Helper to verify if a user has an active Pro entitlement."""
        active_sub = self.repo.get_active_subscription(db, user_id)
        if not active_sub or not active_sub.plan:
            return False

        if active_sub.plan.code not in [SubscriptionPlanCode.PRO_MONTHLY.value, SubscriptionPlanCode.PRO_YEARLY.value]:
            return False

        if active_sub.status != SubscriptionStatus.ACTIVE.value:
            return False

        now = datetime.now(timezone.utc)
        expires = _ensure_utc(active_sub.expires_at)
        if expires and expires < now:
            return False

        return True

    def get_user_entitlements(self, db: Session, current_user: User) -> EntitlementsResponse:
        """Get granular entitlement permissions for current user."""
        self.repo.ensure_seed_plans(db)

        is_pro = self.check_has_active_pro(db, current_user.id)
        if current_user.role == UserRole.ADMIN:
            is_pro = True

        active_sub = self.repo.get_active_subscription(db, current_user.id)
        plan_code = "FREE"
        plan_name = "Free"
        expires_at = None
        status_val = "ACTIVE"

        if active_sub and active_sub.plan:
            plan_code = active_sub.plan.code
            plan_name = active_sub.plan.name
            expires_at = active_sub.expires_at
            status_val = active_sub.status

        return EntitlementsResponse(
            plan_code=plan_code,
            plan_name=plan_name,
            is_pro=is_pro,
            can_access_premium_mock_tests=is_pro,
            can_access_advanced_analytics=is_pro,
            expires_at=expires_at,
            status=status_val,
        )

    def cancel_my_subscription(self, db: Session, current_user: User) -> UserSubscriptionResponse:
        """Cancel active paid subscription and downgrade to Free tier."""
        self.repo.ensure_seed_plans(db)
        self.repo.deactivate_user_active_subscriptions(db, current_user.id)
        return self.get_my_subscription(db, current_user)

    def get_my_transactions(self, db: Session, current_user: User) -> List[PaymentTransactionResponse]:
        """Fetch user-restricted transaction history."""
        txns = self.repo.get_user_transactions(db, current_user.id)
        return [self._to_transaction_response(t) for t in txns]

    def verify_transaction(
        self, db: Session, current_user: User, request: TransactionVerifyRequest
    ) -> PaymentTransactionResponse:
        """Idempotent transaction verification."""
        txn = self.repo.get_transaction_by_ref(db, request.transaction_ref)
        if not txn:
            raise NotFoundException(f"Transaction ref '{request.transaction_ref}' not found")

        # Cross-user authorization guard: only owner or administrator can verify
        if txn.user_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise ForbiddenException("You do not have permission to verify this transaction")

        # Idempotent check: if already successful and verified, return existing record
        if txn.status == PaymentStatus.SUCCESS.value and txn.verified_at is not None:
            return self._to_transaction_response(txn)

        now = datetime.now(timezone.utc)
        txn.status = request.status or PaymentStatus.SUCCESS.value
        txn.verified_at = now
        txn.verified_by = current_user.id

        if txn.status == PaymentStatus.SUCCESS.value and txn.subscription:
            txn.subscription.status = SubscriptionStatus.ACTIVE.value

        db.commit()
        db.refresh(txn)

        return self._to_transaction_response(txn)

    def get_admin_transactions(
        self, db: Session, current_user: User, limit: int = 50, offset: int = 0
    ) -> List[PaymentTransactionResponse]:
        """Platform-wide transaction audit log for Admins."""
        if current_user.role != UserRole.ADMIN:
            raise ForbiddenException("Administrator role required to access global transactions")

        txns = self.repo.get_all_transactions(db, limit=limit, offset=offset)
        return [self._to_transaction_response(t) for t in txns]

    def get_invoice(self, db: Session, current_user: User, transaction_id: int) -> InvoiceResponse:
        """Download or view official tax invoice for a transaction."""
        txn = self.repo.get_transaction_by_id(db, transaction_id)
        if not txn:
            raise NotFoundException("Transaction not found")

        if txn.user_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise ForbiddenException("You do not have permission to view this invoice")

        user = txn.user or current_user
        user_name = f"{user.first_name} {user.last_name}".strip()

        plan_name = "Pro Subscription"
        if txn.subscription and txn.subscription.plan:
            plan_name = f"{txn.subscription.plan.name} Plan"
        elif txn.raw_response and isinstance(txn.raw_response, dict):
            plan_name = txn.raw_response.get("plan_name", "Pro Subscription")

        payment_method = "bKash Auto-Debit"
        if txn.raw_response and isinstance(txn.raw_response, dict):
            payment_method = txn.raw_response.get("payment_method", "bKash Auto-Debit")

        return InvoiceResponse(
            invoice_number=f"INV-{txn.id:06d}",
            transaction_ref=txn.transaction_ref,
            user_name=user_name,
            user_email=user.email,
            date=txn.created_at,
            plan_name=plan_name,
            amount=float(txn.amount),
            currency=txn.currency,
            payment_method=payment_method,
            status="PAID" if txn.status == PaymentStatus.SUCCESS.value else txn.status,
        )
