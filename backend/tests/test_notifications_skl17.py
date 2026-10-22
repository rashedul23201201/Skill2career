import asyncio
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.profile import LearnerProfile, CompanyProfile
from app.models.notification import Notification
from app.models.job import JobPosting, JobStatus, JobPostingType, JobWorkMode, JobExperienceLevel
from app.models.application import JobApplication, ApplicationStatus
from app.core.security import hash_password, create_access_token
from app.services.email_service import email_service
from app.services.notification_service import notification_service
from app.core.exceptions import BadRequestException, NotFoundException, ForbiddenException


def create_test_user(
    db: Session,
    email: str,
    role: UserRole = UserRole.LEARNER,
    first_name: str = "Test",
    last_name: str = "User",
    is_active: bool = True,
) -> User:
    user = User(
        email=email,
        hashed_password=hash_password("Password123!"),
        role=role,
        first_name=first_name,
        last_name=last_name,
        is_active=is_active,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if role == UserRole.LEARNER:
        profile = LearnerProfile(
            user_id=user.id,
            target_role="Software Engineer",
            institution="BUET",
        )
        db.add(profile)
        db.commit()
    elif role == UserRole.COMPANY:
        profile = CompanyProfile(
            user_id=user.id,
            company_name="Tech Innovations Ltd",
            industry="IT",
        )
        db.add(profile)
        db.commit()
    return user


def get_auth_header(user: User) -> dict:
    token = create_access_token(
        subject=user.id,
        claims={"email": user.email, "role": user.role.value},
    )
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# AC-1: Given an important supported activity occurs, when processing is completed,
#       then a notification must be generated.
# ============================================================================

def test_ac1_notification_generation_service(db_session: Session):
    """AC-1: Direct service call creates notification and persists in MySQL."""
    email_service.clear_dispatched()
    learner = create_test_user(db_session, "learner_ac1@example.com", UserRole.LEARNER, "Rahim", "Khan")

    notif = asyncio.run(
        notification_service.create_notification(
            db=db_session,
            recipient_id=learner.id,
            event_type="APPLICATION_UPDATE",
            title="Application Status Changed",
            message="Your application has been shortlisted.",
            link_url="/learner/applications",
            send_email=True,
        )
    )

    assert notif.id is not None
    assert notif.recipient_id == learner.id
    assert notif.event_type == "APPLICATION_UPDATE"
    assert notif.title == "Application Status Changed"
    assert notif.is_read is False
    assert notif.email_sent is True


def create_sample_job(db: Session, company: User) -> JobPosting:
    job = JobPosting(
        company_id=company.id,
        title="Senior Python Backend Developer",
        posting_type="Job",
        work_mode="On-site",
        location="Dhaka, Bangladesh",
        description="Develop backend APIs with FastAPI and relational databases.",
        requirements="B.Sc. in CSE, solid understanding of OOP and SQL.",
        skills=["Python", "FastAPI", "SQL"],
        compensation="50,000 - 65,000 BDT/month",
        experience_level="Junior",
        category="Software Engineering",
        status=JobStatus.ACTIVE.value,
        applications_count=0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def test_ac1_event_driven_job_application_status_update(db_session: Session, client: TestClient):
    """AC-1: Updating application status automatically generates candidate notification & email."""
    email_service.clear_dispatched()
    company = create_test_user(db_session, "company_ac1@example.com", UserRole.COMPANY, "TechCorp", "Recruiter")
    candidate = create_test_user(db_session, "candidate_ac1@example.com", UserRole.LEARNER, "Anis", "Hasan")

    # Create job posting using standard helper
    job = create_sample_job(db_session, company)

    # Create application
    application = JobApplication(
        job_id=job.id,
        learner_id=candidate.id,
        resume_url="https://example.com/resume.pdf",
        resume_filename="resume.pdf",
        status=ApplicationStatus.SUBMITTED.value,
    )
    db_session.add(application)
    db_session.commit()
    db_session.refresh(application)

    # Employer updates candidate status to SHORTLISTED via API
    company_headers = get_auth_header(company)
    response = client.patch(
        f"/api/v1/applications/{application.id}/status",
        headers=company_headers,
        json={"status": "SHORTLISTED", "notes": "Strong background in FastAPI"},
    )
    assert response.status_code == 200, response.text

    # Candidate checks their notifications
    candidate_headers = get_auth_header(candidate)
    notif_res = client.get("/api/v1/notifications", headers=candidate_headers)
    assert notif_res.status_code == 200
    data = notif_res.json()["data"]

    assert data["total"] >= 1
    found = [n for n in data["items"] if n["event_type"] == "APPLICATION_UPDATE"]
    assert len(found) >= 1
    assert "Senior Python Backend Developer" in found[0]["title"]
    assert "Shortlisted" in found[0]["message"]
    assert found[0]["is_read"] is False


# ============================================================================
# AC-2: Given an unread notification exists, when the user opens notifications,
#       then it must be displayed.
# ============================================================================

def test_ac2_list_notifications_unread_display(db_session: Session, client: TestClient):
    """AC-2: Unread notifications are returned with total unread count."""
    user = create_test_user(db_session, "user_ac2@example.com", UserRole.LEARNER)
    headers = get_auth_header(user)

    # Insert 2 unread notifications and 1 read notification
    n1 = Notification(
        recipient_id=user.id,
        event_type="SYSTEM_ALERT",
        title="Welcome to Skill2Career",
        message="Complete your profile to unlock recommended jobs.",
        is_read=False,
    )
    n2 = Notification(
        recipient_id=user.id,
        event_type="COURSE_ENROLLMENT",
        title="Enrolled in FastAPI Masterclass",
        message="You have enrolled in course #1.",
        is_read=False,
    )
    n3 = Notification(
        recipient_id=user.id,
        event_type="SYSTEM_ALERT",
        title="Old archived announcement",
        message="Platform maintenance scheduled.",
        is_read=True,
    )
    db_session.add_all([n1, n2, n3])
    db_session.commit()

    # List all notifications
    response = client.get("/api/v1/notifications", headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]

    assert data["total"] == 3
    assert data["unread_count"] == 2
    assert len(data["items"]) == 3

    # Filter unread only
    response_unread = client.get("/api/v1/notifications?is_read=false", headers=headers)
    assert response_unread.status_code == 200
    data_unread = response_unread.json()["data"]
    assert data_unread["total"] == 2
    assert all(item["is_read"] is False for item in data_unread["items"])

    # Check unread count endpoint
    count_res = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert count_res.status_code == 200
    assert count_res.json()["data"]["unread_count"] == 2


# ============================================================================
# AC-3: Given a notification is opened, when it is marked as read,
#       then its status must be updated.
# ============================================================================

def test_ac3_mark_single_and_all_notifications_as_read(db_session: Session, client: TestClient):
    """AC-3: Marking specific or all notifications as read updates database status."""
    user = create_test_user(db_session, "user_ac3@example.com", UserRole.LEARNER)
    headers = get_auth_header(user)

    n1 = Notification(
        recipient_id=user.id,
        event_type="CHAT_MESSAGE",
        title="New Message",
        message="Hey Rahim, how is the assignment going?",
        is_read=False,
    )
    n2 = Notification(
        recipient_id=user.id,
        event_type="INTERVIEW_INVITE",
        title="Interview Proposal",
        message="Choose a slot for interview.",
        is_read=False,
    )
    db_session.add_all([n1, n2])
    db_session.commit()
    db_session.refresh(n1)
    db_session.refresh(n2)

    # 1. Mark n1 as read
    res1 = client.patch(f"/api/v1/notifications/{n1.id}/read", headers=headers)
    assert res1.status_code == 200
    res1_data = res1.json()["data"]
    assert res1_data["is_read"] is True
    assert res1_data["unread_count"] == 1

    # Verify in DB
    db_session.refresh(n1)
    assert n1.is_read is True

    # 2. Mark all as read
    res_all = client.patch("/api/v1/notifications/mark-all-read", headers=headers)
    assert res_all.status_code == 200
    res_all_data = res_all.json()["data"]
    assert res_all_data["unread_count"] == 0
    assert res_all_data["updated_count"] == 1

    # Verify n2 is now read in DB
    db_session.refresh(n2)
    assert n2.is_read is True


# ============================================================================
# AC-4: Given email notification is required, when the event occurs,
#       then the system must attempt email delivery.
# ============================================================================

def test_ac4_email_delivery_dispatched_for_high_priority_events(db_session: Session):
    """AC-4: System attempts email delivery for high priority events (interview invites, application updates)."""
    email_service.clear_dispatched()
    learner = create_test_user(db_session, "learner_email_test@example.com", UserRole.LEARNER, "Sumon", "Barua")

    # High priority event: INTERVIEW_INVITE
    notif = asyncio.run(
        notification_service.create_notification(
            db=db_session,
            recipient_id=learner.id,
            event_type="INTERVIEW_INVITE",
            title="Technical Interview Invitation",
            message="Your live coding interview is scheduled.",
            link_url="/learner/applications",
        )
    )

    assert notif.email_sent is True
    assert len(email_service.dispatched_emails) == 1
    dispatched = email_service.dispatched_emails[0]
    assert dispatched["to_email"] == "learner_email_test@example.com"
    assert dispatched["event_type"] == "INTERVIEW_INVITE"
    assert "Technical Interview Invitation" in dispatched["subject"]
    assert "Sumon Barua" in dispatched["plain_text"]
    assert dispatched["success"] is True


def test_ac4_invalid_email_syntax_handled_without_exception(db_session: Session):
    """AC-4 Error handling: Invalid email syntax is logged and handled gracefully."""
    email_service.clear_dispatched()
    success = email_service.send_notification_email(
        to_email="invalid-syntax-no-at-sign",
        recipient_name="Faulty User",
        subject="Alert",
        event_type="SYSTEM_ALERT",
        title="Test Alert",
        message="Test message",
    )
    assert success is False
    assert len(email_service.dispatched_emails) == 0


# ============================================================================
# AC-5: Given a user accesses notifications, when the request is processed,
#       then only their notifications must be shown.
# ============================================================================

def test_ac5_strict_tenant_isolation_and_unauthorized_access(db_session: Session, client: TestClient):
    """AC-5: User A only sees User A's notifications; User B cannot read or mark User A's notifications."""
    user_a = create_test_user(db_session, "user_a@example.com", UserRole.LEARNER, "User", "A")
    user_b = create_test_user(db_session, "user_b@example.com", UserRole.LEARNER, "User", "B")

    headers_a = get_auth_header(user_a)
    headers_b = get_auth_header(user_b)

    notif_a = Notification(
        recipient_id=user_a.id,
        event_type="PAYMENT_SUCCESS",
        title="User A's Private Receipt",
        message="Your Pro subscription invoice #1001.",
        is_read=False,
    )
    notif_b = Notification(
        recipient_id=user_b.id,
        event_type="PAYMENT_SUCCESS",
        title="User B's Private Receipt",
        message="Your Pro subscription invoice #1002.",
        is_read=False,
    )
    db_session.add_all([notif_a, notif_b])
    db_session.commit()
    db_session.refresh(notif_a)
    db_session.refresh(notif_b)

    # 1. User A lists notifications -> Only user A's notifications appear
    res_a = client.get("/api/v1/notifications", headers=headers_a)
    assert res_a.status_code == 200
    items_a = res_a.json()["data"]["items"]
    assert len(items_a) == 1
    assert items_a[0]["id"] == notif_a.id
    assert items_a[0]["title"] == "User A's Private Receipt"

    # 2. User B lists notifications -> Only user B's notifications appear
    res_b = client.get("/api/v1/notifications", headers=headers_b)
    assert res_b.status_code == 200
    items_b = res_b.json()["data"]["items"]
    assert len(items_b) == 1
    assert items_b[0]["id"] == notif_b.id
    assert items_b[0]["title"] == "User B's Private Receipt"

    # 3. User B attempts to mark User A's notification as read -> Must be blocked with 403 Forbidden
    hack_attempt = client.patch(f"/api/v1/notifications/{notif_a.id}/read", headers=headers_b)
    assert hack_attempt.status_code == 403
    assert "not authorized" in hack_attempt.json()["message"].lower()

    # Verify notif_a is STILL unread
    db_session.refresh(notif_a)
    assert notif_a.is_read is False


# ============================================================================
# Error Cases & Edge Cases
# ============================================================================

def test_error_case_recipient_not_found(db_session: Session):
    """Error Case: Non-existent recipient user ID raises NotFoundException."""
    with pytest.raises(NotFoundException):
        asyncio.run(
            notification_service.create_notification(
                db=db_session,
                recipient_id=999999,
                event_type="SYSTEM_ALERT",
                title="Alert",
                message="Test",
            )
        )


def test_error_case_deactivated_account(db_session: Session):
    """Error Case: Deactivated recipient account raises BadRequestException."""
    inactive_user = create_test_user(
        db_session, "inactive@example.com", UserRole.LEARNER, is_active=False
    )
    with pytest.raises(BadRequestException) as exc_info:
        asyncio.run(
            notification_service.create_notification(
                db=db_session,
                recipient_id=inactive_user.id,
                event_type="SYSTEM_ALERT",
                title="Alert",
                message="Test",
            )
        )
    assert "deactivated" in str(exc_info.value.message).lower()


def test_error_case_missing_mandatory_parameters(db_session: Session):
    """Error Case: Missing title, message, or event_type raises BadRequestException."""
    user = create_test_user(db_session, "mandatory_test@example.com", UserRole.LEARNER)

    with pytest.raises(BadRequestException):
        asyncio.run(
            notification_service.create_notification(
                db=db_session,
                recipient_id=user.id,
                event_type="",
                title="Title",
                message="Message",
            )
        )

    with pytest.raises(BadRequestException):
        asyncio.run(
            notification_service.create_notification(
                db=db_session,
                recipient_id=user.id,
                event_type="ALERT",
                title="   ",
                message="Message",
            )
        )

    with pytest.raises(BadRequestException):
        asyncio.run(
            notification_service.create_notification(
                db=db_session,
                recipient_id=user.id,
                event_type="ALERT",
                title="Title",
                message="   ",
            )
        )


def test_error_case_non_existent_notification_id_404(db_session: Session, client: TestClient):
    """Error Case: Marking non-existent notification ID returns 404."""
    user = create_test_user(db_session, "user_404@example.com", UserRole.LEARNER)
    headers = get_auth_header(user)

    res = client.patch("/api/v1/notifications/999999/read", headers=headers)
    assert res.status_code == 404


def test_unauthenticated_request_rejected(client: TestClient):
    """Error Case: Unauthenticated request to /api/v1/notifications returns 401."""
    res = client.get("/api/v1/notifications")
    assert res.status_code == 401
