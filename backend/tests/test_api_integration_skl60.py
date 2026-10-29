"""Automated Pytest suite for API Integration Testing (SKL-60).

Sprint 4: Advanced Integrations, Dashboards & Final Testing
Assignee: Muktadir (Member 3)

Validates complete cross-module and multi-layer API integration workflows:
- AC-1: User Lifecycle & RBAC Cross-Role Authorization Matrix
- AC-2: End-to-End LMS Course Creation, Moderation, Enrollment & Learning Progression
- AC-3: End-to-End Recruitment Pipeline: Job Posting, Screening, Application, Interview & Offering
- AC-4: Mock Assessment Engine: Creation, Attempt, Auto-Grading & Performance Analysis
- AC-5: Subscription Monetization, Payment Gateways & Entitlement Gating Lifecycle
- AC-6: Community Forum Discussions & Instructor Verified Answer Pinning
- AC-7: Real-Time Direct Messaging, Unread Count & Participant Privacy Barriers
- AC-8: Event-Driven Notification Lifecycle, Drawer Ingestion & Read State Transitions
- AC-9: Cross-Subsystem Telemetry, Analytics Funnel & Role Dashboard Synthesis
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password, create_access_token
from app.models.user import User, UserRole
from app.models.profile import LearnerProfile, InstructorProfile, CompanyProfile
from app.models.course import Course, CourseModule, Lesson, CourseStatus
from app.models.enrollment import CourseEnrollment, LessonProgress
from app.models.mock_test import MockTest, TestQuestion, TestAttempt
from app.models.job import JobPosting, JobStatus, JobPostingType, JobWorkMode, JobExperienceLevel, SavedJob
from app.models.application import JobApplication, ApplicationStatus
from app.models.screening import ScreeningQuestion
from app.models.interview import InterviewRequest, InterviewStatus, InterviewSlot
from app.models.forum import ForumPost, ForumComment, ForumCategory
from app.models.chat import ChatConversation, ChatMessage
from app.models.notification import Notification
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


# ==============================================================================
# SEEDING & AUTHENTICATION HELPERS
# ==============================================================================

def create_test_user(
    db: Session,
    email: str,
    role: UserRole = UserRole.LEARNER,
    first_name: str = "Test",
    last_name: str = "User",
    is_active: bool = True,
    is_verified: bool = True,
) -> User:
    """Helper to create and persist user records with predefined roles."""
    user = User(
        email=email,
        hashed_password=hash_password("Password123!"),
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
            target_role="Fullstack Software Engineer",
            skills={"primary": ["Python", "FastAPI", "React"]},
            bio="Passionate engineer building scalable applications",
            resume_url="https://example.com/resumes/candidate.pdf",
            resume_filename="candidate.pdf",
        )
        db.add(profile)
        db.commit()
    elif role == UserRole.INSTRUCTOR:
        profile = InstructorProfile(
            user_id=user.id,
            designation="Assistant Professor & Tech Lead",
            institution="University of Asia Pacific",
            onboarding_status="APPROVED",
        )
        db.add(profile)
        db.commit()
    elif role == UserRole.COMPANY:
        profile = CompanyProfile(
            user_id=user.id,
            company_name=f"{first_name} Technologies",
            industry="Software & IT Services",
            verification_status="APPROVED",
            location="Dhaka, Bangladesh",
            website_url="https://techcorp.example.com",
            office_address="Dhaka, Bangladesh",
        )
        db.add(profile)
        db.commit()

    return user


def auth_header(user: User) -> dict:
    """Generate Authorization Bearer token header."""
    token = create_access_token(
        subject=user.id,
        claims={"email": user.email, "role": user.role.value},
    )
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# INTEGRATION TEST SUITES
# ==============================================================================

def test_user_lifecycle_and_rbac_integration(client: TestClient, db_session: Session):
    """AC-1: End-to-end user registration, authentication, token refresh, and cross-role authorization bounds."""
    # 1. Register a new Learner
    reg_payload = {
        "email": "fresh.learner@skill2career.com",
        "password": "SecurePassword123!",
        "first_name": "Rahim",
        "last_name": "Chowdhury",
        "role": "LEARNER",
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201, reg_res.text
    reg_json = reg_res.json()
    assert reg_json["success"] is True
    assert reg_json["data"]["user"]["email"] == "fresh.learner@skill2career.com"

    # 2. Login with credentials
    login_payload = {
        "email": "fresh.learner@skill2career.com",
        "password": "SecurePassword123!",
    }
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    token_data = login_res.json()["data"]
    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]
    assert access_token and refresh_token

    # 3. Refresh the token
    refresh_res = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_res.status_code == 200
    new_token_data = refresh_res.json()["data"]
    assert new_token_data["access_token"] is not None

    # 4. Resolve current user profile via /auth/me
    headers = {"Authorization": f"Bearer {access_token}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()["data"]
    assert me_data["email"] == "fresh.learner@skill2career.com"
    assert me_data["role"] == "LEARNER"

    # 5. RBAC Cross-Role Barriers
    # Learner forbidden from creating corporate job posting
    job_forbidden_res = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "title": "Hacker Job",
            "description": "Unauthorized posting",
            "posting_type": "Job",
            "work_mode": "Remote",
            "location": "Dhaka",
            "requirements": "None",
            "compensation": "100k",
        },
    )
    assert job_forbidden_res.status_code == 403

    # Learner forbidden from administrative telemetry
    admin_forbidden_res = client.get("/api/v1/admin/analytics/overview", headers=headers)
    assert admin_forbidden_res.status_code == 403

    # Unauthenticated calls to protected profile blocked with 401
    unauth_res = client.get("/api/v1/learners/profile")
    assert unauth_res.status_code == 401


def test_lms_course_enrollment_and_progress_integration(client: TestClient, db_session: Session):
    """AC-2: End-to-end Course authoring, moderation approval, learner enrollment, and progress progression."""
    instructor = create_test_user(db_session, "inst.lead@skill2career.com", UserRole.INSTRUCTOR, "Tareq", "Hasan")
    learner = create_test_user(db_session, "student.progress@skill2career.com", UserRole.LEARNER, "Sumaiya", "Akter")
    admin = create_test_user(db_session, "admin.moderator@skill2career.com", UserRole.ADMIN, "Admin", "Super")

    inst_headers = auth_header(instructor)
    learner_headers = auth_header(learner)
    admin_headers = auth_header(admin)

    # 1. Instructor authors a new course
    course_payload = {
        "title": "FastAPI & Distributed Microservices in Python",
        "description": "Comprehensive practical course covering scalable backend engineering.",
        "category": "Software Engineering",
        "level": "Intermediate",
        "price": 2000.0,
        "is_free": False,
    }
    course_res = client.post("/api/v1/courses", headers=inst_headers, json=course_payload)
    assert course_res.status_code == 201, course_res.text
    course_id = course_res.json()["data"]["id"]

    # 2. Instructor adds a curriculum module and lesson
    module_payload = {
        "title": "Module 1: Architecture Foundations",
        "order_index": 1,
    }
    module_res = client.post(f"/api/v1/courses/{course_id}/modules", headers=inst_headers, json=module_payload)
    assert module_res.status_code == 201
    module_id = module_res.json()["data"]["id"]

    lesson_payload = {
        "title": "Lesson 1: FastAPI Dependency Injection & Sessions",
        "module_id": module_id,
        "content_type": "video",
        "duration_minutes": 25,
    }
    lesson_res = client.post(f"/api/v1/courses/{course_id}/lessons", headers=inst_headers, json=lesson_payload)
    assert lesson_res.status_code == 201, lesson_res.text
    lesson_id = lesson_res.json()["data"]["id"]

    # 3. Admin reviews and moderates the course to APPROVED status
    mod_res = client.post(
        f"/api/v1/admin/moderation/courses/{course_id}/approve",
        headers=admin_headers,
        json={"notes": "Meets academic quality standards."},
    )
    assert mod_res.status_code == 200
    assert mod_res.json()["data"]["moderation_status"] == "APPROVED"

    # Also publish course status
    client.patch(
        f"/api/v1/courses/{course_id}/status",
        headers=inst_headers,
        json={"status": "PUBLISHED"},
    )

    # 4. Learner searches catalog and views the published course
    catalog_res = client.get("/api/v1/courses?search=FastAPI")
    assert catalog_res.status_code == 200
    courses_list = catalog_res.json()["data"]["items"]
    assert any(c["id"] == course_id for c in courses_list)

    # 5. Learner enrolls into the course
    enroll_res = client.post(f"/api/v1/courses/{course_id}/enroll", headers=learner_headers)
    assert enroll_res.status_code == 201
    enroll_data = enroll_res.json()["data"]
    assert enroll_data["course_id"] == course_id

    # 6. Learner completes the course lessons
    course_detail_res = client.get(f"/api/v1/courses/{course_id}")
    assert course_detail_res.status_code == 200
    for les in course_detail_res.json()["data"]["lessons"]:
        client.post(
            f"/api/v1/lessons/{les['id']}/complete",
            headers=learner_headers,
            json={"is_completed": True},
        )

    # 7. Course progress reaches 100%
    prog_res = client.get(f"/api/v1/courses/{course_id}/progress", headers=learner_headers)
    assert prog_res.status_code == 200
    prog_data = prog_res.json()["data"]
    assert prog_data["completed_lessons"] >= 1
    assert prog_data["progress_percentage"] == 100.0

    # 8. Verify progress is reflected on Learner Dashboard Summary
    learner_dash_res = client.get("/api/v1/learners/dashboard-summary", headers=learner_headers)
    assert learner_dash_res.status_code == 200
    learner_dash_data = learner_dash_res.json()["data"]
    assert learner_dash_data["metrics"]["enrolled_courses"] >= 1


def test_recruitment_screening_application_interview_pipeline_integration(client: TestClient, db_session: Session):
    """AC-3: End-to-end recruitment lifecycle from job post, screening questions, candidate application to interview."""
    company_user = create_test_user(db_session, "hr@brainstation-23.com", UserRole.COMPANY, "Brain Station", "HR")
    candidate = create_test_user(db_session, "candidate.arif@skill2career.com", UserRole.LEARNER, "Ariful", "Islam")

    comp_headers = auth_header(company_user)
    cand_headers = auth_header(candidate)

    # 1. Company posts an active job opening
    job_payload = {
        "title": "Backend Software Engineer (FastAPI & Cloud)",
        "description": "Lead microservices development and architect enterprise APIs.",
        "posting_type": "Job",
        "work_mode": "Hybrid",
        "location": "Mohakhali, Dhaka",
        "requirements": "3+ years Python, FastAPI, Docker, PostgreSQL/MySQL",
        "skills": ["Python", "FastAPI", "Docker", "SQL"],
        "compensation": "75,000 - 95,000 BDT/month",
        "experience_level": "Mid-Level",
        "category": "Software Engineering",
    }
    job_res = client.post("/api/v1/jobs", headers=comp_headers, json=job_payload)
    assert job_res.status_code == 201, job_res.text
    job_id = job_res.json()["data"]["id"]

    # 2. Company adds custom screening questions
    q_payload = {
        "question_text": "Years of hands-on Python/FastAPI experience?",
        "question_type": "NUMERIC",
        "is_required": True,
        "is_deal_breaker": False,
        "weight": 20,
    }
    q_res = client.post(f"/api/v1/jobs/{job_id}/screening-questions", headers=comp_headers, json=q_payload)
    assert q_res.status_code == 201
    question_id = q_res.json()["data"]["id"]

    # 3. Candidate searches vacancies and saves the job
    search_res = client.get("/api/v1/jobs?search=Backend")
    assert search_res.status_code == 200

    save_res = client.post(f"/api/v1/jobs/{job_id}/save", headers=cand_headers)
    assert save_res.status_code == 200
    assert save_res.json()["data"]["is_saved"] is True

    # 4. Candidate applies for the job with profile resume
    apply_payload = {
        "cover_letter": "I have extensive experience building FastAPI architectures and robust test suites.",
        "use_profile_resume": True,
        "resume_url": "https://example.com/resumes/candidate.pdf",
        "resume_filename": "candidate.pdf",
    }
    apply_res = client.post(f"/api/v1/jobs/{job_id}/apply", headers=cand_headers, json=apply_payload)
    assert apply_res.status_code == 201, apply_res.text
    app_id = apply_res.json()["data"]["id"]

    # 5. Recruiter reviews application details and shortlists candidate
    app_detail_res = client.get(f"/api/v1/applications/{app_id}", headers=comp_headers)
    assert app_detail_res.status_code == 200

    status_update_res = client.patch(
        f"/api/v1/applications/{app_id}/status",
        headers=comp_headers,
        json={"status": "SHORTLISTED", "notes": "Strong candidate background"},
    )
    assert status_update_res.status_code == 200
    assert status_update_res.json()["data"]["status"] == "SHORTLISTED"

    # 6. Recruiter proposes interview time slots
    now = datetime.now(timezone.utc)
    slot1_start = now + timedelta(days=2, hours=10)
    slot1_end = slot1_start + timedelta(minutes=45)
    slot2_start = now + timedelta(days=3, hours=14)
    slot2_end = slot2_start + timedelta(minutes=45)

    interview_payload = {
        "interview_type": "Technical Interview",
        "meeting_platform": "Google Meet",
        "meeting_link": "https://meet.google.com/abc-defg-hij",
        "duration_minutes": 45,
        "notes": "Technical architectural discussion.",
        "proposed_slots": [
            {"start_time": slot1_start.isoformat(), "end_time": slot1_end.isoformat()},
            {"start_time": slot2_start.isoformat(), "end_time": slot2_end.isoformat()},
        ],
    }
    interview_res = client.post(f"/api/v1/applications/{app_id}/interview-request", headers=comp_headers, json=interview_payload)
    assert interview_res.status_code == 201, interview_res.text
    interview_id = interview_res.json()["data"]["id"]

    # 7. Candidate confirms the interview slot
    interview_detail_res = client.get(f"/api/v1/interviews/{interview_id}", headers=cand_headers)
    assert interview_detail_res.status_code == 200
    available_slots = interview_detail_res.json()["data"]["slots"]
    chosen_slot_id = available_slots[0]["id"]

    confirm_res = client.post(
        f"/api/v1/interviews/{interview_id}/select-slot",
        headers=cand_headers,
        json={"slot_id": chosen_slot_id},
    )
    assert confirm_res.status_code == 200
    assert confirm_res.json()["data"]["status"] == "SCHEDULED"

    # 8. Recruiter submits evaluation scorecard & feedback
    feedback_payload = {
        "overall_score": 88,
        "technical_score": 92,
        "communication_score": 85,
        "problem_solving_score": 90,
        "recommendation": "STRONG_HIRE",
        "strengths": ["FastAPI", "Clean Architecture", "Problem Solving"],
        "improvement_areas": [{"area": "Cloud Deployment", "details": "Kubernetes Helm charts"}],
        "feedback_notes": "Extremely promising engineering talent.",
        "internal_notes": "Target salary 85,000 BDT.",
        "suggested_next_action": "OFFER",
        "is_shared_with_candidate": False,
    }
    fb_res = client.post(f"/api/v1/interviews/{interview_id}/feedback", headers=comp_headers, json=feedback_payload)
    assert fb_res.status_code == 201, fb_res.text

    # 9. Recruiter advances candidate status to OFFERED
    offered_res = client.patch(
        f"/api/v1/applications/{app_id}/status",
        headers=comp_headers,
        json={"status": "OFFERED", "notes": "Offer letter dispatched"},
    )
    assert offered_res.status_code == 200
    assert offered_res.json()["data"]["status"] == "OFFERED"

    # 10. Company Dashboard metrics reflect the updated recruitment data
    dash_metrics_res = client.get("/api/v1/companies/dashboard/metrics", headers=comp_headers)
    assert dash_metrics_res.status_code == 200
    metrics = dash_metrics_res.json()["data"]
    assert metrics["active_jobs"] >= 1
    assert metrics["total_applications"] >= 1


def test_mock_test_attempt_and_results_integration(client: TestClient, db_session: Session):
    """AC-4: End-to-end Mock assessment lifecycle: authoring, attempt start, timer submission, scoring & performance."""
    instructor = create_test_user(db_session, "inst.eval@skill2career.com", UserRole.INSTRUCTOR, "Farhan", "Labib")
    learner = create_test_user(db_session, "learner.examinee@skill2career.com", UserRole.LEARNER, "Nadia", "Sultana")
    admin = create_test_user(db_session, "admin.testeval@skill2career.com", UserRole.ADMIN, "Admin", "Eval")

    inst_headers = auth_header(instructor)
    learner_headers = auth_header(learner)
    admin_headers = auth_header(admin)

    # 1. Instructor creates mock test
    test_payload = {
        "title": "Python Data Structures & Complexity Evaluation",
        "description": "Assess proficiency in algorithm analysis and memory complexity.",
        "category": "Programming",
        "duration_minutes": 15,
        "passing_score": 50,
        "status": "DRAFT",
    }
    create_res = client.post("/api/v1/mock-tests", headers=inst_headers, json=test_payload)
    assert create_res.status_code == 201, create_res.text
    test_id = create_res.json()["data"]["id"]

    # 2. Add question to mock test
    q_payload = {
        "question_text": "What is the average time complexity of searching in a Python dictionary (hash table)?",
        "options": ["O(1)", "O(n)", "O(log n)", "O(n^2)"],
        "correct_option": "A",
        "marks": 50,
        "explanation": "Dictionary key lookups use hash tables which operate in amortized O(1) time.",
        "order_index": 0,
    }
    add_q_res = client.post(f"/api/v1/mock-tests/{test_id}/questions", headers=inst_headers, json=q_payload)
    assert add_q_res.status_code == 201, add_q_res.text
    q1_id = add_q_res.json()["data"]["id"]

    # 3. Admin approves mock test moderation and publish
    mod_res = client.post(
        f"/api/v1/admin/moderation/mock-tests/{test_id}/approve",
        headers=admin_headers,
        json={"notes": "Valid assessment"},
    )
    assert mod_res.status_code == 200
    assert mod_res.json()["data"]["moderation_status"] == "APPROVED"
    client.patch(f"/api/v1/mock-tests/{test_id}/status", headers=inst_headers, json={"status": "PUBLISHED"})

    # 4. Learner starts the test attempt session
    start_res = client.post(f"/api/v1/mock-tests/{test_id}/start-attempt", headers=learner_headers)
    assert start_res.status_code == 201, start_res.text
    attempt_id = start_res.json()["data"]["id"]

    # 5. Learner submits answers
    submit_payload = {
        "answers": {str(q1_id): "A"},
        "marked_for_review": [],
    }
    submit_res = client.post(f"/api/v1/attempts/{attempt_id}/submit-answers", headers=learner_headers, json=submit_payload)
    assert submit_res.status_code == 200, submit_res.text
    submit_data = submit_res.json()["data"]
    assert submit_data["status"] in ("SUBMITTED", "COMPLETED")

    # 6. Retrieve detailed performance result
    result_res = client.get(f"/api/v1/attempts/{attempt_id}/result", headers=learner_headers)
    assert result_res.status_code == 200
    res_data = result_res.json()["data"]
    assert res_data["is_passed"] is True
    assert res_data["total_score"] >= 50


def test_subscription_payment_gateway_and_entitlements_integration(client: TestClient, db_session: Session):
    """AC-5: End-to-end monetization: plan retrieval, sandbox payment initiation, webhook verification & entitlement gating."""
    repo = SubscriptionRepository()
    repo.ensure_seed_plans(db_session)

    learner = create_test_user(db_session, "pro.buyer@skill2career.com", UserRole.LEARNER, "Tariq", "Zia")
    admin = create_test_user(db_session, "admin.finance@skill2career.com", UserRole.ADMIN, "Admin", "Finance")

    learner_headers = auth_header(learner)
    admin_headers = auth_header(admin)

    # 1. Query available subscription plans catalog
    plans_res = client.get("/api/v1/subscriptions/plans")
    assert plans_res.status_code == 200
    plans = plans_res.json()["data"]
    assert len(plans) >= 1
    monthly_plan = next((p for p in plans if p["code"] == SubscriptionPlanCode.PRO_MONTHLY.value), plans[0])

    # 2. Initiate Local Payment Session (SSLCommerz)
    init_payload = {
        "plan_id": monthly_plan["id"],
        "gateway_type": "SSLCOMMERZ",
        "payment_method": "bKash Auto-Debit",
    }
    init_res = client.post("/api/v1/payments/initiate", headers=learner_headers, json=init_payload)
    assert init_res.status_code == 200, init_res.text
    init_data = init_res.json()["data"]
    txn_ref = init_data["transaction_ref"]
    assert txn_ref.startswith("SSLC-")

    # 3. Simulate SSLCommerz IPN webhook verification
    ipn_payload = {
        "tran_id": txn_ref,
        "val_id": f"VAL_{txn_ref}",
        "amount": float(monthly_plan["price"]),
        "currency": "BDT",
        "card_type": "BKASH-BKASH",
        "bank_tran_id": f"BANK_{txn_ref}",
        "status": "VALID",
    }
    ipn_res = client.post("/api/v1/payments/sslcommerz/ipn", json=ipn_payload)
    assert ipn_res.status_code == 200, ipn_res.text
    assert ipn_res.json()["success"] is True

    # 4. Verify Entitlement Gating Check
    sub_res = client.get("/api/v1/subscriptions/my-subscription", headers=learner_headers)
    assert sub_res.status_code == 200
    sub_data = sub_res.json()["data"]
    assert sub_data["status"] == SubscriptionStatus.ACTIVE.value
    assert sub_data["plan"]["code"] == monthly_plan["code"]
    assert sub_data["is_pro"] is True

    # 5. User personal transaction history contains successful record
    hist_res = client.get("/api/v1/transactions/my-history", headers=learner_headers)
    assert hist_res.status_code == 200
    history_items = hist_res.json()["data"]
    assert any(item["transaction_ref"] == txn_ref for item in history_items)

    # 6. Admin Revenue Analytics Telemetry reflects the new transaction
    admin_rev_res = client.get("/api/v1/admin/analytics/revenue", headers=admin_headers)
    assert admin_rev_res.status_code == 200
    rev_data = admin_rev_res.json()["data"]
    assert rev_data["total_revenue"] >= float(monthly_plan["price"])


def test_forum_discussions_and_verified_answers_integration(client: TestClient, db_session: Session):
    """AC-6: Forum post creation, peer commenting, instructor answer verification and pinned badge retrieval."""
    learner = create_test_user(db_session, "forum.learner@skill2career.com", UserRole.LEARNER, "Anis", "Haque")
    instructor = create_test_user(db_session, "forum.mentor@skill2career.com", UserRole.INSTRUCTOR, "Dr. Kamal", "Hossain")

    # Ensure a valid forum category exists
    cat = ForumCategory(
        name="Software Engineering Discussions",
        slug="software-engineering-discussions",
        description="Software architecture and coding discussions",
    )
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)

    learner_headers = auth_header(learner)
    inst_headers = auth_header(instructor)

    # 1. Author a new discussion thread
    post_payload = {
        "title": "Optimizing SQLAlchemy 2.0 async queries with FastAPI",
        "content": "What is the recommended approach for preventing N+1 queries when loading nested course relationships?",
        "category_id": cat.id,
    }
    post_res = client.post("/api/v1/forum/posts", headers=learner_headers, json=post_payload)
    assert post_res.status_code == 201, post_res.text
    post_id = post_res.json()["data"]["id"]

    # 2. Peer likes the post
    like_res = client.post(f"/api/v1/forum/posts/{post_id}/like", headers=inst_headers)
    assert like_res.status_code == 200
    assert like_res.json()["data"]["is_liked"] is True

    # 3. Instructor adds a detailed expert answer
    comment_payload = {
        "content": "Use selectinload or joinedload options in SQLAlchemy 2.0 select statements to eagerly fetch relations in 1 query.",
    }
    comment_res = client.post(f"/api/v1/forum/posts/{post_id}/comments", headers=inst_headers, json=comment_payload)
    assert comment_res.status_code == 201, comment_res.text
    comment_id = comment_res.json()["data"]["id"]

    # 4. Instructor marks the answer as verified
    verify_res = client.patch(f"/api/v1/forum/comments/{comment_id}/verify", headers=inst_headers)
    assert verify_res.status_code == 200
    assert verify_res.json()["data"]["is_verified"] is True

    # 5. Fetch post detail: verified comment is retrieved
    detail_res = client.get(f"/api/v1/forum/posts/{post_id}", headers=learner_headers)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()["data"]
    assert detail_data["has_verified_answer"] is True
    comments = detail_data["comments"]
    assert any(c["id"] == comment_id and c["is_verified"] is True for c in comments)


def test_chat_direct_messaging_integration(client: TestClient, db_session: Session):
    """AC-7: Real-time direct chat conversation initiation, message exchange, unread counters, and participant bounds."""
    learner = create_test_user(db_session, "chat.learner@skill2career.com", UserRole.LEARNER, "Sadia", "Jahan")
    instructor = create_test_user(db_session, "chat.mentor@skill2career.com", UserRole.INSTRUCTOR, "Farhana", "Kabir")
    stranger = create_test_user(db_session, "chat.stranger@skill2career.com", UserRole.LEARNER, "Intruder", "Bob")

    learner_headers = auth_header(learner)
    inst_headers = auth_header(instructor)
    stranger_headers = auth_header(stranger)

    # 1. Learner initiates conversation with Instructor
    conv_res = client.post(
        "/api/v1/chat/conversations",
        headers=learner_headers,
        json={"instructor_id": instructor.id, "initial_message": "Hello Professor Kabir!"},
    )
    assert conv_res.status_code == 201, conv_res.text
    conv_id = conv_res.json()["data"]["id"]

    # 2. Instructor replies with a guidance message
    msg_payload = {"message_text": "Welcome to the Machine Learning guidance thread."}
    msg_res = client.post(f"/api/v1/chat/conversations/{conv_id}/messages", headers=inst_headers, json=msg_payload)
    assert msg_res.status_code == 201, msg_res.text
    msg_id = msg_res.json()["data"]["id"]
    assert msg_id is not None

    # 3. Learner fetches conversation message thread
    thread_res = client.get(f"/api/v1/chat/conversations/{conv_id}/messages", headers=learner_headers)
    assert thread_res.status_code == 200
    messages = thread_res.json()["data"]
    assert any(m["id"] == msg_id for m in messages)

    # 4. Learner marks conversation as read
    read_res = client.post(f"/api/v1/chat/conversations/{conv_id}/read", headers=learner_headers)
    assert read_res.status_code == 200
    assert read_res.json()["data"]["conversation_id"] == conv_id

    # Verify conversation unread_count is reset to 0
    conv_check_res = client.get(f"/api/v1/chat/conversations/{conv_id}", headers=learner_headers)
    assert conv_check_res.status_code == 200
    assert conv_check_res.json()["data"]["unread_count"] == 0

    # 5. Unauthorized stranger blocked from inspecting messages
    intruder_res = client.get(f"/api/v1/chat/conversations/{conv_id}/messages", headers=stranger_headers)
    assert intruder_res.status_code in (403, 404)


def test_event_driven_notification_lifecycle_integration(client: TestClient, db_session: Session):
    """AC-8: In-app notification creation, badge counters, and state transitions."""
    recipient = create_test_user(db_session, "notify.recipient@skill2career.com", UserRole.LEARNER, "Tanvir", "Ahmed")
    headers = auth_header(recipient)

    # 1. Simulate dispatch of system notification events
    n1 = Notification(
        recipient_id=recipient.id,
        event_type="APPLICATION_UPDATE",
        title="Application Shortlisted",
        message="Congratulations! Your application for Python Engineer was shortlisted.",
        is_read=False,
    )
    n2 = Notification(
        recipient_id=recipient.id,
        event_type="PAYMENT_CONFIRMATION",
        title="Payment Succeeded",
        message="Your Pro Monthly subscription is now active.",
        is_read=False,
    )
    db_session.add_all([n1, n2])
    db_session.commit()
    db_session.refresh(n1)
    db_session.refresh(n2)

    # 2. Query unread count badge
    unread_res = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert unread_res.status_code == 200
    assert unread_res.json()["data"]["unread_count"] == 2

    # 3. Query notification drawer items
    drawer_res = client.get("/api/v1/notifications", headers=headers)
    assert drawer_res.status_code == 200
    notifs = drawer_res.json()["data"]["items"]
    assert len(notifs) >= 2

    # 4. Mark single notification as read
    read_single_res = client.patch(f"/api/v1/notifications/{n1.id}/read", headers=headers)
    assert read_single_res.status_code == 200
    assert read_single_res.json()["data"]["is_read"] is True

    # 5. Bulk mark all notifications as read
    bulk_res = client.patch("/api/v1/notifications/mark-all-read", headers=headers)
    assert bulk_res.status_code == 200
    assert bulk_res.json()["data"]["unread_count"] == 0


def test_admin_and_role_dashboard_telemetry_integration(client: TestClient, db_session: Session):
    """AC-9: Cross-system metric aggregation verifying consolidated platform telemetry across Admin, Learner, and Company."""
    admin = create_test_user(db_session, "exec.admin@skill2career.com", UserRole.ADMIN, "Executive", "Admin")
    headers = auth_header(admin)

    # 1. Admin overview telemetry combines live entity counts
    overview_res = client.get("/api/v1/admin/analytics/overview", headers=headers)
    assert overview_res.status_code == 200
    overview_data = overview_res.json()["data"]
    assert "users" in overview_data
    assert "courses" in overview_data
    assert "recruitment" in overview_data
    assert overview_data["users"]["total"] >= 1

    # 2. Admin recruitment summary combines pipeline conversion funnels
    recruitment_res = client.get("/api/v1/admin/analytics/recruitment-summary", headers=headers)
    assert recruitment_res.status_code == 200
    rec_data = recruitment_res.json()["data"]
    assert "applications_by_status" in rec_data
    assert "total_jobs" in rec_data
    assert "total_applications" in rec_data
    assert "interviews_by_status" in rec_data
