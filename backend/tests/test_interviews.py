import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.job import JobPosting, JobStatus
from app.models.profile import CompanyProfile
from app.models.application import JobApplication, ApplicationStatus
from app.models.interview import InterviewRequest, InterviewSlot, InterviewStatus
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


def setup_recruitment_flow(db: Session):
    company_user = create_user(
        db, email="recruiter_interview@tech.com", role=UserRole.COMPANY, first_name="Brain", last_name="Station"
    )
    company_profile = CompanyProfile(
        user_id=company_user.id,
        company_name="Brain Station 23",
        verification_status="APPROVED",
    )
    db.add(company_profile)

    candidate_user = create_user(
        db, email="candidate_interview@learner.com", role=UserRole.LEARNER, first_name="Lam-Yea", last_name="Rahman"
    )

    job = JobPosting(
        company_id=company_user.id,
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
        learner_id=candidate_user.id,
        resume_filename="LamYea_CV.pdf",
        cover_letter="Passionate full stack developer.",
        status=ApplicationStatus.SHORTLISTED.value,
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    return company_user, candidate_user, job, application


def test_create_interview_request(client: TestClient, db_session: Session):
    company, candidate, job, application = setup_recruitment_flow(db_session)

    now = datetime.now(timezone.utc)
    slot1_start = now + timedelta(days=2, hours=10)
    slot1_end = slot1_start + timedelta(minutes=45)
    slot2_start = now + timedelta(days=3, hours=14)
    slot2_end = slot2_start + timedelta(minutes=45)

    payload = {
        "interview_type": "Technical Interview",
        "meeting_platform": "Google Meet",
        "meeting_link": "https://meet.google.com/abc-defg-hij",
        "duration_minutes": 45,
        "notes": "Please prepare for data structures and coding assessment.",
        "proposed_slots": [
            {"start_time": slot1_start.isoformat(), "end_time": slot1_end.isoformat()},
            {"start_time": slot2_start.isoformat(), "end_time": slot2_end.isoformat()},
        ],
    }

    # Recruiter creates interview request
    res = client.post(
        f"/api/v1/applications/{application.id}/interview-request",
        json=payload,
        headers=auth_header(company),
    )
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["interview_type"] == "Technical Interview"
    assert data["meeting_platform"] == "Google Meet"
    assert data["status"] == "PENDING"
    assert len(data["slots"]) == 2
    assert data["company_name"] == "Brain Station 23"
    assert data["candidate_name"] == "Lam-Yea Rahman"


def test_unauthorized_user_cannot_create_interview_request(client: TestClient, db_session: Session):
    company, candidate, job, application = setup_recruitment_flow(db_session)

    other_user = create_user(db_session, email="intruder@test.com", role=UserRole.LEARNER)

    payload = {
        "interview_type": "HR Round",
        "meeting_platform": "Zoom",
        "duration_minutes": 30,
        "proposed_slots": [],
    }

    res = client.post(
        f"/api/v1/applications/{application.id}/interview-request",
        json=payload,
        headers=auth_header(other_user),
    )
    assert res.status_code == 403


def test_candidate_views_and_selects_slot(client: TestClient, db_session: Session):
    company, candidate, job, application = setup_recruitment_flow(db_session)

    now = datetime.now(timezone.utc)
    slot1_start = now + timedelta(days=2, hours=9)
    slot1_end = slot1_start + timedelta(minutes=45)
    slot2_start = now + timedelta(days=3, hours=15)
    slot2_end = slot2_start + timedelta(minutes=45)

    create_res = client.post(
        f"/api/v1/applications/{application.id}/interview-request",
        json={
            "interview_type": "Company Interview",
            "meeting_platform": "Google Meet",
            "duration_minutes": 45,
            "proposed_slots": [
                {"start_time": slot1_start.isoformat(), "end_time": slot1_end.isoformat()},
                {"start_time": slot2_start.isoformat(), "end_time": slot2_end.isoformat()},
            ],
        },
        headers=auth_header(company),
    )
    interview_id = create_res.json()["data"]["id"]
    slots = create_res.json()["data"]["slots"]
    chosen_slot_id = slots[1]["id"]

    # Candidate lists my interviews
    list_res = client.get("/api/v1/interviews/me", headers=auth_header(candidate))
    assert list_res.status_code == 200
    assert list_res.json()["data"]["total"] >= 1

    # Candidate accepts slot 2
    select_res = client.post(
        f"/api/v1/interviews/{interview_id}/select-slot",
        json={"slot_id": chosen_slot_id},
        headers=auth_header(candidate),
    )
    assert select_res.status_code == 200
    sel_data = select_res.json()["data"]
    assert sel_data["status"] == "SCHEDULED"
    assert sel_data["selected_slot_id"] == chosen_slot_id
    assert sel_data["scheduled_at"] is not None

    # Verify linked job_application status moved to INTERVIEW_SCHEDULED
    db_session.refresh(application)
    assert application.status == ApplicationStatus.INTERVIEW_SCHEDULED.value


def test_candidate_reschedule_request(client: TestClient, db_session: Session):
    company, candidate, job, application = setup_recruitment_flow(db_session)

    create_res = client.post(
        f"/api/v1/applications/{application.id}/interview-request",
        json={
            "interview_type": "Technical Interview",
            "meeting_platform": "Google Meet",
            "duration_minutes": 45,
            "proposed_slots": [],
        },
        headers=auth_header(company),
    )
    interview_id = create_res.json()["data"]["id"]

    # Candidate requests rescheduling
    reschedule_res = client.post(
        f"/api/v1/interviews/{interview_id}/reschedule",
        json={
            "reason": "Final exam clash on the scheduled date.",
            "preferred_time": "Next Monday after 4:00 PM BST",
        },
        headers=auth_header(candidate),
    )
    assert reschedule_res.status_code == 200
    r_data = reschedule_res.json()["data"]
    assert r_data["status"] == "RESCHEDULE_REQUESTED"
    assert "Final exam clash" in r_data["reschedule_reason"]
    assert r_data["reschedule_preferred_time"] == "Next Monday after 4:00 PM BST"


def test_download_calendar_ics(client: TestClient, db_session: Session):
    company, candidate, job, application = setup_recruitment_flow(db_session)

    create_res = client.post(
        f"/api/v1/applications/{application.id}/interview-request",
        json={
            "interview_type": "Company Interview",
            "meeting_platform": "Google Meet",
            "meeting_link": "https://meet.google.com/test-cal-meet",
            "duration_minutes": 45,
            "proposed_slots": [],
        },
        headers=auth_header(company),
    )
    interview_id = create_res.json()["data"]["id"]
    slot_id = create_res.json()["data"]["slots"][0]["id"]

    # Select slot to confirm time
    client.post(
        f"/api/v1/interviews/{interview_id}/select-slot",
        json={"slot_id": slot_id},
        headers=auth_header(candidate),
    )

    # Download .ics
    ics_res = client.get(
        f"/api/v1/interviews/{interview_id}/ics",
        headers=auth_header(candidate),
    )
    assert ics_res.status_code == 200
    assert "text/calendar" in ics_res.headers["content-type"]
    content = ics_res.text
    assert "BEGIN:VCALENDAR" in content
    assert "BEGIN:VEVENT" in content
    assert "Junior Software Developer" in content
    assert "END:VCALENDAR" in content


def test_get_application_interview(client: TestClient, db_session: Session):
    company, candidate, job, application = setup_recruitment_flow(db_session)

    client.post(
        f"/api/v1/applications/{application.id}/interview-request",
        json={"interview_type": "Screening Round", "duration_minutes": 30, "proposed_slots": []},
        headers=auth_header(company),
    )

    res = client.get(
        f"/api/v1/applications/{application.id}/interview",
        headers=auth_header(candidate),
    )
    assert res.status_code == 200
    assert res.json()["data"]["interview_type"] == "Screening Round"


def test_cancel_and_decline_interview(client: TestClient, db_session: Session):
    company, candidate, job, application = setup_recruitment_flow(db_session)

    create_res = client.post(
        f"/api/v1/applications/{application.id}/interview-request",
        json={"interview_type": "Technical Interview", "duration_minutes": 45, "proposed_slots": []},
        headers=auth_header(company),
    )
    interview_id = create_res.json()["data"]["id"]

    cancel_res = client.patch(
        f"/api/v1/interviews/{interview_id}/status",
        json={"status": "CANCELLED", "notes": "Candidate unable to proceed at this time"},
        headers=auth_header(candidate),
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["data"]["status"] == "CANCELLED"
