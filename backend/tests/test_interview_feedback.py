import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.job import JobPosting, JobStatus
from app.models.profile import CompanyProfile
from app.models.application import JobApplication, ApplicationStatus
from app.models.interview import InterviewRequest, InterviewSlot, InterviewStatus, InterviewRecommendation
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


def setup_interview_flow(db: Session):
    company = create_user(
        db, email="recruiter_feedback@brainstation.com", role=UserRole.COMPANY, first_name="Brain", last_name="Station"
    )
    company_profile = CompanyProfile(
        user_id=company.id,
        company_name="Brain Station 23",
        verification_status="APPROVED",
    )
    db.add(company_profile)

    candidate = create_user(
        db, email="candidate_feedback@learner.com", role=UserRole.LEARNER, first_name="Tanvir", last_name="Hasan"
    )

    admin = create_user(
        db, email="admin_compliance@skill2career.com", role=UserRole.ADMIN, first_name="Super", last_name="Admin"
    )

    job = JobPosting(
        company_id=company.id,
        title="Junior Software Developer",
        posting_type="Job",
        work_mode="On-site",
        location="Dhaka, Bangladesh",
        description="Full stack web engineering role.",
        requirements="B.Sc. in CSE, solid DSA knowledge.",
        skills=["React", "FastAPI", "SQL"],
        compensation="55,000 BDT/month",
        experience_level="Junior",
        category="Software Engineering",
        status=JobStatus.ACTIVE.value,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    application = JobApplication(
        job_id=job.id,
        learner_id=candidate.id,
        resume_filename="Tanvir_Hasan_Resume.pdf",
        status=ApplicationStatus.INTERVIEW_SCHEDULED.value,
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    interview = InterviewRequest(
        application_id=application.id,
        company_id=company.id,
        candidate_id=candidate.id,
        job_id=job.id,
        interview_type="Technical Interview",
        meeting_platform="Google Meet",
        meeting_link="https://meet.google.com/abc-defg-hij",
        duration_minutes=45,
        status=InterviewStatus.SCHEDULED.value,
        scheduled_at=datetime.now(timezone.utc),
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)

    return company, candidate, admin, job, application, interview


def test_submit_structured_scorecard(client: TestClient, db_session: Session):
    company, candidate, admin, job, application, interview = setup_interview_flow(db_session)

    payload = {
        "overall_score": 82,
        "technical_score": 85,
        "communication_score": 80,
        "problem_solving_score": 88,
        "recommendation": "STRONG_HIRE",
        "strengths": ["Problem Solving", "Communication", "Data Structures"],
        "improvement_areas": [
            {"area": "System Design", "details": "Microservices, Caching layers"}
        ],
        "competency_breakdown": [
            {"label": "Data Structures & Algorithms", "score": "88%", "level": "Advanced"},
            {"label": "REST APIs & Backend Architecture", "score": "84%", "level": "Proficient"},
            {"label": "Database Design & SQL Indexing", "score": "76%", "level": "Intermediate"},
            {"label": "Technical Communication & Reasoning", "score": "85%", "level": "Advanced"},
        ],
        "feedback_notes": "Strong analytical intuition with clean algorithmic complexity. Continue practicing distributed system design.",
        "internal_notes": "Very strong candidate. Fits culture well. Target offer 60k.",
        "suggested_next_action": "OFFER",
        "is_shared_with_candidate": False,
    }

    res = client.post(
        f"/api/v1/interviews/{interview.id}/feedback",
        json=payload,
        headers=auth_header(company),
    )
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["overall_score"] == 82
    assert data["recommendation"] == "STRONG_HIRE"
    assert data["suggested_next_action"] == "OFFER"
    assert "Problem Solving" in data["strengths"]
    assert data["is_shared_with_candidate"] is False

    db_session.refresh(interview)
    assert interview.status == InterviewStatus.COMPLETED.value


def test_consolidated_team_feedback_view(client: TestClient, db_session: Session):
    company, candidate, admin, job, application, interview = setup_interview_flow(db_session)

    second_interviewer = create_user(
        db_session,
        email="interviewer2@brainstation.com",
        role=UserRole.COMPANY,
        first_name="Lead",
        last_name="Architect",
    )

    client.post(
        f"/api/v1/interviews/{interview.id}/feedback",
        json={
            "overall_score": 80,
            "technical_score": 82,
            "communication_score": 78,
            "problem_solving_score": 80,
            "recommendation": "HIRE",
            "strengths": ["Data Structures", "Architecture"],
            "improvement_areas": [{"area": "System Design"}],
            "is_shared_with_candidate": False,
        },
        headers=auth_header(company),
    )

    client.post(
        f"/api/v1/interviews/{interview.id}/feedback",
        json={
            "overall_score": 90,
            "technical_score": 92,
            "communication_score": 88,
            "problem_solving_score": 90,
            "recommendation": "STRONG_HIRE",
            "strengths": ["Communication", "Problem Solving"],
            "improvement_areas": [{"area": "DevOps"}],
            "is_shared_with_candidate": False,
        },
        headers=auth_header(second_interviewer),
    )

    res = client.get(
        f"/api/v1/interviews/{interview.id}/feedback",
        headers=auth_header(company),
    )
    assert res.status_code == 200
    team_data = res.json()["data"]
    assert team_data["total_feedbacks"] == 2
    assert team_data["average_overall_score"] == 85.0
    assert team_data["average_technical_score"] == 87.0
    assert team_data["recommendations_breakdown"]["HIRE"] == 1
    assert team_data["recommendations_breakdown"]["STRONG_HIRE"] == 1
    assert "Data Structures" in team_data["top_strengths"]
    assert "Communication" in team_data["top_strengths"]


def test_candidate_feedback_sharing_and_permission_guardrails(
    client: TestClient, db_session: Session
):
    company, candidate, admin, job, application, interview = setup_interview_flow(db_session)

    client.post(
        f"/api/v1/interviews/{interview.id}/feedback",
        json={
            "overall_score": 82,
            "technical_score": 85,
            "communication_score": 80,
            "problem_solving_score": 88,
            "recommendation": "HIRE",
            "strengths": ["Problem Solving"],
            "feedback_notes": "Keep practicing system design.",
            "internal_notes": "CONFIDENTIAL: Proposed salary range 55k-60k",
            "is_shared_with_candidate": False,
        },
        headers=auth_header(company),
    )

    learner_res_before = client.get(
        f"/api/v1/interviews/{interview.id}/feedback",
        headers=auth_header(candidate),
    )
    assert learner_res_before.status_code == 200
    assert learner_res_before.json()["data"]["total_feedbacks"] == 0

    share_res = client.post(
        f"/api/v1/interviews/{interview.id}/feedback/share",
        json={"is_shared_with_candidate": True},
        headers=auth_header(company),
    )
    assert share_res.status_code == 200
    assert share_res.json()["data"]["is_shared_with_candidate"] is True

    learner_res_after = client.get(
        f"/api/v1/interviews/{interview.id}/feedback",
        headers=auth_header(candidate),
    )
    assert learner_res_after.status_code == 200
    candidate_view = learner_res_after.json()["data"]
    assert candidate_view["total_feedbacks"] == 1
    assert candidate_view["average_overall_score"] == 82.0
    feedback_item = candidate_view["feedbacks"][0]
    assert feedback_item["feedback_notes"] == "Keep practicing system design."
    assert feedback_item["internal_notes"] is None

    app_feedback_res = client.get(
        f"/api/v1/applications/{application.id}/interview-feedback",
        headers=auth_header(candidate),
    )
    assert app_feedback_res.status_code == 200
    assert app_feedback_res.json()["data"]["total_feedbacks"] == 1


def test_audit_logging_and_admin_compliance(client: TestClient, db_session: Session):
    company, candidate, admin, job, application, interview = setup_interview_flow(db_session)

    client.post(
        f"/api/v1/interviews/{interview.id}/feedback",
        json={
            "overall_score": 75,
            "technical_score": 75,
            "communication_score": 75,
            "problem_solving_score": 75,
            "recommendation": "NEUTRAL",
            "feedback_notes": "Average performance.",
            "is_shared_with_candidate": False,
        },
        headers=auth_header(company),
    )

    forbidden_res = client.get(
        f"/api/v1/interviews/feedback/audit-logs?interview_id={interview.id}",
        headers=auth_header(company),
    )
    assert forbidden_res.status_code == 403

    admin_res = client.get(
        f"/api/v1/interviews/feedback/audit-logs?interview_id={interview.id}",
        headers=auth_header(admin),
    )
    assert admin_res.status_code == 200
    audit_data = admin_res.json()["data"]
    assert audit_data["total"] >= 1
    assert any("INTERVIEW_FEEDBACK" in item["action"] for item in audit_data["items"])
