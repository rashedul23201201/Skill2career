"""Automated Pytest Suite for SKL-61: Security & Access Control Testing.

Validates comprehensive security architecture, access control bounds, and tamper resistance:
- AC-1: Authentication & Token Security (Expired, malformed, forged signature, 'none' algorithm, unauthenticated rejection).
- AC-2: Password Hashing & Sensitive Credential Secrecy (bcrypt verification, zero plaintext leakage in API outputs).
- AC-3: Strict Role-Based Access Control (RBAC) (Learner, Instructor, Company, and Admin authorization boundaries).
- AC-4: Unverified Company Publishing Barrier (Gatekeeper against fraudulent / unverified recruiters).
- AC-5: Broken Object-Level Authorization (BOLA / IDOR Prevention across Applications, Attempts, Chats, and Notifications).
- AC-6: Session Revocation & Token Claim Invalidation (Immediate rejection on account deactivation and stale role claim).
- AC-7: Input Validation, SQL Injection & Cross-Site Scripting (XSS) Sanitization.
- AC-8: Mass Assignment & Privilege Escalation Tamper Prevention.
- AC-9: Subscription Paywall & Entitlement Gating Protection.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import jwt

from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)
from app.models.user import User, UserRole
from app.models.profile import CompanyProfile, InstructorProfile, LearnerProfile
from app.models.course import Course, CourseStatus, CourseModule, Lesson
from app.models.mock_test import MockTest, TestQuestion, TestAttempt, TestResult
from app.models.job import JobPosting, JobStatus, JobPostingType, JobWorkMode
from app.models.application import JobApplication, ApplicationStatus
from app.models.interview import InterviewRequest, InterviewStatus
from app.models.chat import ChatConversation, ChatMessage
from app.models.notification import Notification
from app.models.subscription import (
    SubscriptionPlan,
    SubscriptionPlanCode,
    SubscriptionStatus,
    UserSubscription,
)
from app.repositories.subscription_repository import SubscriptionRepository


def create_security_user(
    db: Session,
    email: str,
    role: UserRole = UserRole.LEARNER,
    first_name: str = "Sec",
    last_name: str = "Tester",
    is_active: bool = True,
    is_verified: bool = True,
    company_verified: bool = True,
) -> User:
    """Helper to author a user and role-specific profile in test database."""
    user = User(
        email=email,
        hashed_password=hash_password("SecuReP@ssw0rd!123"),
        role=role,
        first_name=first_name,
        last_name=last_name,
        is_active=is_active,
        is_verified=is_verified,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if role == UserRole.LEARNER:
        profile = LearnerProfile(
            user_id=user.id,
            bio="Security & QA Specialist",
            institution="University of Asia Pacific",
            department="CSE",
            target_role="Software Security Engineer",
            skills=["Python", "FastAPI", "Security Testing", "OAuth2"],
            resume_url="https://example.com/resumes/sec_profile.pdf",
            resume_filename="sec_profile.pdf",
        )
        db.add(profile)
    elif role == UserRole.INSTRUCTOR:
        profile = InstructorProfile(
            user_id=user.id,
            designation="Dr. Professor",
            institution="Dept of Cyber Security",
            qualification="Ph.D. in Cyber Security",
            expertise_domain="Cryptography & Security",
            onboarding_status="APPROVED",
        )
        db.add(profile)
    elif role == UserRole.COMPANY:
        profile = CompanyProfile(
            user_id=user.id,
            company_name=f"{first_name} Cyber Defense Inc",
            description="Enterprise Security and Threat Modeling",
            industry="Cybersecurity",
            office_address="Dhaka Tech Park",
            website_url="https://sec-defense.example.com",
            verification_status="APPROVED" if company_verified else "PENDING",
            verified_at=datetime.now(timezone.utc) if company_verified else None,
        )
        db.add(profile)

    db.commit()
    db.refresh(user)
    return user


def auth_header(user: User) -> dict:
    """Generate valid JWT Authorization header for testing."""
    token = create_access_token(
        subject=user.id,
        claims={"email": user.email, "role": user.role.value},
    )
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# AC-1: Authentication & JWT Token Security
# ==============================================================================

def test_unauthenticated_request_rejected(client: TestClient):
    """AC-1.1: Protected endpoints strictly reject unauthenticated requests with HTTP 401."""
    protected_endpoints = [
        ("GET", "/api/v1/auth/me"),
        ("GET", "/api/v1/learners/profile"),
        ("GET", "/api/v1/companies/profile/me"),
        ("POST", "/api/v1/courses"),
        ("POST", "/api/v1/jobs"),
        ("GET", "/api/v1/admin/users"),
        ("GET", "/api/v1/admin/analytics/overview"),
    ]

    for method, path in protected_endpoints:
        if method == "GET":
            res = client.get(path)
        else:
            res = client.post(path, json={})
        assert res.status_code == 401, f"Expected 401 for {method} {path}, got {res.status_code}"
        assert res.json()["error_code"] in ("NOT_AUTHENTICATED", "INVALID_TOKEN")


def test_malformed_and_tampered_token_rejected(client: TestClient, db_session: Session):
    """AC-1.2: Malformed tokens, invalid signatures, and tampered secrets receive HTTP 401."""
    user = create_security_user(db_session, "token.tamper@example.com", UserRole.LEARNER)

    # 1. Nonsense string token
    res1 = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer completely-invalid-token"})
    assert res1.status_code == 401
    assert res1.json()["error_code"] == "INVALID_TOKEN"

    # 2. Token signed with wrong secret key
    fake_token = jwt.encode(
        {"sub": str(user.id), "role": user.role.value, "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        "completely-wrong-secret-key-1234567890",
        algorithm="HS256",
    )
    res2 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {fake_token}"})
    assert res2.status_code == 401
    assert res2.json()["error_code"] == "INVALID_TOKEN"

    # 3. Algorithm 'none' attack simulation
    none_token = jwt.encode(
        {"sub": str(user.id), "role": "ADMIN", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        key="",
        algorithm="none",
    )
    res3 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {none_token}"})
    assert res3.status_code == 401


def test_expired_token_rejected(client: TestClient, db_session: Session):
    """AC-1.3: Expired JWT tokens strictly raise 401 TOKEN_EXPIRED."""
    user = create_security_user(db_session, "token.expired@example.com", UserRole.LEARNER)
    expired_token = create_access_token(
        subject=user.id,
        claims={"email": user.email, "role": user.role.value},
        expires_delta=timedelta(seconds=-10),  # expired 10 seconds ago
    )

    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401
    assert res.json()["error_code"] == "TOKEN_EXPIRED"


# ==============================================================================
# AC-2: Password Hashing & Credential Secrecy
# ==============================================================================

def test_password_hashing_and_credential_privacy(client: TestClient, db_session: Session):
    """AC-2: Passwords must be hashed with strong salt (bcrypt) and NEVER exposed in API responses."""
    user = create_security_user(db_session, "privacy.tester@example.com", UserRole.LEARNER)

    # 1. Verify stored password is a secure bcrypt hash
    assert user.hashed_password.startswith("$2b$") or user.hashed_password.startswith("$2a$")
    assert user.hashed_password != "SecuReP@ssw0rd!123"
    assert verify_password("SecuReP@ssw0rd!123", user.hashed_password) is True
    assert verify_password("WrongPassword!", user.hashed_password) is False

    # 2. Inspect /auth/me output: password must NEVER be returned
    headers = auth_header(user)
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_json = me_res.json()["data"]
    assert "password" not in me_json
    assert "hashed_password" not in me_json

    # 3. Inspect Admin user listing: password must NEVER be exposed
    admin = create_security_user(db_session, "admin.privacy@example.com", UserRole.ADMIN)
    admin_headers = auth_header(admin)
    admin_res = client.get(f"/api/v1/admin/users/{user.id}", headers=admin_headers)
    assert admin_res.status_code == 200
    admin_user_json = admin_res.json()["data"]
    assert "password" not in admin_user_json
    assert "hashed_password" not in admin_user_json


# ==============================================================================
# AC-3: Strict Role-Based Access Control (RBAC) Boundaries
# ==============================================================================

def test_learner_rbac_boundaries(client: TestClient, db_session: Session):
    """AC-3.1: Learner accounts are strictly prevented from executing Admin, Instructor, or Recruiter operations."""
    learner = create_security_user(db_session, "learner.bounds@example.com", UserRole.LEARNER)
    headers = auth_header(learner)

    # Attempt Admin user governance -> 403
    res1 = client.get("/api/v1/admin/users", headers=headers)
    assert res1.status_code == 403
    assert res1.json()["error_code"] == "INSUFFICIENT_ROLE_PERMISSIONS"

    # Attempt Admin executive analytics -> 403
    res2 = client.get("/api/v1/admin/analytics/overview", headers=headers)
    assert res2.status_code == 403

    # Attempt Admin content moderation -> 403
    res3 = client.get("/api/v1/admin/moderation/pending", headers=headers)
    assert res3.status_code == 403

    # Attempt Recruiter vacancy creation -> 403
    res4 = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={"title": "Unauthorized Job", "posting_type": "Job", "work_mode": "Remote"},
    )
    assert res4.status_code == 403

    # Attempt Instructor course authoring -> 403
    res5 = client.post(
        "/api/v1/courses",
        headers=headers,
        json={"title": "Unauthorized Course", "category": "Programming", "level": "Beginner"},
    )
    assert res5.status_code == 403

    # Attempt Mock Test authoring -> 403
    res6 = client.post(
        "/api/v1/mock-tests",
        headers=headers,
        json={"title": "Unauthorized Test", "category": "General", "duration_minutes": 20, "passing_score": 60},
    )
    assert res6.status_code == 403


def test_instructor_and_company_rbac_boundaries(client: TestClient, db_session: Session):
    """AC-3.2: Instructor and Company roles cannot breach each other's domain or access Admin governance."""
    instructor = create_security_user(db_session, "inst.bounds@example.com", UserRole.INSTRUCTOR)
    company = create_security_user(db_session, "comp.bounds@example.com", UserRole.COMPANY)

    inst_headers = auth_header(instructor)
    comp_headers = auth_header(company)

    # Instructor cannot post jobs
    res1 = client.post(
        "/api/v1/jobs",
        headers=inst_headers,
        json={"title": "Instructor Job", "posting_type": "Job", "work_mode": "Remote"},
    )
    assert res1.status_code == 403

    # Company cannot author courses
    res2 = client.post(
        "/api/v1/courses",
        headers=comp_headers,
        json={"title": "Company Course", "category": "Business", "level": "Beginner"},
    )
    assert res2.status_code == 403

    # Neither can access Admin audit logs
    assert client.get("/api/v1/admin/audit-logs", headers=inst_headers).status_code == 403
    assert client.get("/api/v1/admin/audit-logs", headers=comp_headers).status_code == 403


# ==============================================================================
# AC-4: Unverified Company Gatekeeper Barrier
# ==============================================================================

def test_unverified_company_cannot_post_jobs(client: TestClient, db_session: Session):
    """AC-4: Companies pending verification or rejected are forbidden from posting vacancies (SKL-2)."""
    unverified_comp = create_security_user(
        db_session,
        "pending.company@example.com",
        UserRole.COMPANY,
        company_verified=False,
    )
    headers = auth_header(unverified_comp)

    job_payload = {
        "title": "Senior Security Analyst",
        "description": "Must have penetration testing experience.",
        "posting_type": "Job",
        "work_mode": "Hybrid",
        "location": "Gulshan, Dhaka",
        "requirements": "3+ years security engineering",
        "compensation": "75,000 BDT/month",
        "experience_level": "Mid-Level",
        "category": "Software Engineering",
    }

    res = client.post("/api/v1/jobs", headers=headers, json=job_payload)
    assert res.status_code == 403
    assert res.json()["error_code"] == "COMPANY_NOT_VERIFIED"


# ==============================================================================
# AC-5: Broken Object-Level Authorization (BOLA / IDOR Prevention)
# ==============================================================================

def test_job_application_and_withdrawal_idor_protection(client: TestClient, db_session: Session):
    """AC-5.1: Candidate A cannot inspect or withdraw Candidate B's application."""
    cand_a = create_security_user(db_session, "cand.alice@example.com", UserRole.LEARNER)
    cand_b = create_security_user(db_session, "cand.bob@example.com", UserRole.LEARNER)
    company = create_security_user(db_session, "hiring.idor@example.com", UserRole.COMPANY)

    comp_headers = auth_header(company)
    alice_headers = auth_header(cand_a)
    bob_headers = auth_header(cand_b)

    # 1. Company posts a job
    job = JobPosting(
        company_id=company.id,
        title="Software Engineer",
        description="Core developer",
        posting_type=JobPostingType.JOB,
        work_mode=JobWorkMode.REMOTE,
        location="Remote",
        requirements="Python",
        compensation="80,000 BDT/month",
        status=JobStatus.ACTIVE,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    # 2. Bob applies for the job
    bob_app = JobApplication(
        job_id=job.id,
        learner_id=cand_b.id,
        cover_letter="Bob's application statement.",
        status=ApplicationStatus.SUBMITTED.value,
        resume_url="https://example.com/bob.pdf",
    )
    db_session.add(bob_app)
    db_session.commit()
    db_session.refresh(bob_app)

    # 3. Alice attempts to view Bob's application details -> Blocked
    view_res = client.get(f"/api/v1/applications/{bob_app.id}", headers=alice_headers)
    assert view_res.status_code in (403, 404)

    # 4. Alice attempts to withdraw Bob's application -> Blocked
    withdraw_res = client.delete(f"/api/v1/applications/{bob_app.id}/withdraw", headers=alice_headers)
    assert withdraw_res.status_code in (403, 404)

    # 5. Bob can inspect his own application
    bob_view_res = client.get(f"/api/v1/applications/{bob_app.id}", headers=bob_headers)
    assert bob_view_res.status_code == 200
    assert bob_view_res.json()["data"]["id"] == bob_app.id


def test_mock_test_attempt_submission_idor_protection(client: TestClient, db_session: Session):
    """AC-5.2: Learner A cannot submit answers for or tamper with Learner B's test attempt."""
    learner_a = create_security_user(db_session, "examinee.alice@example.com", UserRole.LEARNER)
    learner_b = create_security_user(db_session, "examinee.bob@example.com", UserRole.LEARNER)
    instructor = create_security_user(db_session, "eval.mentor@example.com", UserRole.INSTRUCTOR)

    alice_headers = auth_header(learner_a)
    bob_headers = auth_header(learner_b)
    inst_headers = auth_header(instructor)

    # 1. Author mock test
    test = MockTest(
        instructor_id=instructor.id,
        title="Web Security & PenTesting",
        category="Security",
        duration_minutes=20,
        passing_score=50,
        status="PUBLISHED",
        is_published=True,
        moderation_status="APPROVED",
    )
    db_session.add(test)
    db_session.commit()
    db_session.refresh(test)

    # 2. Bob starts an attempt session
    bob_start_res = client.post(f"/api/v1/mock-tests/{test.id}/start-attempt", headers=bob_headers)
    assert bob_start_res.status_code == 201
    bob_attempt_id = bob_start_res.json()["data"]["id"]

    # 3. Alice attempts to submit answers for Bob's attempt session -> 403/404 Forbidden
    submit_payload = {"answers": {"1": "B"}, "marked_for_review": []}
    tamper_res = client.post(
        f"/api/v1/attempts/{bob_attempt_id}/submit-answers",
        headers=alice_headers,
        json=submit_payload,
    )
    assert tamper_res.status_code in (403, 404)

    # 4. Alice attempts to inspect Bob's attempt result -> 403/404 Forbidden
    inspect_res = client.get(f"/api/v1/attempts/{bob_attempt_id}/result", headers=alice_headers)
    assert inspect_res.status_code in (403, 404)


def test_chat_eavesdropping_and_notification_tampering_idor(client: TestClient, db_session: Session):
    """AC-5.3: Unauthorized third parties cannot eavesdrop on private chats or tamper with notifications."""
    learner = create_security_user(db_session, "student.chatsec@example.com", UserRole.LEARNER)
    instructor = create_security_user(db_session, "mentor.chatsec@example.com", UserRole.INSTRUCTOR)
    stranger = create_security_user(db_session, "eavesdropper@example.com", UserRole.LEARNER)

    learner_headers = auth_header(learner)
    stranger_headers = auth_header(stranger)

    # 1. Learner opens conversation with Instructor
    conv = ChatConversation(learner_id=learner.id, instructor_id=instructor.id)
    db_session.add(conv)
    db_session.commit()
    db_session.refresh(conv)

    msg = ChatMessage(
        conversation_id=conv.id,
        sender_id=learner.id,
        message_text="Private thesis guidance message.",
    )
    db_session.add(msg)

    # 2. Add private notification for Learner
    notif = Notification(
        recipient_id=learner.id,
        event_type="SECURITY_ALERT",
        title="Confidential Alert",
        message="Your credentials were verified.",
        is_read=False,
    )
    db_session.add(notif)
    db_session.commit()
    db_session.refresh(notif)

    # 3. Stranger attempts to fetch conversation messages -> 403/404
    eavesdrop_res = client.get(f"/api/v1/chat/conversations/{conv.id}/messages", headers=stranger_headers)
    assert eavesdrop_res.status_code in (403, 404)

    # 4. Stranger attempts to mark Learner's notification as read -> 403/404
    tamper_notif_res = client.patch(f"/api/v1/notifications/{notif.id}/read", headers=stranger_headers)
    assert tamper_notif_res.status_code in (403, 404)


# ==============================================================================
# AC-6: Session Revocation & Stale Role Invalidation
# ==============================================================================

def test_deactivated_account_session_revocation(client: TestClient, db_session: Session):
    """AC-6.1: Deactivated user accounts immediately have active JWT sessions revoked with 403 ACCOUNT_INACTIVE."""
    user = create_security_user(db_session, "active.target@example.com", UserRole.LEARNER)
    valid_headers = auth_header(user)

    # Token works initially
    res_before = client.get("/api/v1/auth/me", headers=valid_headers)
    assert res_before.status_code == 200

    # Admin or system deactivates account
    user.is_active = False
    db_session.commit()

    # Active token is immediately rejected
    res_after = client.get("/api/v1/auth/me", headers=valid_headers)
    assert res_after.status_code == 403
    assert res_after.json()["error_code"] == "ACCOUNT_INACTIVE"


def test_stale_role_token_invalidation(client: TestClient, db_session: Session):
    """AC-6.2: If admin changes user role, tokens bearing the old role claim are immediately invalidated."""
    user = create_security_user(db_session, "role.change@example.com", UserRole.ADMIN)

    # Generate token bearing ADMIN claim
    token = create_access_token(subject=user.id, claims={"email": user.email, "role": "ADMIN"})
    admin_headers = {"Authorization": f"Bearer {token}"}

    # Verify works
    res_admin = client.get("/api/v1/admin/users", headers=admin_headers)
    assert res_admin.status_code == 200

    # User is demoted to LEARNER in the database
    user.role = UserRole.LEARNER
    db_session.commit()

    # The existing token with 'ADMIN' role claim must be rejected as SESSION_ROLE_REVOKED
    res_demoted = client.get("/api/v1/admin/users", headers=admin_headers)
    assert res_demoted.status_code == 401
    assert res_demoted.json()["error_code"] == "SESSION_ROLE_REVOKED"


# ==============================================================================
# AC-7: Input Sanitization, SQL Injection & XSS Containment
# ==============================================================================

def test_sql_injection_resilience(client: TestClient, db_session: Session):
    """AC-7.1: SQL injection strings in query params are handled safely without SQL syntax errors or unauthorized leakage."""
    sqli_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "' UNION SELECT id, email, hashed_password FROM users --",
        "1' OR 1=1 #",
    ]

    for payload in sqli_payloads:
        # Search courses with SQL injection payload
        res = client.get(f"/api/v1/courses?search={payload}")
        assert res.status_code == 200
        assert "items" in res.json()["data"]

        # Search jobs with SQL injection payload
        job_res = client.get(f"/api/v1/jobs?search={payload}")
        assert job_res.status_code == 200
        assert "items" in job_res.json()["data"]


def test_xss_script_payload_containment(client: TestClient, db_session: Session):
    """AC-7.2: Stored Cross-Site Scripting (XSS) payloads are stored as inert text and do not corrupt responses."""
    learner = create_security_user(db_session, "xss.tester@example.com", UserRole.LEARNER)
    headers = auth_header(learner)

    xss_bio = "<script>alert('XSS-EXPLOIT');</script>"
    xss_location = "<img src='x' onerror='window.stealTokens()'/>"

    update_payload = {
        "location": xss_location,
        "bio": xss_bio,
    }

    res = client.put("/api/v1/learners/profile", headers=headers, json=update_payload)
    assert res.status_code == 200
    profile_data = res.json()["data"]
    # Verify the payload is preserved as safe string content without crashing or executing
    assert profile_data["bio"] == xss_bio
    assert profile_data["location"] == xss_location


# ==============================================================================
# AC-8: Mass Assignment & Privilege Escalation Prevention
# ==============================================================================

def test_mass_assignment_privilege_escalation_prevented(client: TestClient, db_session: Session):
    """AC-8: Malicious callers cannot escalate to ADMIN or tamper with verification status via profile update."""
    learner = create_security_user(db_session, "mass.assignment@example.com", UserRole.LEARNER)
    headers = auth_header(learner)

    malicious_payload = {
        "bio": "Normal user updating bio",
        "role": "ADMIN",  # Attempting privilege escalation to ADMIN
        "is_admin": True,
        "is_verified": True,
        "is_active": True,
    }

    res = client.put("/api/v1/learners/profile", headers=headers, json=malicious_payload)
    assert res.status_code == 200
    updated_profile = res.json()["data"]
    assert updated_profile["role"] == "LEARNER"

    # Verify /auth/me reflects unchanged role
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["data"]["role"] == "LEARNER"


# ==============================================================================
# AC-9: Subscription Entitlement Access Control (Paywall Enforcement)
# ==============================================================================

def test_subscription_entitlement_access_control(client: TestClient, db_session: Session):
    """AC-9: Unsubscribed Free-tier learners are correctly identified and gated on Pro privileges."""
    repo = SubscriptionRepository()
    repo.ensure_seed_plans(db_session)

    free_user = create_security_user(db_session, "free.user@example.com", UserRole.LEARNER)
    headers = auth_header(free_user)

    # 1. Query user's current subscription
    sub_res = client.get("/api/v1/subscriptions/my-subscription", headers=headers)
    assert sub_res.status_code == 200
    sub_data = sub_res.json()["data"]
    assert sub_data["is_pro"] is False
    assert sub_data["plan"]["code"] == SubscriptionPlanCode.FREE.value

    # 2. Check entitlements endpoint
    entitlements_res = client.get("/api/v1/subscriptions/entitlements", headers=headers)
    assert entitlements_res.status_code == 200
    ent_data = entitlements_res.json()["data"]
    assert ent_data["is_pro"] is False
    assert ent_data["can_access_premium_mock_tests"] is False
