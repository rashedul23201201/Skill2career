import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.models.profile import CompanyProfile
from app.models.job import JobPosting, JobStatus
from app.models.screening import ScreeningQuestion, CandidateEvaluation
from app.core.security import hash_password, create_access_token


def create_test_company(
    db: Session,
    email: str,
    company_name: str = "Brain Station 23",
    verification_status: str = "APPROVED",
    is_verified: bool = True,
) -> User:
    user = User(
        email=email,
        hashed_password=hash_password("Password123!"),
        role=UserRole.COMPANY,
        first_name="Brain",
        last_name="Station",
        is_active=True,
        is_verified=is_verified,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    profile = CompanyProfile(
        user_id=user.id,
        company_name=company_name,
        verification_status=verification_status,
        location="Dhaka, Bangladesh",
        industry="Software & IT",
    )
    db.add(profile)
    db.commit()
    db.refresh(user)
    return user


def create_test_user(
    db: Session,
    email: str,
    role: UserRole = UserRole.LEARNER,
    first_name: str = "Test",
    last_name: str = "Learner",
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


def get_auth_headers(user: User) -> dict:
    token = create_access_token(
        subject=user.id,
        claims={"email": user.email, "role": user.role.value},
    )
    return {"Authorization": f"Bearer {token}"}


def create_test_job(db: Session, company: User, title: str = "Junior Software Developer") -> JobPosting:
    job = JobPosting(
        company_id=company.id,
        title=title,
        posting_type="Job",
        work_mode="On-site",
        location="Dhaka, Bangladesh",
        description="Comprehensive developer role overview...",
        requirements="B.Sc in CSE or equivalent experience...",
        compensation="৳35,000 - ৳50,000",
        status=JobStatus.ACTIVE.value,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def test_add_screening_question_ac1(client: TestClient, db_session: Session):
    company = create_test_company(db_session, "comp_screen1@test.com")
    headers = get_auth_headers(company)
    job = create_test_job(db_session, company)

    payload = {
        "question_text": "Years of hands-on React/Node experience?",
        "question_type": "NUMERIC",
        "is_required": True,
        "is_deal_breaker": True,
        "deal_breaker_rule": "GTE",
        "deal_breaker_value": "2",
        "deal_breaker_label": "Auto-Disqualify if < 2 Years",
        "weight": 20,
    }

    res = client.post(
        f"/api/v1/jobs/{job.id}/screening-questions",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True
    assert body["data"]["question_text"] == payload["question_text"]
    assert body["data"]["is_deal_breaker"] is True
    assert body["data"]["deal_breaker_value"] == "2"


def test_unverified_company_blocked_from_adding_questions_ac1(client: TestClient, db_session: Session):
    unverified = create_test_company(db_session, "unverified_comp@test.com", verification_status="PENDING", is_verified=False)
    headers = get_auth_headers(unverified)
    job = create_test_job(db_session, unverified)

    payload = {
        "question_text": "Do you know SQL?",
        "question_type": "YES_NO",
    }

    res = client.post(
        f"/api/v1/jobs/{job.id}/screening-questions",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 403
    assert "COMPANY_NOT_VERIFIED" in res.json().get("message", "")


def test_automated_qualification_scoring_passed_ac2(client: TestClient, db_session: Session):
    company = create_test_company(db_session, "eval_comp@test.com")
    job = create_test_job(db_session, company)

    q1 = ScreeningQuestion(
        job_id=job.id,
        question_text="Years of hands-on React/Node experience?",
        question_type="NUMERIC",
        is_deal_breaker=True,
        deal_breaker_rule="GTE",
        deal_breaker_value="2",
        weight=20,
    )
    q2 = ScreeningQuestion(
        job_id=job.id,
        question_text="Are you comfortable working in hybrid mode in Dhaka?",
        question_type="YES_NO",
        is_deal_breaker=True,
        deal_breaker_rule="MANDATORY",
        deal_breaker_value="Yes",
        weight=20,
    )
    db_session.add_all([q1, q2])
    db_session.commit()
    db_session.refresh(q1)
    db_session.refresh(q2)

    submission = {
        "candidate_name": "Rashedul Islam",
        "candidate_email": "rashedul@test.com",
        "answers": {
            str(q1.id): "3 years",
            str(q2.id): "Yes",
        },
    }

    res = client.post(f"/api/v1/jobs/{job.id}/screen-candidate", json=submission)
    assert res.status_code == 201
    body = res.json()["data"]
    assert body["candidate_name"] == "Rashedul Islam"
    assert body["deal_breaker_passed"] is True
    assert body["match_score"] == 100
    assert body["status"] == "SHORTLISTED"


def test_deal_breaker_auto_disqualification_ac4(client: TestClient, db_session: Session):
    company = create_test_company(db_session, "dq_comp@test.com")
    job = create_test_job(db_session, company)

    q1 = ScreeningQuestion(
        job_id=job.id,
        question_text="Years of hands-on React/Node experience?",
        question_type="NUMERIC",
        is_deal_breaker=True,
        deal_breaker_rule="GTE",
        deal_breaker_value="2",
        weight=20,
    )
    db_session.add(q1)
    db_session.commit()
    db_session.refresh(q1)

    submission = {
        "candidate_name": "Junior Applicant",
        "candidate_email": "junior@test.com",
        "answers": {
            str(q1.id): "1 year",
        },
    }

    res = client.post(f"/api/v1/jobs/{job.id}/screen-candidate", json=submission)
    assert res.status_code == 201
    body = res.json()["data"]
    assert body["deal_breaker_passed"] is False
    assert "Failed" in body["deal_breaker_failed_reason"]
    assert body["status"] == "DISQUALIFIED"
    assert body["match_score"] <= 45


def test_recruiter_filtering_and_response_review_ac3(client: TestClient, db_session: Session):
    company = create_test_company(db_session, "filter_comp@test.com")
    headers = get_auth_headers(company)
    job = create_test_job(db_session, company)

    eval1 = CandidateEvaluation(
        job_id=job.id,
        candidate_name="Rashedul Islam",
        candidate_email="r@test.com",
        match_score=94,
        deal_breaker_passed=True,
        status="SHORTLISTED",
        key_answers_preview="3 yrs React/Node • Hybrid Confirmed",
    )
    eval2 = CandidateEvaluation(
        job_id=job.id,
        candidate_name="Disqualified Candidate",
        candidate_email="dq@test.com",
        match_score=45,
        deal_breaker_passed=False,
        status="DISQUALIFIED",
        key_answers_preview="1 yr experience • Remote Only",
    )
    db_session.add_all([eval1, eval2])
    db_session.commit()

    res_all = client.get(
        f"/api/v1/jobs/{job.id}/applicants",
        headers=headers,
    )
    assert res_all.status_code == 200
    assert res_all.json()["data"]["total"] == 2
    assert res_all.json()["data"]["passed_count"] == 1
    assert res_all.json()["data"]["disqualified_count"] == 1

    res_passed = client.get(
        f"/api/v1/jobs/{job.id}/applicants?deal_breaker_passed=true",
        headers=headers,
    )
    assert res_passed.status_code == 200
    assert res_passed.json()["data"]["total"] == 1
    assert res_passed.json()["data"]["items"][0]["candidate_name"] == "Rashedul Islam"


def test_candidate_status_update_shortlist_disqualify(client: TestClient, db_session: Session):
    company = create_test_company(db_session, "status_comp@test.com")
    headers = get_auth_headers(company)
    job = create_test_job(db_session, company)

    eval1 = CandidateEvaluation(
        job_id=job.id,
        candidate_name="Applicant",
        candidate_email="applicant@test.com",
        match_score=80,
        deal_breaker_passed=True,
        status="UNDER_REVIEW",
    )
    db_session.add(eval1)
    db_session.commit()
    db_session.refresh(eval1)

    res_shortlist = client.patch(
        f"/api/v1/applicants/{eval1.id}/status",
        json={"status": "SHORTLISTED"},
        headers=headers,
    )
    assert res_shortlist.status_code == 200
    assert res_shortlist.json()["data"]["status"] == "SHORTLISTED"

    res_dq = client.patch(
        f"/api/v1/applicants/{eval1.id}/status",
        json={"status": "DISQUALIFIED"},
        headers=headers,
    )
    assert res_dq.status_code == 200
    assert res_dq.json()["data"]["status"] == "DISQUALIFIED"


def test_admin_audit_compliance_guardrails_ac5(client: TestClient, db_session: Session):
    company = create_test_company(db_session, "audit_comp@test.com")
    admin = create_test_user(db_session, "admin_auditor@test.com", role=UserRole.ADMIN)
    headers = get_auth_headers(admin)
    job = create_test_job(db_session, company)

    q = ScreeningQuestion(
        job_id=job.id,
        question_text="Non-compliant question?",
        question_type="TEXT",
    )
    db_session.add(q)
    db_session.commit()
    db_session.refresh(q)

    res_del = client.delete(
        f"/api/v1/screening-questions/{q.id}",
        headers=headers,
    )
    assert res_del.status_code == 200
    assert res_del.json()["success"] is True

    assert db_session.get(ScreeningQuestion, q.id) is None
