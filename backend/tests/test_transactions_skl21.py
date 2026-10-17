"""Comprehensive Unit Tests for SKL-21: Transaction History & Verification.

Covers:
- Personal transaction history ledger (user-restricted)
- Cross-user security boundary enforcement
- Idempotent transaction verification & duplicate prevention
- Official tax invoice retrieval and RBAC
- Admin platform-wide transaction audit log with RBAC and pagination
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.subscription import (
    SubscriptionPlan,
    UserSubscription,
    PaymentTransaction,
    SubscriptionStatus,
    PaymentStatus,
)
from app.core.security import hash_password, create_access_token


def create_test_user(
    db: Session,
    email: str,
    role: UserRole = UserRole.LEARNER,
    first_name: str = "Transaction",
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


def test_get_my_transactions_empty(client: TestClient, db_session: Session):
    """Test that a new learner with no purchases returns an empty ledger with success=True."""
    user = create_test_user(db_session, "empty_tx_user@test.com")
    headers = auth_header(user)

    response = client.get("/api/v1/transactions/my-history", headers=headers)
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    assert res["data"] == []


def test_get_my_transactions_with_records(client: TestClient, db_session: Session):
    """Test that purchasing plans creates immutable transaction entries in the user's ledger."""
    user = create_test_user(db_session, "active_tx_user@test.com")
    headers = auth_header(user)

    # 1. Purchase Monthly Plan (৳499)
    resp1 = client.post(
        "/api/v1/subscriptions/select-plan",
        json={"plan_code": "PRO_MONTHLY", "payment_method": "bKash Auto-Debit"},
        headers=headers,
    )
    assert resp1.status_code == 200

    # 2. Purchase Yearly Plan (৳4,999)
    resp2 = client.post(
        "/api/v1/subscriptions/select-plan",
        json={"plan_code": "PRO_YEARLY", "payment_method": "Nagad Gateway"},
        headers=headers,
    )
    assert resp2.status_code == 200

    # Retrieve history
    history_resp = client.get("/api/v1/transactions/my-history", headers=headers)
    assert history_resp.status_code == 200
    txns = history_resp.json()["data"]
    assert len(txns) == 2

    # Most recent first
    assert txns[0]["amount"] == 4999.00
    assert txns[0]["currency"] == "BDT"
    assert txns[0]["status"] == "SUCCESS"
    assert "TXN-" in txns[0]["transaction_ref"]

    assert txns[1]["amount"] == 499.00
    assert txns[1]["currency"] == "BDT"
    assert txns[1]["status"] == "SUCCESS"


def test_cross_user_transaction_isolation(client: TestClient, db_session: Session):
    """Verify that User A cannot see User B's transactions."""
    user_a = create_test_user(db_session, "isolation_a@test.com")
    user_b = create_test_user(db_session, "isolation_b@test.com")

    headers_a = auth_header(user_a)
    headers_b = auth_header(user_b)

    # User A buys Pro Monthly
    client.post(
        "/api/v1/subscriptions/select-plan",
        json={"plan_code": "PRO_MONTHLY"},
        headers=headers_a,
    )

    # User B should have 0 transactions in their history
    b_history = client.get("/api/v1/transactions/my-history", headers=headers_b).json()["data"]
    assert len(b_history) == 0

    # User A should have 1 transaction
    a_history = client.get("/api/v1/transactions/my-history", headers=headers_a).json()["data"]
    assert len(a_history) == 1
    assert a_history[0]["user_id"] == user_a.id


def test_idempotent_transaction_verification(client: TestClient, db_session: Session):
    """Verify that idempotent verification returns existing verified transaction without duplicate charges."""
    user = create_test_user(db_session, "idempotent_user@test.com")
    headers = auth_header(user)

    client.post(
        "/api/v1/subscriptions/select-plan",
        json={"plan_code": "PRO_MONTHLY"},
        headers=headers,
    )
    tx_list = client.get("/api/v1/transactions/my-history", headers=headers).json()["data"]
    txn_ref = tx_list[0]["transaction_ref"]

    # First verification
    res1 = client.post("/api/v1/transactions/verify", json={"transaction_ref": txn_ref}, headers=headers)
    assert res1.status_code == 200
    v1 = res1.json()["data"]
    assert v1["status"] == "SUCCESS"
    verified_at = v1["verified_at"]
    assert verified_at is not None

    # Duplicate verification attempt (idempotent)
    res2 = client.post("/api/v1/transactions/verify", json={"transaction_ref": txn_ref}, headers=headers)
    assert res2.status_code == 200
    v2 = res2.json()["data"]
    assert v2["transaction_ref"] == txn_ref
    assert v2["verified_at"] == verified_at

    # Check total count remains 1
    final_txns = client.get("/api/v1/transactions/my-history", headers=headers).json()["data"]
    assert len(final_txns) == 1


def test_transaction_verification_cross_user_forbidden(client: TestClient, db_session: Session):
    """Verify that Learner B cannot verify Learner A's transaction."""
    user_a = create_test_user(db_session, "owner_tx@test.com")
    user_b = create_test_user(db_session, "intruder_tx@test.com")

    headers_a = auth_header(user_a)
    headers_b = auth_header(user_b)

    client.post(
        "/api/v1/subscriptions/select-plan",
        json={"plan_code": "PRO_MONTHLY"},
        headers=headers_a,
    )
    tx_list = client.get("/api/v1/transactions/my-history", headers=headers_a).json()["data"]
    txn_ref = tx_list[0]["transaction_ref"]

    # User B attempts to verify User A's transaction
    res = client.post("/api/v1/transactions/verify", json={"transaction_ref": txn_ref}, headers=headers_b)
    assert res.status_code == 403
    assert "permission" in res.json()["message"].lower()


def test_transaction_verification_admin_allowed(client: TestClient, db_session: Session):
    """Verify that an Administrator can verify any user's transaction."""
    user = create_test_user(db_session, "learner_for_admin_verify@test.com")
    admin = create_test_user(db_session, "admin_verifier@test.com", role=UserRole.ADMIN)

    client.post(
        "/api/v1/subscriptions/select-plan",
        json={"plan_code": "PRO_MONTHLY"},
        headers=auth_header(user),
    )
    tx_list = client.get("/api/v1/transactions/my-history", headers=auth_header(user)).json()["data"]
    txn_ref = tx_list[0]["transaction_ref"]

    res = client.post(
        "/api/v1/transactions/verify",
        json={"transaction_ref": txn_ref},
        headers=auth_header(admin),
    )
    assert res.status_code == 200
    assert res.json()["data"]["transaction_ref"] == txn_ref


def test_transaction_verification_not_found(client: TestClient, db_session: Session):
    """Verify that non-existent transaction_ref returns 404."""
    user = create_test_user(db_session, "not_found_tx_user@test.com")
    res = client.post(
        "/api/v1/transactions/verify",
        json={"transaction_ref": "NON-EXISTENT-REF-999"},
        headers=auth_header(user),
    )
    assert res.status_code == 404


def test_get_invoice_success(client: TestClient, db_session: Session):
    """Test retrieving tax invoice with all mandatory receipt attributes."""
    user = create_test_user(
        db_session,
        "invoice_owner@test.com",
        first_name="Tahmid",
        last_name="Chowdhury",
    )
    headers = auth_header(user)

    client.post(
        "/api/v1/subscriptions/select-plan",
        json={"plan_code": "PRO_MONTHLY", "payment_method": "bKash Auto-Debit"},
        headers=headers,
    )
    txns = client.get("/api/v1/transactions/my-history", headers=headers).json()["data"]
    txn_id = txns[0]["id"]

    inv_res = client.get(f"/api/v1/transactions/{txn_id}/invoice", headers=headers)
    assert inv_res.status_code == 200
    inv = inv_res.json()["data"]
    assert inv["invoice_number"] == f"INV-{txn_id:06d}"
    assert inv["user_name"] == "Tahmid Chowdhury"
    assert inv["user_email"] == "invoice_owner@test.com"
    assert inv["amount"] == 499.00
    assert inv["currency"] == "BDT"
    assert inv["payment_method"] == "bKash Auto-Debit"
    assert inv["status"] == "PAID"
    assert inv["transaction_ref"] == txns[0]["transaction_ref"]


def test_get_invoice_cross_user_forbidden(client: TestClient, db_session: Session):
    """Test that User B is forbidden from viewing User A's tax invoice."""
    user_a = create_test_user(db_session, "inv_user_a@test.com")
    user_b = create_test_user(db_session, "inv_user_b@test.com")

    client.post(
        "/api/v1/subscriptions/select-plan",
        json={"plan_code": "PRO_MONTHLY"},
        headers=auth_header(user_a),
    )
    txns_a = client.get("/api/v1/transactions/my-history", headers=auth_header(user_a)).json()["data"]
    txn_id_a = txns_a[0]["id"]

    # User B requests User A's invoice
    res = client.get(f"/api/v1/transactions/{txn_id_a}/invoice", headers=auth_header(user_b))
    assert res.status_code == 403


def test_get_invoice_admin_allowed(client: TestClient, db_session: Session):
    """Test that Administrator can view any user's tax invoice."""
    user = create_test_user(db_session, "invoice_target@test.com")
    admin = create_test_user(db_session, "invoice_admin@test.com", role=UserRole.ADMIN)

    client.post(
        "/api/v1/subscriptions/select-plan",
        json={"plan_code": "PRO_MONTHLY"},
        headers=auth_header(user),
    )
    txns = client.get("/api/v1/transactions/my-history", headers=auth_header(user)).json()["data"]
    txn_id = txns[0]["id"]

    res = client.get(f"/api/v1/transactions/{txn_id}/invoice", headers=auth_header(admin))
    assert res.status_code == 200
    assert res.json()["data"]["transaction_ref"] == txns[0]["transaction_ref"]


def test_get_invoice_not_found(client: TestClient, db_session: Session):
    """Test that querying a non-existent transaction ID returns 404."""
    user = create_test_user(db_session, "inv_not_found@test.com")
    res = client.get("/api/v1/transactions/999999/invoice", headers=auth_header(user))
    assert res.status_code == 404


def test_admin_transactions_audit_rbac(client: TestClient, db_session: Session):
    """Test that only Admins can access platform-wide transaction audit log."""
    learner = create_test_user(db_session, "learner_forbidden@test.com", role=UserRole.LEARNER)
    instructor = create_test_user(db_session, "inst_forbidden@test.com", role=UserRole.INSTRUCTOR)
    admin = create_test_user(db_session, "admin_audit_boss@test.com", role=UserRole.ADMIN)

    # 1. Learner rejected (403)
    resp_l = client.get("/api/v1/admin/transactions", headers=auth_header(learner))
    assert resp_l.status_code == 403

    # 2. Instructor rejected (403)
    resp_i = client.get("/api/v1/admin/transactions", headers=auth_header(instructor))
    assert resp_i.status_code == 403

    # 3. Admin authorized (200)
    resp_a = client.get("/api/v1/admin/transactions", headers=auth_header(admin))
    assert resp_a.status_code == 200
    assert resp_a.json()["success"] is True


def test_admin_transactions_audit_pagination_and_data(client: TestClient, db_session: Session):
    """Test admin audit log pagination and user metadata inclusion."""
    admin = create_test_user(db_session, "audit_pagination_admin@test.com", role=UserRole.ADMIN)
    user = create_test_user(
        db_session,
        "paginated_buyer@test.com",
        first_name="Rahim",
        last_name="Uddin",
    )

    client.post(
        "/api/v1/subscriptions/select-plan",
        json={"plan_code": "PRO_MONTHLY"},
        headers=auth_header(user),
    )

    res = client.get("/api/v1/admin/transactions?limit=10&offset=0", headers=auth_header(admin))
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) >= 1

    # Verify user metadata is populated
    matching = next((t for t in data if t["user_id"] == user.id), None)
    assert matching is not None
    assert matching["user_email"] == "paginated_buyer@test.com"
    assert matching["user_name"] == "Rahim Uddin"
    assert matching["amount"] == 499.00
