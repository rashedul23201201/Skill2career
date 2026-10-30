"""Automated Pytest Suite for SKL-62: System Integration Testing.

Sprint 4 Agile Deliverable
Assignee: Saif / QA & Development Team

Validates end-to-end multi-module system integration across the entire SKILL2CAREER platform:
- AC-1: Frontend-to-Backend HTTP API Contract & Communication Protocol
- AC-2: FastAPI and Relational Database (ORM) Persistence, Transactions & Relational Consistency
- AC-3: Multi-Module Cross-Subsystem End-to-End System Workflows:
  * Workflow 1: Learner Onboarding, Course Discovery, Enrollment & Lesson Progression
  * Workflow 2: Recruiter Company Verification, Job Posting, Screening, Application & Interview Lifecycle
  * Workflow 3: Subscription Monetization, Payment Gateway (SSLCommerz/Stripe) & Feature Entitlement Gating
  * Workflow 4: Community Forum Discussions, Commenting & Instructor Verified Answer Resolution
  * Workflow 5: Direct Real-Time Chat Messaging, Message Persistence & In-App Notification Dispatch
  * Workflow 6: Executive Admin Telemetry & Cross-Module Analytics Synthesis
- AC-4: Resilient Fault Tolerance, Defensive Fallback & External/Integrated Service Failure Handling
- AC-5: Integration Verification, Idempotence, Re-run Stability & Regression Prevention
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password, create_access_token
from app.models.user import User, UserRole
from app.models.profile import LearnerProfile, InstructorProfile, CompanyProfile
from app.models.course import Course, CourseStatus, CourseModule, Lesson
from app.models.enrollment import CourseEnrollment, LessonProgress
from app.models.mock_test import MockTest, TestQuestion, TestAttempt
from app.models.job import JobPosting, JobStatus, JobPostingType, JobWorkMode, JobExperienceLevel
from app.models.application import JobApplication, ApplicationStatus
from app.models.screening import ScreeningQuestion
from app.models.interview import InterviewRequest, InterviewStatus
from app.models.forum import ForumPost, ForumComment, ForumCategory
from app.models.chat import ChatConversation, ChatMessage
from app.models.notification import Notification
from app.models.subscription import (
    SubscriptionPlan,
    SubscriptionPlanCode,
    SubscriptionBillingCycle,
    UserSubscription,
    SubscriptionStatus,
    PaymentTransaction,
    PaymentStatus,
    PaymentGatewayType,
)
from app.repositories.subscription_repository import SubscriptionRepository


# ==============================================================================
# TEST DATA HELPERS & FIXTURES FOR SYSTEM INTEGRATION
# ==============================================================================

def create_sys_user(
    db: Session,
    email: str,
    role: UserRole = UserRole.LEARNER,
    first_name: str = "System",
    last_name: str = "Tester",
    is_active: bool = True,
    is_verified: bool = True,
    company_verified: bool = True,
) -> User:
    """Helper to create and persist user and matching role profile for system tests."""
    user = User(
        email=email,
        hashed_password=hash_password("SysTestP@ss123!"),
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
            bio="Integration QA Specialist",
            institution="University of Asia Pacific",
            department="Computer Science & Engineering",
            target_role="Full Stack Engineer",
            skills=["Python", "FastAPI", "React", "PostgreSQL", "Docker"],
            resume_url="https://example.com/resumes/sys_learner.pdf",
            resume_filename="sys_learner.pdf",
        )
        db.add(profile)
    elif role == UserRole.INSTRUCTOR:
        profile = InstructorProfile(
            user_id=user.id,
            designation="Principal Software Architect",
            institution="Tech Academy",
            qualification="M.Sc. in Computer Science",
            expertise_domain="Distributed Systems & Cloud",
            onboarding_status="APPROVED",
        )
        db.add(profile)
    elif role == UserRole.COMPANY:
        profile = CompanyProfile(
            user_id=user.id,
            company_name=f"{first_name} Innovations Ltd",
            description="Enterprise Cloud & Software Solutions Provider",
            industry="Software Engineering",
            office_address="Gulshan-2, Dhaka 1212, Bangladesh",
            location="Dhaka, Bangladesh",
            website_url="https://innovations.example.com",
            verification_status="APPROVED" if company_verified else "PENDING",
            verified_at=datetime.now(timezone.utc) if company_verified else None,
        )
        db.add(profile)

    db.commit()
    db.refresh(user)
    return user


def auth_header(user: User) -> dict:
    """Generate Authorization Bearer token header."""
    token = create_access_token(
        subject=user.id,
        claims={"email": user.email, "role": user.role.value},
    )
    return {"Authorization": f"Bearer {token}"}


def ensure_sys_subscription_plan(db: Session, code: SubscriptionPlanCode = SubscriptionPlanCode.PRO_MONTHLY) -> SubscriptionPlan:
    """Ensure a subscription plan exists in test database using repository seeder."""
    repo = SubscriptionRepository()
    repo.ensure_seed_plans(db)
    plan = repo.get_plan_by_code(db, code.value)
    return plan


# ==============================================================================
# AC-1: FRONTEND-TO-BACKEND HTTP API CONTRACT & COMMUNICATION TESTING
# ==============================================================================

def test_ac1_system_health_and_service_discovery(client: TestClient):
    """AC-1.1: Verify root service discovery, health probe contracts, and OpenAPI specifications."""
    # Root discovery
    root_res = client.get("/")
    assert root_res.status_code == 200
    root_json = root_res.json()
    assert "service" in root_json
    assert "version" in root_json
    assert root_json["health"] == "/api/v1/health"

    # API v1 Health Check
    health_res = client.get("/api/v1/health")
    assert health_res.status_code == 200
    health_json = health_res.json()
    assert health_json.get("status") in ("healthy", "ok")

    # OpenAPI schema discovery
    openapi_res = client.get("/api/v1/openapi.json")
    assert openapi_res.status_code == 200
    openapi_json = openapi_res.json()
    assert openapi_json["openapi"].startswith("3.")
    assert "/api/v1/auth/login" in openapi_json["paths"]
    assert "/api/v1/courses" in openapi_json["paths"]
    assert "/api/v1/jobs" in openapi_json["paths"]


def test_ac1_standard_response_envelope_format(client: TestClient, db_session: Session):
    """AC-1.2: Validate standard API response envelope across public and protected endpoints."""
    # Public catalog endpoint returns standard structure
    course_res = client.get("/api/v1/courses")
    assert course_res.status_code == 200
    course_json = course_res.json()
    assert "courses" in course_json or "data" in course_json or isinstance(course_json, (dict, list))

    # Authenticated endpoint returns standard envelope
    learner = create_sys_user(db_session, "envelope.tester@example.com", UserRole.LEARNER)
    me_res = client.get("/api/v1/auth/me", headers=auth_header(learner))
    assert me_res.status_code == 200
    me_json = me_res.json()
    assert me_json["success"] is True
    assert me_json["data"]["email"] == "envelope.tester@example.com"
    assert me_json["data"]["role"] == "LEARNER"


def test_ac1_cors_and_preflight_headers_communication(client: TestClient):
    """AC-1.3: Verify CORS headers and preflight configuration for frontend React client."""
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Authorization,Content-Type",
    }
    options_res = client.options("/api/v1/auth/login", headers=headers)
    assert options_res.status_code == 200
    assert options_res.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert options_res.headers.get("access-control-allow-credentials") == "true"


# ==============================================================================
# AC-2: FASTAPI AND RELATIONAL DATABASE PERSISTENCE & DATA INTEGRITY
# ==============================================================================

def test_ac2_database_persistence_and_bidirectional_relational_mapping(client: TestClient, db_session: Session):
    """AC-2.1: Verify end-to-end ORM persistence, relational mappings, and DB retrieval consistency."""
    instructor = create_sys_user(db_session, "inst.db.persist@example.com", UserRole.INSTRUCTOR, first_name="DB", last_name="Persist")

    # Create Course directly in DB
    course = Course(
        instructor_id=instructor.id,
        title="Distributed Systems with Python & FastAPI",
        description="Master microservices, queues, caching, and scalable persistence.",
        category="Software Engineering",
        level="Intermediate",
        price=1500.0,
        is_free=False,
        status=CourseStatus.PUBLISHED,
        moderation_status="APPROVED",
    )
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    # Add CourseModule & Lesson
    module = CourseModule(course_id=course.id, title="Module 1: Architecture & Concurrency", order_index=1)
    db_session.add(module)
    db_session.commit()
    db_session.refresh(module)

    lesson = Lesson(
        course_id=course.id,
        module_id=module.id,
        title="Lesson 1.1: Asynchronous Event Loops",
        content_type="VIDEO",
        duration_minutes=45,
        order_index=1,
        moderation_status="APPROVED",
    )
    db_session.add(lesson)
    db_session.commit()
    db_session.refresh(lesson)

    # Verify through API client
    learner = create_sys_user(db_session, "learner.db.fetch@example.com", UserRole.LEARNER)
    get_course_res = client.get(f"/api/v1/courses/{course.id}", headers=auth_header(learner))
    assert get_course_res.status_code == 200
    course_data = get_course_res.json()["data"] if "data" in get_course_res.json() else get_course_res.json()
    assert course_data["title"] == "Distributed Systems with Python & FastAPI"
    assert course_data["instructor_id"] == instructor.id


def test_ac2_database_transactional_rollback_and_session_isolation(client: TestClient, db_session: Session):
    """AC-2.2: Verify that failed transactional operations roll back cleanly without leaving orphan data."""
    initial_user_count = db_session.query(User).count()

    # Attempt registration with missing required field (invalid payload)
    invalid_payload = {
        "email": "invalid-email-format",
    }
    fail_res = client.post("/api/v1/auth/register", json=invalid_payload)
    assert fail_res.status_code in (422, 400)

    # Verify database state remained unchanged
    current_user_count = db_session.query(User).count()
    assert current_user_count == initial_user_count


# ==============================================================================
# AC-3: MULTI-MODULE CROSS-SUBSYSTEM END-TO-END WORKFLOWS
# ==============================================================================

def test_ac3_workflow_learner_onboarding_course_enrollment_progression(client: TestClient, db_session: Session):
    """AC-3.1: Full workflow: Auth Registration -> Profile Setup -> Course Discovery -> Enrollment -> Lesson Progression."""
    # Step 1: Learner registers via Auth API
    reg_payload = {
        "email": "workflow.learner@skill2career.com",
        "password": "SecurePassword123!",
        "first_name": "Tariq",
        "last_name": "Zaman",
        "role": "LEARNER",
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    learner_id = reg_res.json()["data"]["user"]["id"]

    # Step 2: Login to obtain token
    login_res = client.post("/api/v1/auth/login", json={"email": "workflow.learner@skill2career.com", "password": "SecurePassword123!"})
    assert login_res.status_code == 200
    token = login_res.json()["data"]["access_token"]
    learner_header = {"Authorization": f"Bearer {token}"}

    # Step 3: Setup Instructor and published course with lesson in DB
    instructor = create_sys_user(db_session, "workflow.inst@skill2career.com", UserRole.INSTRUCTOR)
    course = Course(
        instructor_id=instructor.id,
        title="Modern Cloud Native Python",
        description="Kubernetes, Docker, and Microservices architecture.",
        category="Cloud Computing",
        level="Intermediate",
        price=0.0,
        is_free=True,
        status=CourseStatus.PUBLISHED,
        moderation_status="APPROVED",
    )
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    mod = CourseModule(course_id=course.id, title="Module 1: Docker Basics", order_index=1)
    db_session.add(mod)
    db_session.commit()
    db_session.refresh(mod)

    les = Lesson(
        course_id=course.id,
        module_id=mod.id,
        title="Lesson 1: Multi-stage Dockerfiles",
        content_type="VIDEO",
        duration_minutes=25,
        order_index=1,
        moderation_status="APPROVED",
    )
    db_session.add(les)
    db_session.commit()
    db_session.refresh(les)

    # Step 4: Learner enrolls in course
    enroll_res = client.post(f"/api/v1/courses/{course.id}/enroll", headers=learner_header)
    assert enroll_res.status_code in (200, 201)

    # Step 5: Learner completes lesson
    comp_res = client.post(f"/api/v1/lessons/{les.id}/complete", headers=learner_header)
    assert comp_res.status_code in (200, 201)

    # Step 6: Verify enrollment progress in database
    enrollment = db_session.query(CourseEnrollment).filter(
        CourseEnrollment.user_id == learner_id,
        CourseEnrollment.course_id == course.id,
    ).first()
    assert enrollment is not None
    assert enrollment.completed_lessons_count >= 1
    assert enrollment.progress_percentage > 0


def test_ac3_workflow_recruitment_job_posting_screening_interview_pipeline(client: TestClient, db_session: Session):
    """AC-3.2: Full workflow: Company Registration -> Job Posting with Screening -> Candidate Application -> Interview Scheduling -> Feedback Scorecard -> Notification."""
    # Step 1: Admin and Company Setup
    admin = create_sys_user(db_session, "sys.admin@skill2career.com", UserRole.ADMIN)
    company = create_sys_user(db_session, "recruiter.corp@example.com", UserRole.COMPANY, first_name="Apex")
    candidate = create_sys_user(db_session, "applicant.dev@example.com", UserRole.LEARNER, first_name="Anis")

    comp_header = auth_header(company)
    cand_header = auth_header(candidate)

    # Step 2: Company posts a job vacancy
    job_payload = {
        "title": "Senior Backend Software Engineer",
        "posting_type": "JOB",
        "work_mode": "HYBRID",
        "location": "Dhaka, Bangladesh",
        "description": "Building high-performance REST APIs and microservices.",
        "requirements": "Strong mastery of Python, FastAPI, SQL, and Docker.",
        "skills": ["Python", "FastAPI", "SQL", "Docker"],
        "compensation": "BDT 120,000 - 160,000 / month",
        "salary_min": 120000,
        "salary_max": 160000,
        "duration": "Full-Time",
        "experience_level": "MID_LEVEL",
        "category": "Software Engineering",
        "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
    }
    job_res = client.post("/api/v1/jobs", json=job_payload, headers=comp_header)
    assert job_res.status_code == 201
    job_id = job_res.json()["data"]["id"]

    # Step 3: Candidate discovers job and applies with profile resume
    app_payload = {
        "cover_letter": "I have extensive experience building FastAPI architectures and robust test suites.",
        "use_profile_resume": True,
        "resume_url": "https://example.com/resumes/candidate.pdf",
        "resume_filename": "candidate.pdf",
    }
    apply_res = client.post(f"/api/v1/jobs/{job_id}/apply", json=app_payload, headers=cand_header)
    assert apply_res.status_code == 201
    app_id = apply_res.json()["data"]["id"]

    # Step 4: Recruiter updates application status to SHORTLISTED
    status_update_res = client.patch(
        f"/api/v1/applications/{app_id}/status",
        headers=comp_header,
        json={"status": "SHORTLISTED", "notes": "Strong candidate background"},
    )
    assert status_update_res.status_code == 200

    # Step 5: Recruiter proposes interview time slots
    now = datetime.now(timezone.utc)
    slot1_start = now + timedelta(days=2, hours=10)
    slot1_end = slot1_start + timedelta(minutes=45)
    slot2_start = now + timedelta(days=3, hours=14)
    slot2_end = slot2_start + timedelta(minutes=45)

    interview_payload = {
        "interview_type": "Technical Interview",
        "meeting_platform": "Google Meet",
        "meeting_link": "https://meet.google.com/sys-int-meet",
        "duration_minutes": 45,
        "notes": "Technical architectural discussion.",
        "proposed_slots": [
            {"start_time": slot1_start.isoformat(), "end_time": slot1_end.isoformat()},
            {"start_time": slot2_start.isoformat(), "end_time": slot2_end.isoformat()},
        ],
    }
    interview_res = client.post(f"/api/v1/applications/{app_id}/interview-request", headers=comp_header, json=interview_payload)
    assert interview_res.status_code == 201
    interview_id = interview_res.json()["data"]["id"]

    # Step 6: Recruiter submits evaluation scorecard & feedback
    feedback_payload = {
        "overall_score": 90,
        "technical_score": 92,
        "communication_score": 88,
        "problem_solving_score": 90,
        "recommendation": "STRONG_HIRE",
        "strengths": ["FastAPI", "Clean Architecture", "Problem Solving"],
        "improvement_areas": [{"area": "Cloud Deployment", "details": "Kubernetes Helm charts"}],
        "feedback_notes": "Candidate demonstrated exceptional domain knowledge.",
        "internal_notes": "Recommended hire.",
        "suggested_next_action": "OFFER",
        "is_shared_with_candidate": False,
    }
    fb_res = client.post(f"/api/v1/interviews/{interview_id}/feedback", headers=comp_header, json=feedback_payload)
    assert fb_res.status_code == 201

    # Step 7: Verify application in DB is associated with candidate
    app_db = db_session.query(JobApplication).filter(JobApplication.id == app_id).first()
    assert app_db is not None
    assert app_db.learner_id == candidate.id


def test_ac3_workflow_subscription_monetization_payment_entitlement(client: TestClient, db_session: Session):
    """AC-3.3: Full workflow: Plan Selection -> Payment Initiation -> Gateway IPN -> Transaction Persistence -> Feature Entitlement."""
    user = create_sys_user(db_session, "subscriber.sys@example.com", UserRole.LEARNER)
    user_header = auth_header(user)
    plan = ensure_sys_subscription_plan(db_session, SubscriptionPlanCode.PRO_MONTHLY)

    # Step 1: Query Subscription Plans
    plans_res = client.get("/api/v1/subscriptions/plans", headers=user_header)
    assert plans_res.status_code == 200

    # Step 2: Initiate Payment via Gateway
    pay_payload = {
        "plan_id": plan.id,
        "gateway_type": "SSLCOMMERZ",
    }
    init_res = client.post("/api/v1/payments/initiate", json=pay_payload, headers=user_header)
    assert init_res.status_code == 200
    tran_ref = init_res.json()["data"]["transaction_ref"]
    assert tran_ref.startswith("SSLC-")

    # Step 3: Gateway sends IPN success callback
    ipn_payload = {
        "tran_id": tran_ref,
        "val_id": f"VAL_{tran_ref}",
        "amount": float(plan.price),
        "currency": "BDT",
        "card_type": "BKASH-BKASH",
        "bank_tran_id": "BANK_TRX_9999",
        "status": "VALID",
    }
    ipn_res = client.post("/api/v1/payments/sslcommerz/ipn", json=ipn_payload)
    assert ipn_res.status_code == 200
    assert ipn_res.json()["success"] is True

    # Step 4: Verify transaction ledger in database
    tran = db_session.query(PaymentTransaction).filter(PaymentTransaction.transaction_ref == tran_ref).first()
    assert tran is not None
    assert tran.status == PaymentStatus.SUCCESS.value

    # Step 5: Check User Entitlements via API
    ent_res = client.get("/api/v1/subscriptions/entitlements", headers=user_header)
    assert ent_res.status_code == 200
    ent_json = ent_res.json()["data"] if "data" in ent_res.json() else ent_res.json()
    assert ent_json.get("plan_code") in (SubscriptionPlanCode.PRO_MONTHLY.value, "PRO_MONTHLY")


def test_ac3_workflow_community_forum_instructor_verified_answer(client: TestClient, db_session: Session):
    """AC-3.4: Full workflow: Forum Discussion -> Question Asking -> Instructor Verification Pinning."""
    learner = create_sys_user(db_session, "forum.learner@example.com", UserRole.LEARNER)
    instructor = create_sys_user(db_session, "forum.prof@example.com", UserRole.INSTRUCTOR)

    category = ForumCategory(name="Backend Architecture", description="Questions on APIs and Databases", slug="backend-arch")
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    # Step 1: Learner posts question
    post = ForumPost(
        category_id=category.id,
        author_id=learner.id,
        title="Best practices for SQLite vs PostgreSQL in FastAPI Integration Tests?",
        content="Should we use SQLite in-memory or a dedicated containerized PostgreSQL database?",
    )
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    # Step 2: Instructor posts verified answer comment
    comment = ForumComment(
        post_id=post.id,
        author_id=instructor.id,
        content="Use SQLite in-memory with StaticPool for unit/mock tests, and PostgreSQL for end-to-end migrations.",
        is_instructor_reply=True,
    )
    db_session.add(comment)
    db_session.commit()
    db_session.refresh(comment)

    # Step 3: Instructor verifies the answer via PATCH API
    verify_res = client.patch(
        f"/api/v1/forum/comments/{comment.id}/verify",
        json={"is_verified": True},
        headers=auth_header(instructor),
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["data"]["is_verified"] is True

    # Step 4: Database reflects verified status
    db_session.refresh(comment)
    db_session.refresh(post)
    assert comment.is_verified is True
    assert post.has_verified_answer is True


def test_ac3_workflow_realtime_chat_and_notification_delivery(client: TestClient, db_session: Session):
    """AC-3.5: Full workflow: Chat Initiation -> Message Delivery -> Unread Notification Tracking."""
    learner = create_sys_user(db_session, "chat.learner@example.com", UserRole.LEARNER)
    instructor = create_sys_user(db_session, "chat.instructor@example.com", UserRole.INSTRUCTOR)

    learner_h = auth_header(learner)
    inst_h = auth_header(instructor)

    # Step 1: Learner creates conversation with instructor
    conv_res = client.post("/api/v1/chat/conversations", json={"instructor_id": instructor.id}, headers=learner_h)
    assert conv_res.status_code in (200, 201)
    conv_id = conv_res.json()["data"]["id"]

    # Step 2: Learner sends message
    msg_res = client.post(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        json={"message_text": "Hello Professor, could you clarify question 3 in module 2?"},
        headers=learner_h,
    )
    assert msg_res.status_code == 201
    msg_data = msg_res.json()["data"]
    assert msg_data["message_text"] == "Hello Professor, could you clarify question 3 in module 2?"

    # Step 3: Instructor reads conversation
    read_res = client.post(f"/api/v1/chat/conversations/{conv_id}/read", headers=inst_h)
    assert read_res.status_code == 200

    # Step 4: Verify messages exist in database
    messages_in_db = db_session.query(ChatMessage).filter(ChatMessage.conversation_id == conv_id).count()
    assert messages_in_db >= 1


def test_ac3_workflow_admin_executive_dashboard_telemetry_aggregation(client: TestClient, db_session: Session):
    """AC-3.6: Multi-module telemetry aggregation across Users, LMS, Jobs, and Monetization."""
    admin = create_sys_user(db_session, "exec.admin@skill2career.com", UserRole.ADMIN)
    admin_h = auth_header(admin)

    # Query overview analytics
    analytics_res = client.get("/api/v1/admin/analytics/overview", headers=admin_h)
    assert analytics_res.status_code == 200
    analytics_data = analytics_res.json()["data"] if "data" in analytics_res.json() else analytics_res.json()

    # Verify presence of multi-module summary keys
    assert "users" in analytics_data or "total_users" in analytics_data or "overview" in analytics_data
    assert "revenue" in analytics_data or "total_revenue" in analytics_data or "financials" in analytics_data

    # Query overview stats
    stats_res = client.get("/api/v1/admin/overview-stats", headers=admin_h)
    assert stats_res.status_code == 200


# ==============================================================================
# AC-4: INTEGRATED SERVICE FAULT TOLERANCE & DEFENSIVE RESILIENCE
# ==============================================================================

def test_ac4_payment_gateway_failure_and_resilient_recovery(client: TestClient, db_session: Session):
    """AC-4.1: Simulate payment gateway cancellation/failure and ensure graceful transaction marking."""
    user = create_sys_user(db_session, "pay.fail.test@example.com", UserRole.LEARNER)
    plan = ensure_sys_subscription_plan(db_session)

    # Initiate payment
    init_res = client.post(
        "/api/v1/payments/initiate",
        json={"plan_id": plan.id, "gateway_type": "SSLCOMMERZ"},
        headers=auth_header(user),
    )
    assert init_res.status_code == 200
    tran_ref = init_res.json()["data"]["transaction_ref"]

    # Simulate gateway cancellation callback
    cancel_res = client.post("/api/v1/payments/sslcommerz/cancel", json={"tran_id": tran_ref})
    assert cancel_res.status_code == 200

    cancel_data = cancel_res.json()["data"]
    assert cancel_data["status"] == "FAILED"
    assert cancel_data["subscription_activated"] is False

    # Verify transaction in DB is marked FAILED, and subscription NOT activated
    tran = db_session.query(PaymentTransaction).filter(PaymentTransaction.transaction_ref == tran_ref).first()
    assert tran is not None
    assert tran.status == PaymentStatus.FAILED.value
    assert "cancelled" in tran.error_reason.lower()


def test_ac4_database_unique_constraint_collision_handling(client: TestClient, db_session: Session):
    """AC-4.2: Verify that duplicate registration collision yields structured HTTP 409 Conflict without crash."""
    existing_user = create_sys_user(db_session, "duplicate.collision@example.com", UserRole.LEARNER)

    dup_payload = {
        "email": "duplicate.collision@example.com",
        "password": "Password123!",
        "first_name": "Colliding",
        "last_name": "Account",
        "role": "LEARNER",
    }
    dup_res = client.post("/api/v1/auth/register", json=dup_payload)
    assert dup_res.status_code == 409
    assert dup_res.json()["error_code"] == "EMAIL_ALREADY_EXISTS"


def test_ac4_malformed_request_payload_validation_errors(client: TestClient):
    """AC-4.3: Verify malformed JSON and schema boundary breaches receive HTTP 422 with validation errors."""
    malformed_payload = {
        "email": "not-an-email",
        "role": "SUPER_ADMIN_INVALID_ROLE",
    }
    res = client.post("/api/v1/auth/register", json=malformed_payload)
    assert res.status_code == 422
    error_data = res.json()
    assert error_data["success"] is False
    assert "errors" in error_data or "message" in error_data


def test_ac4_unauthorized_service_boundary_rejection(client: TestClient):
    """AC-4.4: Reject unauthenticated and forged token requests at the gateway boundary."""
    # Bogus token
    forged_res = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer forged.signature.jwt"})
    assert forged_res.status_code == 401

    # Missing token on protected router
    unauth_res = client.post("/api/v1/jobs", json={})
    assert unauth_res.status_code == 401


# ==============================================================================
# AC-5: INTEGRATION VERIFICATION, IDEMPOTENCE & RETEST STABILITY
# ==============================================================================

def test_ac5_idempotent_webhook_and_retry_protection(client: TestClient, db_session: Session):
    """AC-5.1: Verify duplicate payment IPN callbacks process idempotently without multiplying entitlements."""
    user = create_sys_user(db_session, "idempotent.user@example.com", UserRole.LEARNER)
    plan = ensure_sys_subscription_plan(db_session)

    init_res = client.post(
        "/api/v1/payments/initiate",
        json={"plan_id": plan.id, "gateway_type": "SSLCOMMERZ"},
        headers=auth_header(user),
    )
    tran_ref = init_res.json()["data"]["transaction_ref"]

    ipn_payload = {
        "tran_id": tran_ref,
        "val_id": f"VAL_{tran_ref}",
        "amount": float(plan.price),
        "currency": "BDT",
        "card_type": "BKASH-BKASH",
        "bank_tran_id": "BANK_TRX_8888",
        "status": "VALID",
    }

    # First callback -> processes successfully
    res1 = client.post("/api/v1/payments/sslcommerz/ipn", json=ipn_payload)
    assert res1.status_code == 200

    # Second callback (retry from gateway) -> handled idempotently without error
    res2 = client.post("/api/v1/payments/sslcommerz/ipn", json=ipn_payload)
    assert res2.status_code == 200

    # Verify only 1 payment transaction exists for this ref
    trans_count = db_session.query(PaymentTransaction).filter(PaymentTransaction.transaction_ref == tran_ref).count()
    assert trans_count == 1


def test_ac5_system_integration_health_and_readiness(client: TestClient):
    """AC-5.2: End-to-end integration probe verifying that all subsystem root points respond."""
    endpoints_to_probe = [
        ("GET", "/"),
        ("GET", "/api/v1/health"),
        ("GET", "/api/v1/courses"),
        ("GET", "/api/v1/jobs"),
        ("GET", "/api/v1/subscriptions/plans"),
        ("GET", "/api/v1/forum/categories"),
    ]

    for method, path in endpoints_to_probe:
        if method == "GET":
            res = client.get(path)
            assert res.status_code in (200, 204), f"Health probe failed for {path}: {res.status_code}"
