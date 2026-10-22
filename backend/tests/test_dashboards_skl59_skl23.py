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
from app.models.course import Course, CourseStatus, CourseModule, Lesson
from app.models.enrollment import CourseEnrollment, LessonProgress
from app.models.mock_test import MockTest, TestAttempt
from app.models.job import JobPosting, JobStatus, JobPostingType, JobWorkMode
from app.models.application import JobApplication, ApplicationStatus
from app.models.interview import InterviewRequest, InterviewStatus
from app.models.chat import ChatConversation, ChatMessage
from app.models.notification import Notification
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


# ==============================================================================
# SPRINT 4 TICKET SKL-59: Learner & Instructor Role Dashboards Test Suite
# ==============================================================================

@pytest.fixture
def seeded_dashboard_data(db_session: Session, learner_user: User, instructor_user: User, company_user: User):
    """Seed comprehensive course, assessment, profile, and interaction data for SKL-59."""
    # 1. Instructor Profile
    inst_profile = InstructorProfile(
        user_id=instructor_user.id,
        designation="CSE Instructor",
        institution="Independent Educator",
        qualification="M.Sc. in Computer Science",
        expertise_domain="Software Engineering",
        years_experience="6+ years",
        onboarding_status="APPROVED",
    )
    db_session.add(inst_profile)

    # 2. Learner Profile
    lrn_profile = LearnerProfile(
        user_id=learner_user.id,
        institution="CSE @ UAP",
        department="B.Sc. in Computer Science & Engineering",
        target_role="Junior Software Developer",
        completion_pct=85,
        skills={"items": ["Java", "Python", "SQL", "Git"]},
    )
    db_session.add(lrn_profile)
    db_session.commit()

    # 3. Course Authored by Instructor
    course = Course(
        instructor_id=instructor_user.id,
        title="Software Engineering",
        description="Comprehensive preparation covering Graphs, Dynamic Programming & System Complexity.",
        category="Software Engineering",
        level="Intermediate",
        price=2000.0,
        is_free=False,
        status=CourseStatus.PUBLISHED.value,
        duration_weeks=8,
    )
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    # 4. Course Module & Lessons
    module = CourseModule(course_id=course.id, title="Module 1: Foundations", order_index=1)
    db_session.add(module)
    db_session.commit()
    db_session.refresh(module)

    lesson1 = Lesson(
        course_id=course.id,
        module_id=module.id,
        title="Intro to Architecture",
        content_type="VIDEO",
        order_index=1,
    )
    lesson2 = Lesson(
        course_id=course.id,
        module_id=module.id,
        title="Design Patterns",
        content_type="VIDEO",
        order_index=2,
    )
    lesson3 = Lesson(
        course_id=course.id,
        module_id=module.id,
        title="System Scalability",
        content_type="VIDEO",
        order_index=3,
    )
    db_session.add_all([lesson1, lesson2, lesson3])
    db_session.commit()

    # 5. Course Enrollment for Learner
    enrollment = CourseEnrollment(
        user_id=learner_user.id,
        course_id=course.id,
        status="ACTIVE",
        progress_percentage=75.0,
        completed_lessons_count=2,
    )
    db_session.add(enrollment)
    db_session.commit()
    db_session.refresh(enrollment)

    # 6. Lesson Progress
    prog1 = LessonProgress(
        user_id=learner_user.id,
        course_id=course.id,
        lesson_id=lesson1.id,
        enrollment_id=enrollment.id,
        is_completed=True,
    )
    prog2 = LessonProgress(
        user_id=learner_user.id,
        course_id=course.id,
        lesson_id=lesson2.id,
        enrollment_id=enrollment.id,
        is_completed=True,
    )
    db_session.add_all([prog1, prog2])

    # 7. Mock Test by Instructor
    mock_test = MockTest(
        instructor_id=instructor_user.id,
        title="DSA Mock Test",
        description="Data structures algorithmic evaluation",
        category="Software Engineering",
        duration_minutes=60,
        passing_score=60,
        total_questions=25,
        status="ACTIVE",
        is_published=True,
    )
    db_session.add(mock_test)
    db_session.commit()
    db_session.refresh(mock_test)

    # 8. Test Attempt by Learner
    attempt = TestAttempt(
        test_id=mock_test.id,
        learner_id=learner_user.id,
        score=82.0,
        total_marks=100.0,
        percentage=82.0,
        is_passed=True,
        submitted_at=datetime.now(timezone.utc),
    )
    db_session.add(attempt)

    # 9. Company, Job, Application & Interview
    company_profile = CompanyProfile(
        user_id=company_user.id,
        company_name="Brain Station 23",
        industry="Software & IT",
        verification_status="APPROVED",
    )
    db_session.add(company_profile)

    job = JobPosting(
        company_id=company_user.id,
        title="Junior Software Developer",
        posting_type=JobPostingType.JOB.value,
        work_mode=JobWorkMode.REMOTE.value,
        location="Dhaka",
        description="Looking for Junior Software Developer",
        requirements="Python, React",
        compensation="50,000 BDT/month",
        status=JobStatus.ACTIVE.value,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    app = JobApplication(
        job_id=job.id,
        learner_id=learner_user.id,
        status=ApplicationStatus.SHORTLISTED.value,
    )
    db_session.add(app)
    db_session.commit()
    db_session.refresh(app)

    interview = InterviewRequest(
        application_id=app.id,
        company_id=company_user.id,
        candidate_id=learner_user.id,
        job_id=job.id,
        interview_type="Technical Interview",
        meeting_platform="Live Coding round via Google Meet",
        status=InterviewStatus.SCHEDULED.value,
        scheduled_at=datetime.now(timezone.utc),
    )
    db_session.add(interview)

    # 10. Chat & Notification
    conv = ChatConversation(
        learner_id=learner_user.id,
        instructor_id=instructor_user.id,
    )
    db_session.add(conv)
    db_session.commit()
    db_session.refresh(conv)

    chat_msg = ChatMessage(
        conversation_id=conv.id,
        sender_id=learner_user.id,
        message_text="Hello instructor, I have a question on lesson 2.",
        is_read=False,
    )
    notif = Notification(
        recipient_id=learner_user.id,
        event_type="APPLICATION_UPDATE",
        title="Application Shortlisted",
        message="Your application at Brain Station 23 was shortlisted.",
        is_read=False,
    )
    db_session.add_all([chat_msg, notif])
    db_session.commit()

    return {
        "course": course,
        "enrollment": enrollment,
        "mock_test": mock_test,
        "attempt": attempt,
        "job": job,
        "application": app,
        "interview": interview,
    }


# ==============================================================================
# AC-1: Given an authenticated learner, when the dashboard opens, then learner-specific information must be displayed.
# ==============================================================================

def test_learner_dashboard_summary_success(client: TestClient, learner_user: User, seeded_dashboard_data):
    """AC-1: Authenticated learner receives 200 OK and accurate learner dashboard telemetry."""
    headers = auth_header(learner_user)
    response = client.get("/api/v1/learners/dashboard-summary", headers=headers)

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True

    data = res_data["data"]
    assert "metrics" in data
    assert "active_curriculum" in data
    assert "enrolled_courses" in data
    assert "latest_interview" in data
    assert "latest_mock_test" in data
    assert "latest_application" in data
    assert "career_profile" in data

    # Verify metric cards
    assert data["metrics"]["enrolled_courses"] >= 1
    assert data["metrics"]["course_progress"] == 75.0
    assert data["metrics"]["mock_test_score"] == 82.0
    assert data["metrics"]["applications_count"] >= 1
    assert data["metrics"]["unread_notifications"] >= 1

    # Verify active curriculum
    assert data["active_curriculum"]["title"] == "Software Engineering"
    assert data["active_curriculum"]["progress_percentage"] == 75.0
    assert data["active_curriculum"]["completed_lessons"] == 2

    # Verify assessment result
    assert data["latest_mock_test"]["test_title"] == "DSA Mock Test"
    assert data["latest_mock_test"]["percentage"] == 82.0
    assert data["latest_mock_test"]["is_passed"] is True

    # Verify interview schedule & application
    assert data["latest_interview"]["job_title"] == "Junior Software Developer"
    assert data["latest_interview"]["company_name"] == "Brain Station 23"
    assert data["latest_application"]["company_name"] == "Brain Station 23"

    # Verify career profile
    assert data["career_profile"]["first_name"] == learner_user.first_name
    assert data["career_profile"]["institution"] == "CSE @ UAP"
    assert "Python" in data["career_profile"]["skills"]


# ==============================================================================
# AC-2: Given an authenticated instructor, when the dashboard opens, then instructor-specific information must be displayed.
# ==============================================================================

def test_instructor_dashboard_summary_success(client: TestClient, instructor_user: User, seeded_dashboard_data):
    """AC-2: Authenticated instructor receives 200 OK and complete workspace telemetry."""
    headers = auth_header(instructor_user)
    response = client.get("/api/v1/instructors/dashboard-summary", headers=headers)

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True

    data = res_data["data"]
    assert "metrics" in data
    assert "my_courses" in data
    assert "learner_performance" in data
    assert "profile" in data

    # Verify metrics
    assert data["metrics"]["active_courses"] >= 1
    assert data["metrics"]["total_learners"] >= 1
    assert data["metrics"]["mock_tests"] >= 1
    assert data["metrics"]["unread_inquiries"] >= 1

    # Verify courses list
    assert len(data["my_courses"]) >= 1
    assert data["my_courses"][0]["title"] == "Software Engineering"
    assert data["my_courses"][0]["enrolled_learners"] >= 1
    assert data["my_courses"][0]["average_progress"] == 75.0

    # Verify learner performance cohort metrics
    assert data["learner_performance"]["average_course_progress"] == 75.0
    assert data["learner_performance"]["average_test_score"] == 82.0
    assert data["learner_performance"]["cohort_label"] == "Batch 2026"

    # Verify instructor profile summary
    assert data["profile"]["designation"] == "CSE Instructor"
    assert data["profile"]["specialization"] == "Software Engineering"
    assert data["profile"]["onboarding_status"] == "APPROVED"


# ==============================================================================
# AC-3: Given relevant course or test data exists, when the dashboard loads, then appropriate summaries must be shown.
# ==============================================================================

def test_dashboard_exact_mathematical_aggregation(
    client: TestClient,
    db_session: Session,
    learner_user: User,
    instructor_user: User,
    seeded_dashboard_data,
):
    """AC-3: System data calculations strictly match database state for both Learner and Instructor."""
    # 1. Learner verification
    lrn_res = client.get("/api/v1/learners/dashboard-summary", headers=auth_header(learner_user)).json()["data"]
    assert lrn_res["metrics"]["enrolled_courses"] == 1
    assert lrn_res["metrics"]["course_progress"] == 75.0
    assert lrn_res["metrics"]["mock_test_score"] == 82.0

    # 2. Add a 2nd enrollment with 25% progress and verify average becomes 50%
    c2 = Course(
        instructor_id=instructor_user.id,
        title="Web Programming",
        description="Comprehensive web development curriculum.",
        category="Software Engineering",
        status=CourseStatus.PUBLISHED.value,
        price=1000.0,
    )
    db_session.add(c2)
    db_session.commit()
    db_session.refresh(c2)

    enr2 = CourseEnrollment(
        user_id=learner_user.id,
        course_id=c2.id,
        status="ACTIVE",
        progress_percentage=25.0,
        completed_lessons_count=1,
    )
    db_session.add(enr2)
    db_session.commit()

    refreshed_lrn = client.get("/api/v1/learners/dashboard-summary", headers=auth_header(learner_user)).json()["data"]
    assert refreshed_lrn["metrics"]["enrolled_courses"] == 2
    assert refreshed_lrn["metrics"]["course_progress"] == 50.0  # (75 + 25) / 2

    # 3. Instructor verification: now has 2 courses, 1 distinct student, average progress across 2 enrollments is 50.0%
    inst_res = client.get("/api/v1/instructors/dashboard-summary", headers=auth_header(instructor_user)).json()["data"]
    assert inst_res["metrics"]["active_courses"] == 2
    assert inst_res["metrics"]["total_learners"] == 1
    assert inst_res["learner_performance"]["average_course_progress"] == 50.0


# ==============================================================================
# AC-4: Given a user is not authenticated, when the dashboard is accessed, then access must be denied.
# ==============================================================================

def test_unauthenticated_dashboard_access_denied(client: TestClient):
    """AC-4: Unauthenticated access to learner and instructor summaries returns HTTP 401."""
    res1 = client.get("/api/v1/learners/dashboard-summary")
    assert res1.status_code == 401
    assert res1.json()["error_code"] == "NOT_AUTHENTICATED"

    res2 = client.get("/api/v1/instructors/dashboard-summary")
    assert res2.status_code == 401
    assert res2.json()["error_code"] == "NOT_AUTHENTICATED"


def test_role_mismatch_dashboard_access_denied(
    client: TestClient,
    learner_user: User,
    instructor_user: User,
    company_user: User,
):
    """AC-4: Role mismatch returns HTTP 403 Forbidden."""
    # Learner cannot access instructor summary
    res_lrn = client.get("/api/v1/instructors/dashboard-summary", headers=auth_header(learner_user))
    assert res_lrn.status_code == 403
    assert res_lrn.json()["error_code"] == "INSUFFICIENT_ROLE_PERMISSIONS"

    # Instructor cannot access learner summary
    res_inst = client.get("/api/v1/learners/dashboard-summary", headers=auth_header(instructor_user))
    assert res_inst.status_code == 403
    assert res_inst.json()["error_code"] == "INSUFFICIENT_ROLE_PERMISSIONS"

    # Company cannot access either
    res_comp1 = client.get("/api/v1/learners/dashboard-summary", headers=auth_header(company_user))
    assert res_comp1.status_code == 403
    assert res_comp1.json()["error_code"] == "INSUFFICIENT_ROLE_PERMISSIONS"

    res_comp2 = client.get("/api/v1/instructors/dashboard-summary", headers=auth_header(company_user))
    assert res_comp2.status_code == 403
    assert res_comp2.json()["error_code"] == "INSUFFICIENT_ROLE_PERMISSIONS"


# ==============================================================================
# AC-5: Given dashboard data cannot be retrieved or is empty, graceful response is handled.
# ==============================================================================

def test_empty_state_graceful_handling(client: TestClient, db_session: Session):
    """AC-5: Brand new accounts with zero enrollments/courses return clean empty states without crashing."""
    new_learner = create_user(db_session, "brandnew.learner@example.com", UserRole.LEARNER, "Newbie", "Student")
    new_instructor = create_user(db_session, "brandnew.instructor@example.com", UserRole.INSTRUCTOR, "Fresh", "Teacher")

    # Learner empty state
    res_l = client.get("/api/v1/learners/dashboard-summary", headers=auth_header(new_learner))
    assert res_l.status_code == 200
    data_l = res_l.json()["data"]
    assert data_l["metrics"]["enrolled_courses"] == 0
    assert data_l["metrics"]["course_progress"] == 0.0
    assert data_l["metrics"]["mock_test_score"] == 0.0
    assert data_l["active_curriculum"] is None
    assert len(data_l["enrolled_courses"]) == 0

    # Instructor empty state
    res_i = client.get("/api/v1/instructors/dashboard-summary", headers=auth_header(new_instructor))
    assert res_i.status_code == 200
    data_i = res_i.json()["data"]
    assert data_i["metrics"]["active_courses"] == 0
    assert data_i["metrics"]["total_learners"] == 0
    assert len(data_i["my_courses"]) == 0
    assert data_i["learner_performance"]["average_course_progress"] == 0.0
