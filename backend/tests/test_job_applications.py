import io
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.job import JobPosting, JobStatus
from app.models.profile import LearnerProfile, CompanyProfile
from app.models.screening import ScreeningQuestion, QuestionType, DealBreakerRule
from app.models.application import JobApplication, ApplicationStatus
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


def create_sample_job(db: Session, company: User, status: str = JobStatus.ACTIVE.value) -> JobPosting:
    job = JobPosting(
        company_id=company.id,
        title="Junior Software Engineer",
        posting_type="Job",
        work_mode="On-site",
        location="Dhaka, Bangladesh",
        description="Develop backend APIs with FastAPI and relational databases.",
        requirements="B.Sc. in CSE, solid understanding of OOP and SQL.",
        skills=["Python", "FastAPI", "SQL"],
        compensation="50,000 - 65,000 BDT/month",
        experience_level="Junior",
        category="Software Engineering",
        status=status,
        applications_count=0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def test_apply_job_positive_profile_resume(client: TestClient, db_session: Session):
    company = create_user(db_session, "comp1@test.com", UserRole.COMPANY, "Brain", "Station")
    job = create_sample_job(db_session, company)

    learner = create_user(db_session, "learner1@test.com", UserRole.LEARNER, "Tanvir", "Hasan")
    profile = LearnerProfile(
        user_id=learner.id,
        resume_url="/uploads/resumes/Tanvir_Hasan_Resume.pdf",
        resume_filename="Tanvir_Hasan_Resume.pdf",
        completion_pct=85,
    )
    db_session.add(profile)
    db_session.commit()

    q1 = ScreeningQuestion(
        job_id=job.id,
        question_text="Do you have experience with Python?",
        question_type=QuestionType.YES_NO.value,
        expected_answer="Yes",
        weight=20,
    )
    db_session.add(q1)
    db_session.commit()

    payload = {
        "use_profile_resume": True,
        "cover_letter": "I have 1 year of hands-on experience building web services in Python.",
        "screening_answers": {str(q1.id): "Yes"},
    }

    response = client.post(
        f"/api/v1/jobs/{job.id}/apply",
        json=payload,
        headers=auth_header(learner),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["job_id"] == job.id
    assert data["data"]["learner_id"] == learner.id
    assert data["data"]["status"] == "SUBMITTED"
    assert data["data"]["resume_filename"] == "Tanvir_Hasan_Resume.pdf"
    assert data["data"]["screening_score"] == 100

    db_session.refresh(job)
    assert job.applications_count == 1


def test_apply_job_with_file_upload(client: TestClient, db_session: Session):
    company = create_user(db_session, "comp2@test.com", UserRole.COMPANY)
    job = create_sample_job(db_session, company)
    learner = create_user(db_session, "learner2@test.com", UserRole.LEARNER)

    dummy_pdf = b"%PDF-1.4 header content for testing resume uploads..."

    response = client.post(
        f"/api/v1/jobs/{job.id}/apply",
        data={"cover_letter": "Uploaded custom resume document."},
        files={"resume_file": ("my_resume.pdf", io.BytesIO(dummy_pdf), "application/pdf")},
        headers=auth_header(learner),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["resume_filename"] == "my_resume.pdf"
    assert "my_resume.pdf" in data["data"]["resume_url"] or "job_" in data["data"]["resume_url"]


def test_apply_job_duplicate_blocked(client: TestClient, db_session: Session):
    company = create_user(db_session, "comp3@test.com", UserRole.COMPANY)
    job = create_sample_job(db_session, company)
    learner = create_user(db_session, "learner3@test.com", UserRole.LEARNER)

    app = JobApplication(
        job_id=job.id,
        learner_id=learner.id,
        resume_url="/uploads/resumes/test.pdf",
        resume_filename="test.pdf",
        status=ApplicationStatus.SUBMITTED.value,
    )
    db_session.add(app)
    db_session.commit()

    response = client.post(
        f"/api/v1/jobs/{job.id}/apply",
        json={"resume_url": "/uploads/resumes/test.pdf", "resume_filename": "test.pdf"},
        headers=auth_header(learner),
    )

    assert response.status_code == 400
    err = response.json()
    assert "DUPLICATE_APPLICATION" in err.get("error_code", "") or "already active" in err.get("message", "")


def test_apply_job_inactive_fails(client: TestClient, db_session: Session):
    company = create_user(db_session, "comp4@test.com", UserRole.COMPANY)
    job = create_sample_job(db_session, company, status=JobStatus.CLOSED.value)
    learner = create_user(db_session, "learner4@test.com", UserRole.LEARNER)

    response = client.post(
        f"/api/v1/jobs/{job.id}/apply",
        json={"resume_url": "/test.pdf", "resume_filename": "test.pdf"},
        headers=auth_header(learner),
    )

    assert response.status_code == 400


def test_apply_job_non_learner_fails(client: TestClient, db_session: Session):
    company = create_user(db_session, "comp5@test.com", UserRole.COMPANY)
    job = create_sample_job(db_session, company)
    instructor = create_user(db_session, "inst5@test.com", UserRole.INSTRUCTOR)

    response = client.post(
        f"/api/v1/jobs/{job.id}/apply",
        json={"resume_url": "/test.pdf", "resume_filename": "test.pdf"},
        headers=auth_header(instructor),
    )

    assert response.status_code == 403


def test_get_learner_applications_tracking(client: TestClient, db_session: Session):
    company = create_user(db_session, "comp6@test.com", UserRole.COMPANY, "Brain", "Station")
    c_profile = CompanyProfile(user_id=company.id, company_name="Brain Station 23")
    db_session.add(c_profile)
    job = create_sample_job(db_session, company)

    learner = create_user(db_session, "learner6@test.com", UserRole.LEARNER)

    app1 = JobApplication(
        job_id=job.id,
        learner_id=learner.id,
        resume_url="/uploads/resumes/cv.pdf",
        resume_filename="cv.pdf",
        status=ApplicationStatus.SHORTLISTED.value,
        screening_score=85,
    )
    db_session.add(app1)
    db_session.commit()

    response = client.get(
        "/api/v1/learners/applications",
        headers=auth_header(learner),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total"] == 1
    assert data["data"]["shortlisted_count"] == 1
    item = data["data"]["items"][0]
    assert item["status"] == "SHORTLISTED"
    assert item["job_title"] == "Junior Software Engineer"
    assert item["company_name"] == "Brain Station 23"


def test_check_job_application_status(client: TestClient, db_session: Session):
    company = create_user(db_session, "comp7@test.com", UserRole.COMPANY)
    job = create_sample_job(db_session, company)
    learner = create_user(db_session, "learner7@test.com", UserRole.LEARNER)

    res_initial = client.get(
        f"/api/v1/applications/check/{job.id}",
        headers=auth_header(learner),
    )
    assert res_initial.status_code == 200
    assert res_initial.json()["data"]["has_applied"] is False

    app = JobApplication(
        job_id=job.id,
        learner_id=learner.id,
        resume_url="/test.pdf",
        resume_filename="test.pdf",
        status=ApplicationStatus.SUBMITTED.value,
    )
    db_session.add(app)
    db_session.commit()

    res_after = client.get(
        f"/api/v1/applications/check/{job.id}",
        headers=auth_header(learner),
    )
    assert res_after.status_code == 200
    assert res_after.json()["data"]["has_applied"] is True
    assert res_after.json()["data"]["application"]["status"] == "SUBMITTED"


def test_recruiter_update_application_status(client: TestClient, db_session: Session):
    company = create_user(db_session, "comp8@test.com", UserRole.COMPANY)
    job = create_sample_job(db_session, company)
    learner = create_user(db_session, "learner8@test.com", UserRole.LEARNER)

    app = JobApplication(
        job_id=job.id,
        learner_id=learner.id,
        resume_url="/test.pdf",
        status=ApplicationStatus.SUBMITTED.value,
    )
    db_session.add(app)
    db_session.commit()

    response = client.patch(
        f"/api/v1/applications/{app.id}/status",
        json={"status": "SHORTLISTED", "notes": "Strong background in Python and DSA."},
        headers=auth_header(company),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "SHORTLISTED"
    assert data["data"]["review_notes"] == "Strong background in Python and DSA."


def test_unauthorized_company_cannot_update_status(client: TestClient, db_session: Session):
    company1 = create_user(db_session, "comp9_1@test.com", UserRole.COMPANY)
    company2 = create_user(db_session, "comp9_2@test.com", UserRole.COMPANY)
    job = create_sample_job(db_session, company1)
    learner = create_user(db_session, "learner9@test.com", UserRole.LEARNER)

    app = JobApplication(
        job_id=job.id,
        learner_id=learner.id,
        resume_url="/test.pdf",
        status=ApplicationStatus.SUBMITTED.value,
    )
    db_session.add(app)
    db_session.commit()

    response = client.patch(
        f"/api/v1/applications/{app.id}/status",
        json={"status": "SHORTLISTED"},
        headers=auth_header(company2),
    )

    assert response.status_code == 403


def test_candidate_withdraw_application(client: TestClient, db_session: Session):
    company = create_user(db_session, "comp10@test.com", UserRole.COMPANY)
    job = create_sample_job(db_session, company)
    job.applications_count = 1
    learner = create_user(db_session, "learner10@test.com", UserRole.LEARNER)

    app = JobApplication(
        job_id=job.id,
        learner_id=learner.id,
        resume_url="/test.pdf",
        status=ApplicationStatus.SUBMITTED.value,
    )
    db_session.add(app)
    db_session.commit()

    response = client.delete(
        f"/api/v1/applications/{app.id}/withdraw",
        headers=auth_header(learner),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "WITHDRAWN"

    db_session.refresh(job)
    assert job.applications_count == 0


def test_deal_breaker_evaluation_in_application(client: TestClient, db_session: Session):
    company = create_user(db_session, "comp11@test.com", UserRole.COMPANY)
    job = create_sample_job(db_session, company)
    learner = create_user(db_session, "learner11@test.com", UserRole.LEARNER)

    q_deal = ScreeningQuestion(
        job_id=job.id,
        question_text="Years of professional experience with React?",
        question_type=QuestionType.NUMERIC.value,
        is_deal_breaker=True,
        deal_breaker_rule=DealBreakerRule.GTE.value,
        deal_breaker_value="2",
        weight=50,
    )
    db_session.add(q_deal)
    db_session.commit()

    payload = {
        "resume_url": "/test.pdf",
        "resume_filename": "test.pdf",
        "screening_answers": {str(q_deal.id): "1"},
    }

    response = client.post(
        f"/api/v1/jobs/{job.id}/apply",
        json=payload,
        headers=auth_header(learner),
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["deal_breaker_passed"] is False
    assert "Minimum: 2" in data["deal_breaker_failed_reason"]
    assert data["screening_score"] <= 45
