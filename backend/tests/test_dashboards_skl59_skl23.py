"""Automated Pytest suite for Admin Dashboard & Analytics (SKL-23).

Validates Acceptance Criteria AC-1 through AC-5:
- AC-1: Given valid Admin account, authorized dashboard information is returned.
- AC-2: Non-admin users (Learner, Instructor, Company) and unauthenticated calls are blocked with 403/401.
- AC-3: Exact mathematical aggregation of users, courses, jobs, applications, and revenue.
- AC-4: Dynamic refresh reflects new system data mutations (e.g. newly completed transactions, new jobs).
- AC-5: In-depth summaries for revenue (gateways, plans) and recruitment pipelines.
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password, create_access_token
from app.models.user import User, UserRole
from app.models.profile import CompanyProfile, InstructorProfile, LearnerProfile
from app.models.course import Course, CourseStatus
from app.models.job import JobPosting, JobStatus, JobPostingType, JobWorkMode
from app.models.application import JobApplication, ApplicationStatus
from app.models.interview import InterviewRequest, InterviewStatus
from app.models.subscription import (
    PaymentTransaction,
    PaymentStatus,
    UserSubscription,
    SubscriptionStatus,
    SubscriptionPlan,
    SubscriptionPlanCode,
    SubscriptionBillingCycle,
)


def create_user(
    db: Session,
    email: str,
    role: UserRole = UserRole.LEARNER,
    first_name: str = "Test",
    last_name: str = "User",
    is_active: bool = True,
    is_verified: bool = True,
) -> User:
    """Helper to seed user record."""
    user = User(
        email=email,
        hashed_password=hash_password("SecurePassword123!"),
        role=role,
        first_name=first_name,
        last_name=last_name,
        is_active=is_active,
        is_verified=is_verified,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth_header(user: User) -> dict:
    """Helper to generate JWT Bearer authorization header."""
    token = create_access_token(
        subject=user.id,
        claims={"email": user.email, "role": user.role.value},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_user(db_session: Session) -> User:
    """Create super admin user."""
    return create_user(db_session, "superadmin@skill2career.com", UserRole.ADMIN, "Super", "Admin")


@pytest.fixture
def learner_user(db_session: Session) -> User:
    """Create learner user."""
    return create_user(db_session, "learner@example.com", UserRole.LEARNER, "John", "Learner")


@pytest.fixture
def instructor_user(db_session: Session) -> User:
    """Create instructor user."""
    return create_user(db_session, "instructor@example.com", UserRole.INSTRUCTOR, "Jane", "Educator")


@pytest.fixture
def company_user(db_session: Session) -> User:
    """Create company user."""
    return create_user(db_session, "hiring@techcorp.com", UserRole.COMPANY, "TechCorp", "Recruiter")


@pytest.fixture
def seeded_platform_data(db_session: Session, admin_user: User, learner_user: User, company_user: User):
    """Seed a representative ecosystem dataset with companies, courses, jobs, apps, and transactions."""
    # 1. Company Profile
    company_profile = CompanyProfile(
        user_id=company_user.id,
        company_name="TechCorp Solutions",
        industry="Software & IT",
        verification_status="APPROVED",
    )
    db_session.add(company_profile)

    # 2. Course
    course = Course(
        instructor_id=admin_user.id,
        title="Fullstack Web Engineering",
        description="Master modern web development with FastAPI and React",
        category="Software Engineering",
        level="Intermediate",
        price=1500.0,
        is_free=False,
        status=CourseStatus.PUBLISHED.value,
        moderation_status="APPROVED",
    )
    db_session.add(course)

    # 3. Job Posting
    job = JobPosting(
        company_id=company_user.id,
        title="Junior Python Engineer",
        posting_type=JobPostingType.JOB.value,
        work_mode=JobWorkMode.REMOTE.value,
        location="Dhaka",
        description="Looking for Python backend developer",
        requirements="Python, FastAPI, SQL",
        compensation="50,000 BDT/month",
        status=JobStatus.ACTIVE.value,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    # 4. Job Application
    application = JobApplication(
        job_id=job.id,
        learner_id=learner_user.id,
        status=ApplicationStatus.SHORTLISTED.value,
    )
    db_session.add(application)
    db_session.commit()
    db_session.refresh(application)

    # 5. Interview Request
    interview = InterviewRequest(
        application_id=application.id,
        company_id=company_user.id,
        candidate_id=learner_user.id,
        job_id=job.id,
        status=InterviewStatus.SCHEDULED.value,
    )
    db_session.add(interview)
    db_session.commit()
    db_session.refresh(interview)

    # 6. Subscription Plan & Subscriptions
    plan = SubscriptionPlan(
        name="Pro Monthly",
        code=SubscriptionPlanCode.PRO_MONTHLY.value,
        description="Monthly career pass",
        price=499.00,
        billing_cycle=SubscriptionBillingCycle.MONTHLY.value,
        is_active=True,
    )
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)

    user_sub = UserSubscription(
        user_id=learner_user.id,
        plan_id=plan.id,
        status=SubscriptionStatus.ACTIVE.value,
    )
    db_session.add(user_sub)
    db_session.commit()
    db_session.refresh(user_sub)

    # 7. Payment Transactions: 1 Success (499.00), 1 Failed (499.00)
    tx1 = PaymentTransaction(
        transaction_ref="TXN_TEST_SUCCESS_01",
        user_id=learner_user.id,
        subscription_id=user_sub.id,
        amount=499.00,
        currency="BDT",
        gateway="SSLCOMMERZ",
        status=PaymentStatus.SUCCESS.value,
    )
    tx2 = PaymentTransaction(
        transaction_ref="TXN_TEST_FAILED_02",
        user_id=learner_user.id,
        subscription_id=user_sub.id,
        amount=499.00,
        currency="BDT",
        gateway="SSLCOMMERZ",
        status=PaymentStatus.FAILED.value,
    )
    db_session.add_all([tx1, tx2])
    db_session.commit()

    return {
        "company_profile": company_profile,
        "course": course,
        "job": job,
        "application": application,
        "interview": interview,
        "plan": plan,
        "user_sub": user_sub,
        "tx1": tx1,
        "tx2": tx2,
    }


# ==============================================================================
# AC-1: Given valid Admin account, authorized dashboard analytics are displayed
# ==============================================================================

def test_admin_analytics_overview_success(client: TestClient, admin_user: User, seeded_platform_data):
    """AC-1: Valid admin receives 200 OK and complete overview analytics telemetry."""
    headers = auth_header(admin_user)
    response = client.get("/api/v1/admin/analytics/overview", headers=headers)

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True

    data = res_data["data"]
    assert "users" in data
    assert "companies" in data
    assert "courses" in data
    assert "recruitment" in data
    assert "revenue" in data
    assert "moderation" in data
    assert "recent_activity" in data

    # Verify data content
    assert data["users"]["total"] >= 3
    assert data["companies"]["verified"] >= 1
    assert data["courses"]["published"] >= 1
    assert data["recruitment"]["total_jobs"] >= 1
    assert data["revenue"]["total_revenue"] == 499.00
    assert data["revenue"]["successful_transactions"] == 1
    assert len(data["recent_activity"]) > 0


def test_admin_analytics_revenue_success(client: TestClient, admin_user: User, seeded_platform_data):
    """AC-1: Valid admin receives 200 OK and detailed financial breakdown."""
    headers = auth_header(admin_user)
    response = client.get("/api/v1/admin/analytics/revenue", headers=headers)

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True

    data = res_data["data"]
    assert data["total_revenue"] == 499.00
    assert data["currency"] == "BDT"
    assert data["total_transactions"] == 2
    assert data["successful_transactions"] == 1
    assert data["failed_transactions"] == 1
    assert data["success_rate"] == 50.0  # 1 of 2
    assert data["active_subscriptions"] == 1
    assert len(data["revenue_by_gateway"]) >= 1
    assert data["revenue_by_gateway"][0]["gateway"] == "SSLCOMMERZ"
    assert data["revenue_by_gateway"][0]["total_amount"] == 499.00


def test_admin_analytics_recruitment_summary_success(client: TestClient, admin_user: User, seeded_platform_data):
    """AC-1: Valid admin receives 200 OK and recruitment pipeline metrics."""
    headers = auth_header(admin_user)
    response = client.get("/api/v1/admin/analytics/recruitment-summary", headers=headers)

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True

    data = res_data["data"]
    assert data["total_jobs"] >= 1
    assert data["active_jobs"] >= 1
    assert data["total_applications"] >= 1
    assert data["applications_by_status"]["SHORTLISTED"] >= 1
    assert data["total_interviews"] >= 1
    assert data["interviews_by_status"]["SCHEDULED"] >= 1
    assert len(data["top_hiring_companies"]) >= 1
    assert len(data["recent_job_postings"]) >= 1


# ==============================================================================
# AC-2: Given a non-admin user, access must be denied (403 Forbidden / 401)
# ==============================================================================

def test_learner_denied_access_to_admin_analytics(client: TestClient, learner_user: User):
    """AC-2: Learner role receives HTTP 403 Forbidden on all analytics routes."""
    headers = auth_header(learner_user)

    endpoints = [
        "/api/v1/admin/analytics/overview",
        "/api/v1/admin/analytics/revenue",
        "/api/v1/admin/analytics/recruitment-summary",
    ]
    for url in endpoints:
        res = client.get(url, headers=headers)
        assert res.status_code == 403
        data = res.json()
        assert data["success"] is False
        assert data["error_code"] == "INSUFFICIENT_ROLE_PERMISSIONS"


def test_instructor_and_company_denied_access(client: TestClient, instructor_user: User, company_user: User):
    """AC-2: Instructor and Company roles receive HTTP 403 Forbidden."""
    for user in [instructor_user, company_user]:
        headers = auth_header(user)
        res = client.get("/api/v1/admin/analytics/revenue", headers=headers)
        assert res.status_code == 403
        assert res.json()["error_code"] == "INSUFFICIENT_ROLE_PERMISSIONS"


def test_unauthenticated_request_rejected(client: TestClient):
    """AC-2: Unauthenticated request receives HTTP 401 Unauthorized."""
    res = client.get("/api/v1/admin/analytics/overview")
    assert res.status_code == 401
    assert res.json()["error_code"] == "NOT_AUTHENTICATED"


# ==============================================================================
# AC-3: Exact mathematical aggregation of system data
# ==============================================================================

def test_revenue_and_recruitment_aggregation_math(client: TestClient, admin_user: User, seeded_platform_data):
    """AC-3: System data calculations strictly match database state."""
    headers = auth_header(admin_user)

    # 1. Check revenue: failed transactions must NOT be counted in total_revenue
    rev_res = client.get("/api/v1/admin/analytics/revenue", headers=headers).json()["data"]
    assert rev_res["total_revenue"] == 499.00
    assert rev_res["successful_transactions"] == 1
    assert rev_res["failed_transactions"] == 1
    assert rev_res["success_rate"] == 50.0

    # 2. Check recruitment stage counts
    rec_res = client.get("/api/v1/admin/analytics/recruitment-summary", headers=headers).json()["data"]
    assert rec_res["applications_by_status"]["SHORTLISTED"] == 1
    assert rec_res["applications_by_status"]["OFFERED"] == 0
    assert rec_res["interviews_by_status"]["SCHEDULED"] == 1


# ==============================================================================
# AC-4: Dynamic refresh updates to latest information
# ==============================================================================

def test_dashboard_data_updates_dynamically_on_mutation(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    learner_user: User,
    seeded_platform_data,
):
    """AC-4: New transaction and job postings immediately reflect on subsequent queries."""
    headers = auth_header(admin_user)

    # Initial revenue is 499.00
    initial_rev = client.get("/api/v1/admin/analytics/revenue", headers=headers).json()["data"]["total_revenue"]
    assert initial_rev == 499.00

    # Insert a 2nd successful transaction (৳1,500 via Global Gateway)
    new_tx = PaymentTransaction(
        transaction_ref="TXN_NEW_GLOBAL_PAY",
        user_id=learner_user.id,
        amount=1500.00,
        currency="BDT",
        gateway="GLOBAL_GATEWAY",
        status=PaymentStatus.SUCCESS.value,
    )
    db_session.add(new_tx)
    db_session.commit()

    # Query again (simulating dashboard refresh)
    refreshed_data = client.get("/api/v1/admin/analytics/revenue", headers=headers).json()["data"]
    assert refreshed_data["total_revenue"] == 1999.00  # 499 + 1500
    assert refreshed_data["successful_transactions"] == 2
    assert refreshed_data["total_transactions"] == 3
    assert refreshed_data["success_rate"] == 66.67  # 2 of 3

    # Check overview also reflects updated revenue
    overview_data = client.get("/api/v1/admin/analytics/overview", headers=headers).json()["data"]
    assert overview_data["revenue"]["total_revenue"] == 1999.00
    assert overview_data["revenue"]["successful_transactions"] == 2


# ==============================================================================
# AC-5: In-depth summaries for revenue and recruitment pipelines
# ==============================================================================

def test_detailed_summaries_gateways_and_plans(
    client: TestClient,
    admin_user: User,
    seeded_platform_data,
):
    """AC-5: Revenue summary provides granular gateway breakdown and plan distribution."""
    headers = auth_header(admin_user)
    rev_data = client.get("/api/v1/admin/analytics/revenue", headers=headers).json()["data"]

    # Gateways summary
    gateways = {g["gateway"]: g for g in rev_data["revenue_by_gateway"]}
    assert "SSLCOMMERZ" in gateways
    assert gateways["SSLCOMMERZ"]["count"] == 1
    assert gateways["SSLCOMMERZ"]["total_amount"] == 499.00

    # Plan summary
    plans = {p["plan_code"]: p for p in rev_data["revenue_by_plan"]}
    assert SubscriptionPlanCode.PRO_MONTHLY.value in plans
    assert plans[SubscriptionPlanCode.PRO_MONTHLY.value]["subscriber_count"] == 1
    assert plans[SubscriptionPlanCode.PRO_MONTHLY.value]["total_revenue"] == 499.00

    # Recent transactions audit summary
    recent_txs = rev_data["recent_transactions"]
    assert len(recent_txs) >= 1
    assert recent_txs[0]["transaction_ref"] is not None
    assert recent_txs[0]["user_email"] == "learner@example.com"
