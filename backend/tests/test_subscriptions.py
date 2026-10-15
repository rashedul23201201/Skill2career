import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.mock_test import MockTest, TestQuestion, MockTestStatus
from app.models.subscription import (
    SubscriptionPlan,
    UserSubscription,
    PaymentTransaction,
    SubscriptionStatus,
    SubscriptionPlanCode,
)
from app.core.security import hash_password, create_access_token


def create_user(
    db: Session,
    email: str,
    role: UserRole = UserRole.LEARNER,
    first_name: str = "Test",
    last_name: str = "User",
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


def create_sample_mock_test(db: Session, instructor: User, is_premium: bool = False) -> MockTest:
    test = MockTest(
        instructor_id=instructor.id,
        title="Premium Security Engineering Assessment" if is_premium else "Basic Python Test",
        description="Assessing high-security concepts and architectures.",
        category="Security",
        duration_minutes=45,
        passing_score=60,
        total_questions=1,
        status=MockTestStatus.PUBLISHED.value,
        is_published=True,
        is_premium=is_premium,
    )
    db.add(test)
    db.commit()
    db.refresh(test)

    q = TestQuestion(
        test_id=test.id,
        question_text="What does symmetric encryption utilize?",
        options=["A single shared key", "Public and private key pairs", "Zero knowledge proofs", "Hash only"],
        correct_option="A",
        marks=5,
        order_index=1,
    )
    db.add(q)
    db.commit()
    db.refresh(test)
    return test


def test_get_subscription_plans(client: TestClient, db_session: Session):
    """Test retrieving public subscription plans with Free, Pro Monthly, and Pro Yearly tiers."""
    response = client.get("/api/v1/subscriptions/plans")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    plans = data["data"]
    assert len(plans) >= 3

    codes = [p["code"] for p in plans]
    assert "FREE" in codes
    assert "PRO_MONTHLY" in codes
    assert "PRO_YEARLY" in codes

    monthly = next(p for p in plans if p["code"] == "PRO_MONTHLY")
    assert monthly["price"] == 499.00
    assert "Mock tests" in monthly["features"]

    yearly = next(p for p in plans if p["code"] == "PRO_YEARLY")
    assert yearly["price"] == 4999.00


def test_get_my_subscription_defaults_to_free(client: TestClient, db_session: Session):
    """Test that a new user without an existing subscription defaults cleanly to Free."""
    user = create_user(db_session, "new_sub_user@test.com")
    headers = auth_header(user)

    response = client.get("/api/v1/subscriptions/my-subscription", headers=headers)
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    sub = res["data"]
    assert sub["user_id"] == user.id
    assert sub["plan"]["code"] == "FREE"
    assert sub["status"] == "ACTIVE"
    assert sub["is_pro"] is False
    assert sub["expires_at"] is None


def test_select_plan_pro_monthly_and_yearly(client: TestClient, db_session: Session):
    """Test activating Pro Monthly and Pro Yearly plans, verifying expiration and transaction ledger."""
    user = create_user(db_session, "upgrade_user@test.com")
    headers = auth_header(user)

    # 1. Upgrade to PRO_MONTHLY
    payload = {
        "plan_code": "PRO_MONTHLY",
        "payment_gateway": "SIMULATED",
        "payment_method": "bKash Auto-Debit",
    }
    resp1 = client.post("/api/v1/subscriptions/select-plan", json=payload, headers=headers)
    assert resp1.status_code == 200
    data1 = resp1.json()["data"]
    assert data1["plan"]["code"] == "PRO_MONTHLY"
    assert data1["is_pro"] is True
    assert data1["expires_at"] is not None

    # Check transaction ledger was created
    tx_resp = client.get("/api/v1/transactions/my-history", headers=headers)
    assert tx_resp.status_code == 200
    tx_list = tx_resp.json()["data"]
    assert len(tx_list) == 1
    assert tx_list[0]["amount"] == 499.00
    assert tx_list[0]["status"] == "SUCCESS"

    # 2. Upgrade to PRO_YEARLY
    payload_yr = {
        "plan_code": "PRO_YEARLY",
        "payment_gateway": "SIMULATED",
    }
    resp2 = client.post("/api/v1/subscriptions/select-plan", json=payload_yr, headers=headers)
    assert resp2.status_code == 200
    data2 = resp2.json()["data"]
    assert data2["plan"]["code"] == "PRO_YEARLY"
    assert data2["is_pro"] is True

    # Check second transaction exists
    tx_resp2 = client.get("/api/v1/transactions/my-history", headers=headers)
    tx_list2 = tx_resp2.json()["data"]
    assert len(tx_list2) == 2


def test_premium_mock_test_entitlement_gating(client: TestClient, db_session: Session):
    """Test that premium mock tests reject Free learners with HTTP 403, and grant access after Pro upgrade."""
    instructor = create_user(db_session, "inst_premium@test.com", role=UserRole.INSTRUCTOR)
    learner = create_user(db_session, "learner_premium@test.com", role=UserRole.LEARNER)

    regular_test = create_sample_mock_test(db_session, instructor, is_premium=False)
    premium_test = create_sample_mock_test(db_session, instructor, is_premium=True)

    learner_headers = auth_header(learner)

    # 1. Non-premium test should allow Free learner
    resp_reg = client.post(f"/api/v1/mock-tests/{regular_test.id}/attempts", headers=learner_headers)
    assert resp_reg.status_code in [200, 201]
    assert resp_reg.json()["success"] is True

    # 2. Premium test should reject Free learner with 403 Forbidden
    resp_prem = client.post(f"/api/v1/mock-tests/{premium_test.id}/attempts", headers=learner_headers)
    assert resp_prem.status_code == 403
    assert "Premium subscription required" in resp_prem.json()["message"]

    # 3. Upgrade learner to PRO_MONTHLY
    upgrade_res = client.post(
        "/api/v1/subscriptions/select-plan",
        json={"plan_code": "PRO_MONTHLY"},
        headers=learner_headers,
    )
    assert upgrade_res.status_code == 200

    # 4. Premium test now succeeds!
    resp_prem_after = client.post(f"/api/v1/mock-tests/{premium_test.id}/attempts", headers=learner_headers)
    assert resp_prem_after.status_code in [200, 201]
    assert resp_prem_after.json()["success"] is True


def test_advanced_analytics_entitlement_gating(client: TestClient, db_session: Session):
    """Test that advanced analytics endpoint enforces Pro entitlement."""
    learner = create_user(db_session, "analytics_user@test.com", role=UserRole.LEARNER)
    headers = auth_header(learner)

    # 1. Free learner rejected from advanced analytics overview
    resp_denied = client.get("/api/v1/subscriptions/analytics/advanced", headers=headers)
    assert resp_denied.status_code == 403

    # Check entitlements API reports is_pro=False
    ent_resp = client.get("/api/v1/subscriptions/entitlements", headers=headers)
    assert ent_resp.status_code == 200
    assert ent_resp.json()["data"]["is_pro"] is False
    assert ent_resp.json()["data"]["can_access_advanced_analytics"] is False

    # 2. Upgrade to Pro
    client.post("/api/v1/subscriptions/select-plan", json={"plan_code": "PRO_MONTHLY"}, headers=headers)

    # 3. Entitlements API reports is_pro=True
    ent_resp2 = client.get("/api/v1/subscriptions/entitlements", headers=headers)
    assert ent_resp2.status_code == 200
    assert ent_resp2.json()["data"]["is_pro"] is True
    assert ent_resp2.json()["data"]["can_access_advanced_analytics"] is True

    # 4. Advanced analytics allowed
    resp_allowed = client.get("/api/v1/subscriptions/analytics/advanced", headers=headers)
    assert resp_allowed.status_code == 200
    assert resp_allowed.json()["data"]["pro_features_unlocked"] is True


def test_cancel_subscription_downgrades_to_free(client: TestClient, db_session: Session):
    """Test cancelling subscription reverts user to Free tier."""
    user = create_user(db_session, "cancel_sub_user@test.com")
    headers = auth_header(user)

    # Subscribe to Pro
    client.post("/api/v1/subscriptions/select-plan", json={"plan_code": "PRO_MONTHLY"}, headers=headers)

    # Cancel subscription
    cancel_resp = client.post("/api/v1/subscriptions/cancel", json={"reason": "Completed preparation"}, headers=headers)
    assert cancel_resp.status_code == 200
    sub = cancel_resp.json()["data"]
    assert sub["plan"]["code"] == "FREE"
    assert sub["is_pro"] is False


def test_transaction_idempotent_verification_and_invoice(client: TestClient, db_session: Session):
    """Test idempotent transaction verification and downloading tax invoice."""
    user = create_user(db_session, "invoice_user@test.com")
    headers = auth_header(user)

    # Select plan to generate a transaction
    client.post("/api/v1/subscriptions/select-plan", json={"plan_code": "PRO_MONTHLY"}, headers=headers)

    # Get transaction ref
    tx_list = client.get("/api/v1/transactions/my-history", headers=headers).json()["data"]
    assert len(tx_list) > 0
    txn_ref = tx_list[0]["transaction_ref"]
    txn_id = tx_list[0]["id"]

    # Verify idempotency
    v_resp1 = client.post("/api/v1/transactions/verify", json={"transaction_ref": txn_ref}, headers=headers)
    assert v_resp1.status_code == 200
    assert v_resp1.json()["data"]["status"] == "SUCCESS"

    v_resp2 = client.post("/api/v1/transactions/verify", json={"transaction_ref": txn_ref}, headers=headers)
    assert v_resp2.status_code == 200
    assert v_resp2.json()["data"]["transaction_ref"] == txn_ref

    # Get tax invoice
    inv_resp = client.get(f"/api/v1/transactions/{txn_id}/invoice", headers=headers)
    assert inv_resp.status_code == 200
    inv = inv_resp.json()["data"]
    assert inv["transaction_ref"] == txn_ref
    assert inv["amount"] == 499.00
    assert inv["status"] == "PAID"


def test_admin_transaction_audit_rbac(client: TestClient, db_session: Session):
    """Test platform-wide transaction audit log access control."""
    admin = create_user(db_session, "admin_audit_user@test.com", role=UserRole.ADMIN)
    learner = create_user(db_session, "learner_audit_user@test.com", role=UserRole.LEARNER)

    # Learner should be forbidden (403)
    resp_learner = client.get("/api/v1/admin/transactions", headers=auth_header(learner))
    assert resp_learner.status_code == 403

    # Admin should succeed (200)
    resp_admin = client.get("/api/v1/admin/transactions", headers=auth_header(admin))
    assert resp_admin.status_code == 200
    assert resp_admin.json()["success"] is True
