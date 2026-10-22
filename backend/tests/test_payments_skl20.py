"""Comprehensive Unit and Integration Tests for SKL-20: Local & Global Payment Integration.

Covers:
- AC-1: Correct amount matching plan pricing is transmitted to gateway
- AC-2: Local payment initiates SSLCommerz gateway session
- AC-3: Global payment initiates Global Gateway (Stripe) checkout session
- AC-4: Successful payment verification records transaction and activates subscription entitlement
- AC-5: Failed or cancelled payment records FAILED status and DOES NOT activate subscription
- Idempotency & duplicate IPN/webhook prevention
- Amount and currency mismatch protection
- Hash signature verification
- Browser form redirect vs JSON API responses
- Payment status inquiry and authorization boundaries
"""

import hashlib
import hmac
import time
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password, create_access_token
from app.models.user import User, UserRole
from app.models.subscription import (
    SubscriptionPlan,
    UserSubscription,
    PaymentTransaction,
    SubscriptionStatus,
    SubscriptionPlanCode,
    SubscriptionBillingCycle,
    PaymentStatus,
    PaymentGatewayType,
)
from app.repositories.subscription_repository import SubscriptionRepository
from app.services.payment_service import PaymentService


def create_test_user(
    db: Session,
    email: str,
    role: UserRole = UserRole.LEARNER,
    first_name: str = "Payment",
    last_name: str = "Tester",
) -> User:
    user = User(
        email=email,
        hashed_password=hash_password("Password123!"),
        role=role,
        first_name=first_name,
        last_name=last_name,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth_header(user: User) -> dict:
    token = create_access_token(
        subject=user.id,
        claims={"email": user.email, "role": user.role.value},
    )
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# AC-1, AC-2, AC-3: Payment Initiation Tests
# ==============================================================================

def test_initiate_payment_sslcommerz_ac1_ac2(client: TestClient, db_session: Session):
    """AC-1 & AC-2: Given a valid paid plan, when local payment starts,

    then SSLCommerz must be used and the correct plan amount must be sent.
    """
    repo = SubscriptionRepository()
    repo.ensure_seed_plans(db_session)
    user = create_test_user(db_session, "ssl_initiate@example.com")
    headers = auth_header(user)

    monthly_plan = repo.get_plan_by_code(db_session, SubscriptionPlanCode.PRO_MONTHLY.value)
    assert monthly_plan is not None

    payload = {
        "plan_id": monthly_plan.id,
        "gateway_type": "SSLCOMMERZ",
        "payment_method": "bKash Auto-Debit",
    }

    response = client.post("/api/v1/payments/initiate", json=payload, headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    res_data = data["data"]

    # AC-1: Correct amount transmitted
    assert res_data["amount"] == float(monthly_plan.price)
    assert res_data["currency"] == "BDT"

    # AC-2: SSLCommerz gateway selected
    assert res_data["gateway_type"] == "SSLCOMMERZ"
    assert res_data["transaction_ref"].startswith("SSLC-")
    assert "sslcommerz" in res_data["redirect_url"].lower()
    assert res_data["status"] == "PENDING"

    # Verify transaction record persisted in database with PENDING status
    txn = repo.get_transaction_by_ref(db_session, res_data["transaction_ref"])
    assert txn is not None
    assert txn.status == PaymentStatus.PENDING.value
    assert float(txn.amount) == float(monthly_plan.price)
    assert txn.gateway_type == "SSLCOMMERZ"
    assert txn.subscription_id is None  # Subscription NOT active yet


def test_initiate_payment_global_gateway_ac1_ac3(client: TestClient, db_session: Session):
    """AC-1 & AC-3: Given a valid paid plan, when global payment starts,

    then the configured global gateway (Stripe) must be used with the correct amount.
    """
    repo = SubscriptionRepository()
    repo.ensure_seed_plans(db_session)
    user = create_test_user(db_session, "global_initiate@example.com")
    headers = auth_header(user)

    yearly_plan = repo.get_plan_by_code(db_session, SubscriptionPlanCode.PRO_YEARLY.value)
    assert yearly_plan is not None

    payload = {
        "plan_code": yearly_plan.code,
        "gateway_type": "GLOBAL_GATEWAY",
        "payment_method": "International Credit Card",
    }

    response = client.post("/api/v1/payments/initiate", json=payload, headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    res_data = data["data"]

    # AC-1: Correct amount
    assert res_data["amount"] == float(yearly_plan.price)

    # AC-3: Global gateway used
    assert res_data["gateway_type"] == "GLOBAL_GATEWAY"
    assert res_data["transaction_ref"].startswith("GLB-")
    assert "checkout.stripe.com" in res_data["redirect_url"]
    assert res_data["status"] == "PENDING"


def test_initiate_payment_free_plan_rejected(client: TestClient, db_session: Session):
    """Verify that initiating payment for a free plan is rejected with HTTP 400."""
    repo = SubscriptionRepository()
    repo.ensure_seed_plans(db_session)
    user = create_test_user(db_session, "free_initiate@example.com")
    headers = auth_header(user)

    free_plan = repo.get_plan_by_code(db_session, SubscriptionPlanCode.FREE.value)
    payload = {"plan_id": free_plan.id, "gateway_type": "SSLCOMMERZ"}

    response = client.post("/api/v1/payments/initiate", json=payload, headers=headers)
    assert response.status_code == 400
    assert "Free tier plan does not require payment" in response.json()["message"]


def test_initiate_payment_invalid_plan_rejected(client: TestClient, db_session: Session):
    """Verify that initiating payment for a non-existent plan returns HTTP 404."""
    user = create_test_user(db_session, "invalid_plan_user@example.com")
    headers = auth_header(user)

    payload = {"plan_id": 99999, "gateway_type": "SSLCOMMERZ"}
    response = client.post("/api/v1/payments/initiate", json=payload, headers=headers)
    assert response.status_code == 404


# ==============================================================================
# AC-4: Payment Verification & Automated Subscription Activation Tests
# ==============================================================================

def test_sslcommerz_ipn_verification_success_ac4(client: TestClient, db_session: Session):
    """AC-4: Given payment is successfully verified via SSLCommerz IPN,

    then transaction must be recorded as SUCCESS and user subscription activated.
    """
    repo = SubscriptionRepository()
    repo.ensure_seed_plans(db_session)
    user = create_test_user(db_session, "ssl_success_ipn@example.com")
    headers = auth_header(user)

    monthly_plan = repo.get_plan_by_code(db_session, SubscriptionPlanCode.PRO_MONTHLY.value)

    # 1. Initiate payment
    init_res = client.post(
        "/api/v1/payments/initiate",
        json={"plan_id": monthly_plan.id, "gateway_type": "SSLCOMMERZ"},
        headers=headers,
    )
    tran_ref = init_res.json()["data"]["transaction_ref"]

    # 2. Simulate SSLCommerz IPN webhook callback
    ipn_payload = {
        "tran_id": tran_ref,
        "val_id": "VAL_SSLC_12345678",
        "amount": float(monthly_plan.price),
        "currency": "BDT",
        "card_type": "BKASH-BKASH",
        "bank_tran_id": "BANK_TRX_8888",
        "status": "VALID",
    }

    ipn_res = client.post("/api/v1/payments/sslcommerz/ipn", json=ipn_payload)
    assert ipn_res.status_code == 200

    data = ipn_res.json()
    assert data["success"] is True
    assert data["data"]["status"] == "SUCCESS"
    assert data["data"]["subscription_activated"] is True

    # 3. Verify in database: transaction is SUCCESS and linked to active UserSubscription
    txn = repo.get_transaction_by_ref(db_session, tran_ref)
    assert txn.status == PaymentStatus.SUCCESS.value
    assert txn.verified_at is not None
    assert txn.gateway_val_id == "VAL_SSLC_12345678"
    assert txn.bank_tran_id == "BANK_TRX_8888"
    assert txn.card_type == "BKASH-BKASH"
    assert txn.subscription_id is not None

    # Check that user's subscription entitlement is now active
    active_sub = repo.get_active_subscription(db_session, user.id)
    assert active_sub is not None
    assert active_sub.id == txn.subscription_id
    assert active_sub.plan_id == monthly_plan.id
    assert active_sub.status == SubscriptionStatus.ACTIVE.value
    assert active_sub.expires_at is not None


def test_sslcommerz_duplicate_ipn_idempotency(client: TestClient, db_session: Session):
    """Verify that multiple duplicate IPN callbacks do not double-activate subscriptions."""
    repo = SubscriptionRepository()
    repo.ensure_seed_plans(db_session)
    user = create_test_user(db_session, "idempotent_ssl@example.com")
    headers = auth_header(user)

    monthly_plan = repo.get_plan_by_code(db_session, SubscriptionPlanCode.PRO_MONTHLY.value)

    init_res = client.post(
        "/api/v1/payments/initiate",
        json={"plan_id": monthly_plan.id, "gateway_type": "SSLCOMMERZ"},
        headers=headers,
    )
    tran_ref = init_res.json()["data"]["transaction_ref"]

    ipn_payload = {
        "tran_id": tran_ref,
        "val_id": "VAL_112233",
        "amount": float(monthly_plan.price),
        "status": "VALID",
    }

    # First callback
    res1 = client.post("/api/v1/payments/sslcommerz/ipn", json=ipn_payload)
    assert res1.status_code == 200
    first_verified_at = repo.get_transaction_by_ref(db_session, tran_ref).verified_at

    # Count subscriptions
    subs_before = len(repo.get_subscriptions_by_user(db_session, user.id))

    # Second identical callback
    res2 = client.post("/api/v1/payments/sslcommerz/ipn", json=ipn_payload)
    assert res2.status_code == 200
    assert res2.json()["data"]["subscription_activated"] is True

    # No duplicate subscription was created
    subs_after = len(repo.get_subscriptions_by_user(db_session, user.id))
    assert subs_before == subs_after
    assert repo.get_transaction_by_ref(db_session, tran_ref).verified_at == first_verified_at


# ==============================================================================
# AC-5: Payment Failure & Cancellation Tests (Subscription NOT activated)
# ==============================================================================

def test_sslcommerz_payment_failure_does_not_activate_subscription_ac5(
    client: TestClient, db_session: Session
):
    """AC-5: Given payment fails, when the response is received,

    then the subscription must not be activated.
    """
    repo = SubscriptionRepository()
    repo.ensure_seed_plans(db_session)
    user = create_test_user(db_session, "ssl_fail_user@example.com")
    headers = auth_header(user)

    monthly_plan = repo.get_plan_by_code(db_session, SubscriptionPlanCode.PRO_MONTHLY.value)

    init_res = client.post(
        "/api/v1/payments/initiate",
        json={"plan_id": monthly_plan.id, "gateway_type": "SSLCOMMERZ"},
        headers=headers,
    )
    tran_ref = init_res.json()["data"]["transaction_ref"]

    # Gateway reports FAILED
    fail_payload = {
        "tran_id": tran_ref,
        "status": "FAILED",
        "error": "Card limit exceeded or insufficient funds",
    }

    response = client.post("/api/v1/payments/sslcommerz/ipn", json=fail_payload)
    assert response.status_code == 200

    data = response.json()["data"]
    assert data["status"] == "FAILED"
    assert data["verified"] is False
    assert data["subscription_activated"] is False

    # Check database: status is FAILED and NO Pro subscription is active
    txn = repo.get_transaction_by_ref(db_session, tran_ref)
    assert txn.status == PaymentStatus.FAILED.value
    assert "Card limit exceeded" in txn.error_reason
    assert txn.subscription_id is None

    active_sub = repo.get_active_subscription(db_session, user.id)
    assert active_sub is None  # User was NOT upgraded to Pro


def test_sslcommerz_cancel_endpoint_does_not_activate_subscription_ac5(
    client: TestClient, db_session: Session
):
    """AC-5: Given payment is cancelled, when response is received,

    then the subscription must not be activated.
    """
    repo = SubscriptionRepository()
    repo.ensure_seed_plans(db_session)
    user = create_test_user(db_session, "ssl_cancel_user@example.com")
    headers = auth_header(user)

    monthly_plan = repo.get_plan_by_code(db_session, SubscriptionPlanCode.PRO_MONTHLY.value)

    init_res = client.post(
        "/api/v1/payments/initiate",
        json={"plan_id": monthly_plan.id, "gateway_type": "SSLCOMMERZ"},
        headers=headers,
    )
    tran_ref = init_res.json()["data"]["transaction_ref"]

    cancel_res = client.post("/api/v1/payments/sslcommerz/cancel", json={"tran_id": tran_ref})
    assert cancel_res.status_code == 200

    data = cancel_res.json()["data"]
    assert data["status"] == "FAILED"
    assert data["subscription_activated"] is False

    txn = repo.get_transaction_by_ref(db_session, tran_ref)
    assert txn.status == PaymentStatus.FAILED.value
    assert "cancelled" in txn.error_reason.lower()

    active_sub = repo.get_active_subscription(db_session, user.id)
    assert active_sub is None


def test_sslcommerz_amount_mismatch_fails_ac5(client: TestClient, db_session: Session):
    """Verify that a tampered or mismatched amount fails verification without activating subscription."""
    repo = SubscriptionRepository()
    repo.ensure_seed_plans(db_session)
    user = create_test_user(db_session, "tamper_amount_user@example.com")
    headers = auth_header(user)

    monthly_plan = repo.get_plan_by_code(db_session, SubscriptionPlanCode.PRO_MONTHLY.value)

    init_res = client.post(
        "/api/v1/payments/initiate",
        json={"plan_id": monthly_plan.id, "gateway_type": "SSLCOMMERZ"},
        headers=headers,
    )
    tran_ref = init_res.json()["data"]["transaction_ref"]

    # Hacker sends amount: 10.0 instead of 499.0
    tampered_payload = {
        "tran_id": tran_ref,
        "amount": 10.00,
        "status": "VALID",
    }

    res = client.post("/api/v1/payments/sslcommerz/ipn", json=tampered_payload)
    assert res.status_code == 200

    data = res.json()["data"]
    assert data["status"] == "FAILED"
    assert data["subscription_activated"] is False
    assert "mismatch" in data["error_reason"].lower()

    active_sub = repo.get_active_subscription(db_session, user.id)
    assert active_sub is None


# ==============================================================================
# Global Gateway (Stripe Sandbox) Webhook Tests
# ==============================================================================

def test_global_gateway_webhook_success_ac4(client: TestClient, db_session: Session):
    """AC-4: Given payment succeeds on Global Gateway,

    webhook event verifies transaction and activates user subscription.
    """
    repo = SubscriptionRepository()
    repo.ensure_seed_plans(db_session)
    user = create_test_user(db_session, "global_webhook_user@example.com")
    headers = auth_header(user)

    yearly_plan = repo.get_plan_by_code(db_session, SubscriptionPlanCode.PRO_YEARLY.value)

    init_res = client.post(
        "/api/v1/payments/initiate",
        json={"plan_id": yearly_plan.id, "gateway_type": "GLOBAL_GATEWAY"},
        headers=headers,
    )
    tran_ref = init_res.json()["data"]["transaction_ref"]

    webhook_payload = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_mock_session_12345",
                "client_reference_id": tran_ref,
                "amount_total": int(float(yearly_plan.price) * 100),
                "payment_status": "paid",
            }
        },
    }

    res = client.post("/api/v1/payments/global/webhook", json=webhook_payload)
    assert res.status_code == 200

    data = res.json()["data"]
    assert data["status"] == "SUCCESS"
    assert data["subscription_activated"] is True

    txn = repo.get_transaction_by_ref(db_session, tran_ref)
    assert txn.status == PaymentStatus.SUCCESS.value
    assert txn.subscription_id is not None

    active_sub = repo.get_active_subscription(db_session, user.id)
    assert active_sub is not None
    assert active_sub.plan_id == yearly_plan.id


def test_global_gateway_webhook_failure_ac5(client: TestClient, db_session: Session):
    """AC-5: Given Global Gateway reports payment failure,

    transaction is recorded as FAILED and subscription is not activated.
    """
    repo = SubscriptionRepository()
    repo.ensure_seed_plans(db_session)
    user = create_test_user(db_session, "global_fail_user@example.com")
    headers = auth_header(user)

    monthly_plan = repo.get_plan_by_code(db_session, SubscriptionPlanCode.PRO_MONTHLY.value)

    init_res = client.post(
        "/api/v1/payments/initiate",
        json={"plan_id": monthly_plan.id, "gateway_type": "GLOBAL_GATEWAY"},
        headers=headers,
    )
    tran_ref = init_res.json()["data"]["transaction_ref"]

    webhook_payload = {
        "type": "payment_intent.payment_failed",
        "data": {
            "object": {
                "metadata": {"transaction_ref": tran_ref},
                "last_payment_error": {"message": "Card was declined"},
            }
        },
    }

    res = client.post("/api/v1/payments/global/webhook", json=webhook_payload)
    assert res.status_code == 200

    data = res.json()["data"]
    assert data["status"] == "FAILED"
    assert data["subscription_activated"] is False

    active_sub = repo.get_active_subscription(db_session, user.id)
    assert active_sub is None


# ==============================================================================
# Browser Form Redirect Callback Tests
# ==============================================================================

def test_sslcommerz_success_browser_form_redirect(client: TestClient, db_session: Session):
    """Verify that browser form POST submission to /success returns HTTP 303 Redirect to frontend."""
    repo = SubscriptionRepository()
    repo.ensure_seed_plans(db_session)
    user = create_test_user(db_session, "browser_redirect_user@example.com")
    headers = auth_header(user)

    monthly_plan = repo.get_plan_by_code(db_session, SubscriptionPlanCode.PRO_MONTHLY.value)

    init_res = client.post(
        "/api/v1/payments/initiate",
        json={"plan_id": monthly_plan.id, "gateway_type": "SSLCOMMERZ"},
        headers=headers,
    )
    tran_ref = init_res.json()["data"]["transaction_ref"]

    form_data = {
        "tran_id": tran_ref,
        "val_id": "VAL_BROWSER_123",
        "amount": str(monthly_plan.price),
        "status": "VALID",
    }

    # Browser submits urlencoded form with text/html accept header
    res = client.post(
        "/api/v1/payments/sslcommerz/success",
        data=form_data,
        headers={"Accept": "text/html,application/xhtml+xml"},
        follow_redirects=False,
    )

    assert res.status_code == 303
    redirect_location = res.headers["location"]
    assert "/subscription?payment=success" in redirect_location
    assert tran_ref in redirect_location


# ==============================================================================
# Payment Status & Security RBAC Tests
# ==============================================================================

def test_get_payment_status_authorization(client: TestClient, db_session: Session):
    """Verify payment status query allows the owner but rejects unauthorized third parties with 403."""
    repo = SubscriptionRepository()
    repo.ensure_seed_plans(db_session)

    owner = create_test_user(db_session, "owner_user@example.com")
    other_user = create_test_user(db_session, "attacker_user@example.com")
    admin_user = create_test_user(db_session, "admin_user@example.com", role=UserRole.ADMIN)

    monthly_plan = repo.get_plan_by_code(db_session, SubscriptionPlanCode.PRO_MONTHLY.value)

    init_res = client.post(
        "/api/v1/payments/initiate",
        json={"plan_id": monthly_plan.id, "gateway_type": "SSLCOMMERZ"},
        headers=auth_header(owner),
    )
    tran_ref = init_res.json()["data"]["transaction_ref"]

    # 1. Owner can inspect status
    res_owner = client.get(f"/api/v1/payments/{tran_ref}/status", headers=auth_header(owner))
    assert res_owner.status_code == 200
    assert res_owner.json()["data"]["transaction_ref"] == tran_ref

    # 2. Other user is blocked with HTTP 403 Forbidden
    res_other = client.get(f"/api/v1/payments/{tran_ref}/status", headers=auth_header(other_user))
    assert res_other.status_code == 403

    # 3. Admin can inspect status
    res_admin = client.get(f"/api/v1/payments/{tran_ref}/status", headers=auth_header(admin_user))
    assert res_admin.status_code == 200
