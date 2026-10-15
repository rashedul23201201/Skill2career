"""Automated Pytest suite for Company Recruitment Dashboard (SKL-11)."""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password, create_access_token
from app.models.user import User, UserRole
from app.models.profile import CompanyProfile, LearnerProfile
from app.models.job import JobPosting, JobStatus
from app.models.application import JobApplication, ApplicationStatus
from app.models.interview import InterviewRequest, InterviewStatus


def create_user(
    db: Session,
    email: str,
    role: UserRole = UserRole.COMPANY,
    first_name: str = "Brain Station 23",
    last_name: str = "",
    is_verified: bool = True,
) -> User:
    """Helper to seed users."""
    user = User(
        email=email,
        hashed_password=hash_password("RecruiterPass123!"),
        role=role,
        first_name=first_name,
        last_name=last_name,
        is_active=True,
        is_verified=is_verified,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth_header(user: User) -> dict:
    """Generate bearer token header."""
    token = create_access_token(
        subject=user.id,
        claims={"email": user.email, "role": user.role.value},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def company_with_data(db_session: Session):
    """Seed a company with jobs, applications in various stages, and interviews."""
    company = create_user(db_session, "recruiter@bs23.com", UserRole.COMPANY, "Brain Station", "23", is_verified=True)
    profile = CompanyProfile(
        user_id=company.id,
        company_name="Brain Station 23",
        industry="Software & IT Services",
        company_size="500+",
        contact_person="Muktadir Rahman",
        contact_phone="+8801700000000",
        website_url="https://brainstation-23.com",
        office_address="Mirpur 14, Dhaka, Bangladesh",
        tagline="Global Digital Solutions Partner",
        verification_status="APPROVED",
        trade_license_url="https://storage.skill2career.com/licenses/bs23.pdf",
    )
    db_session.add(profile)

    # Job 1: Active
    job1 = JobPosting(
        company_id=company.id,
        title="Junior Software Developer",
        posting_type="Job",
        work_mode="On-site",
        location="Dhaka",
        description="Build full stack features.",
        requirements="Python, React",
        compensation="55,000 BDT/month",
        experience_level="Junior",
        category="Software Engineering",
        status=JobStatus.ACTIVE.value,
        applications_count=3,
    )
    # Job 2: Closed
    job2 = JobPosting(
        company_id=company.id,
        title="Software Engineering Intern",
        posting_type="Internship",
        work_mode="Hybrid",
        location="Dhaka",
        description="Internship for CS students.",
        requirements="JavaScript, Python",
        compensation="20,000 BDT/month",
        experience_level="Internship",
        category="Software Engineering",
        status=JobStatus.CLOSED.value,
        applications_count=1,
    )
    db_session.add_all([job1, job2])
    db_session.commit()
    db_session.refresh(job1)
    db_session.refresh(job2)

    # Candidates
    c1 = create_user(db_session, "c1@test.com", UserRole.LEARNER, "Rashedul", "Islam")
    c2 = create_user(db_session, "c2@test.com", UserRole.LEARNER, "Lam-yea", "Chowdhury")
    c3 = create_user(db_session, "c3@test.com", UserRole.LEARNER, "Saif", "Ahmed")
    c4 = create_user(db_session, "c4@test.com", UserRole.LEARNER, "Asif", "Karim")

    # Applications for Job 1
    app1 = JobApplication(
        job_id=job1.id,
        learner_id=c1.id,
        status=ApplicationStatus.SHORTLISTED.value,
        applied_at=datetime.now(timezone.utc) - timedelta(days=2),
    )
    app2 = JobApplication(
        job_id=job1.id,
        learner_id=c2.id,
        status=ApplicationStatus.SUBMITTED.value,
        applied_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    app3 = JobApplication(
        job_id=job1.id,
        learner_id=c3.id,
        status=ApplicationStatus.OFFERED.value,
        applied_at=datetime.now(timezone.utc) - timedelta(days=5),
    )
    # Application for Job 2
    app4 = JobApplication(
        job_id=job2.id,
        learner_id=c4.id,
        status=ApplicationStatus.INTERVIEW_SCHEDULED.value,
        applied_at=datetime.now(timezone.utc) - timedelta(days=3),
    )
    db_session.add_all([app1, app2, app3, app4])
    db_session.commit()
    db_session.refresh(app1)

    # Interview for c1
    interview1 = InterviewRequest(
        application_id=app1.id,
        company_id=company.id,
        candidate_id=c1.id,
        job_id=job1.id,
        interview_type="Technical Interview",
        meeting_platform="Google Meet",
        meeting_link="https://meet.google.com/xyz-abc-def",
        status=InterviewStatus.SCHEDULED.value,
        scheduled_at=datetime.now(timezone.utc) + timedelta(days=1),
        duration_minutes=45,
    )
    db_session.add(interview1)
    db_session.commit()

    return {
        "company": company,
        "job1": job1,
        "job2": job2,
        "c1": c1,
        "c2": c2,
        "interview1": interview1,
    }


def test_get_company_dashboard_metrics(client: TestClient, company_with_data):
    """SKL-11 AC-1: Verify central recruitment KPI metrics and stage breakdown."""
    company = company_with_data["company"]
    headers = auth_header(company)

    response = client.get("/api/v1/companies/dashboard/metrics", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    metrics = data["data"]

    # 1 active job (job1), 1 closed job (job2)
    assert metrics["active_jobs"] == 1
    # 4 total applications across all postings
    assert metrics["total_applications"] == 4
    # 1 shortlisted application (c1)
    assert metrics["shortlisted"] == 1
    # 1 pending review (c2)
    assert metrics["pending_reviews"] == 1
    # 1 scheduled interview
    assert metrics["scheduled_interviews"] == 1

    # Stage breakdown
    breakdown = metrics["stage_breakdown"]
    assert breakdown["applied"] == 1
    assert breakdown["shortlisted"] == 1
    assert breakdown["offered"] == 1
    assert breakdown["interview_scheduled"] == 1

    # Growth indicators
    growth = metrics["growth_indicators"]
    assert "active_jobs_growth" in growth
    assert "applications_growth" in growth


def test_get_company_dashboard_vacancies_with_stages(client: TestClient, company_with_data):
    """SKL-11 AC-2: Verify active postings table showing candidate volume per hiring stage."""
    company = company_with_data["company"]
    headers = auth_header(company)

    # 1. Default filter: ACTIVE jobs
    response = client.get("/api/v1/companies/dashboard/vacancies", headers=headers)
    assert response.status_code == 200

    data = response.json()["data"]
    assert data["total"] == 1
    assert data["active_count"] == 1
    assert len(data["items"]) == 1

    item = data["items"][0]
    assert item["title"] == "Junior Software Developer"
    assert item["status"] == "ACTIVE"
    assert item["applications_count"] == 3
    # Stage breakdown for this job: 1 applied, 1 shortlisted, 1 offered
    assert item["stages"]["applied"] == 1
    assert item["stages"]["shortlisted"] == 1
    assert item["stages"]["offered"] == 1

    # 2. Filter: ALL jobs
    all_res = client.get("/api/v1/companies/dashboard/vacancies?status=ALL", headers=headers)
    assert all_res.status_code == 200
    all_data = all_res.json()["data"]
    assert all_data["total"] == 2
    assert all_data["active_count"] == 1


def test_get_company_dashboard_recent_activity(client: TestClient, company_with_data):
    """SKL-11 AC-3: Verify chronological event stream aggregating applicants and interviews."""
    company = company_with_data["company"]
    headers = auth_header(company)

    response = client.get("/api/v1/companies/dashboard/recent-activity?limit=10", headers=headers)
    assert response.status_code == 200

    data = response.json()["data"]
    assert data["total"] > 0
    items = data["items"]

    # Candidate details and event types must be populated
    event_types = [item["type"] for item in items]
    assert any("APPLICATION" in t for t in event_types)
    assert any("INTERVIEW" in t for t in event_types)

    for item in items:
        assert item["candidate_name"]
        assert item["candidate_initials"]
        assert item["job_title"]
        assert item["description"]
        assert item["timestamp"]


def test_get_company_dashboard_profile_status_verified(client: TestClient, company_with_data):
    """SKL-11 AC-4: Verify profile status for approved company (no alert banner required)."""
    company = company_with_data["company"]
    headers = auth_header(company)

    response = client.get("/api/v1/companies/dashboard/profile-status", headers=headers)
    assert response.status_code == 200

    status_data = response.json()["data"]
    assert status_data["company_name"] == "Brain Station 23"
    assert status_data["verification_status"] == "APPROVED"
    assert status_data["is_verified"] is True
    assert status_data["requires_verification"] is False
    assert status_data["has_submitted_dossier"] is True
    assert status_data["active_jobs_count"] == 1


def test_get_company_dashboard_profile_status_unverified(client: TestClient, db_session: Session):
    """SKL-11 AC-4: Verify unverified company requires_verification flag is True for alert banner."""
    unverified_comp = create_user(
        db_session, "unverified@startup.com", UserRole.COMPANY, "Startup", "Hub", is_verified=False
    )
    profile = CompanyProfile(
        user_id=unverified_comp.id,
        company_name="Startup Hub",
        verification_status="PENDING",
    )
    db_session.add(profile)
    db_session.commit()

    headers = auth_header(unverified_comp)
    response = client.get("/api/v1/companies/dashboard/profile-status", headers=headers)
    assert response.status_code == 200

    status_data = response.json()["data"]
    assert status_data["is_verified"] is False
    assert status_data["requires_verification"] is True
    assert status_data["verification_status"] == "PENDING"


def test_get_company_dashboard_upcoming_interviews(client: TestClient, company_with_data):
    """Verify upcoming interview sessions endpoint."""
    company = company_with_data["company"]
    headers = auth_header(company)

    response = client.get("/api/v1/companies/dashboard/upcoming-interviews", headers=headers)
    assert response.status_code == 200

    interviews = response.json()["data"]
    assert len(interviews) == 1
    assert interviews[0]["candidate_name"] == "Rashedul Islam"
    assert interviews[0]["meeting_platform"] == "Google Meet"
    assert "meet.google.com" in interviews[0]["meeting_link"]


def test_company_dashboard_rbac_enforcement(client: TestClient, db_session: Session):
    """Verify strict RBAC: Learner & Instructor receive HTTP 403 Forbidden, Anonymous receives 401."""
    learner = create_user(db_session, "learner_rbac@test.com", UserRole.LEARNER)
    instructor = create_user(db_session, "instructor_rbac@test.com", UserRole.INSTRUCTOR)

    # Anonymous -> 401
    anon_res = client.get("/api/v1/companies/dashboard/metrics")
    assert anon_res.status_code == 401

    # Learner -> 403
    learner_res = client.get("/api/v1/companies/dashboard/metrics", headers=auth_header(learner))
    assert learner_res.status_code == 403

    # Instructor -> 403
    instructor_res = client.get("/api/v1/companies/dashboard/vacancies", headers=auth_header(instructor))
    assert instructor_res.status_code == 403
