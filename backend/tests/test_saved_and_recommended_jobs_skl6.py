import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.profile import CompanyProfile, LearnerProfile
from app.models.job import JobPosting, JobStatus, SavedJob
from app.models.application import JobApplication, ApplicationStatus
from app.core.security import hash_password, create_access_token


def create_user_with_token(
    db: Session,
    email: str,
    role: UserRole = UserRole.LEARNER,
    first_name: str = "Test",
    last_name: str = "User",
) -> tuple[User, dict]:
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

    token = create_access_token(
        subject=user.id,
        claims={"email": user.email, "role": user.role.value},
    )
    headers = {"Authorization": f"Bearer {token}"}
    return user, headers


def create_company_user(
    db: Session,
    email: str,
    company_name: str,
    verification_status: str = "APPROVED",
) -> User:
    user = User(
        email=email,
        hashed_password=hash_password("Password123!"),
        role=UserRole.COMPANY,
        first_name="Hiring",
        last_name="Manager",
        is_active=True,
        is_verified=(verification_status == "APPROVED"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    profile = CompanyProfile(
        user_id=user.id,
        company_name=company_name,
        verification_status=verification_status,
        location="Dhaka, Bangladesh",
        industry="Technology",
    )
    db.add(profile)
    db.commit()
    db.refresh(user)
    return user


def seed_job(
    db: Session,
    company: User,
    title: str,
    skills: list[str] = None,
    requirements: str = "Standard requirements",
    category: str = "Software Engineering",
    status: str = "ACTIVE",
    deadline_offset_days: int = 15,
) -> JobPosting:
    now = datetime.now(timezone.utc)
    job = JobPosting(
        company_id=company.id,
        title=title,
        posting_type="Job",
        work_mode="Remote",
        location="Dhaka",
        description="Comprehensive role overview",
        requirements=requirements,
        skills=skills or ["Python", "FastAPI"],
        compensation="৳50,000 - ৳70,000",
        salary_min=50000,
        salary_max=70000,
        experience_level="Entry Level",
        category=category,
        status=status,
        deadline=now + timedelta(days=deadline_offset_days),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def test_save_job_success_and_1_click_toggle(client: TestClient, db_session: Session):
    """Test 1-click bookmarking and unsaving via POST /api/v1/jobs/{id}/save (SKL-6)."""
    company = create_company_user(db_session, "comp1@example.com", "Brain Station")
    job = seed_job(db_session, company, "Junior Python Engineer")

    learner, headers = create_user_with_token(db_session, "learner1@example.com", UserRole.LEARNER)

    # 1. First click: Save job
    res1 = client.post(f"/api/v1/jobs/{job.id}/save", headers=headers)
    assert res1.status_code == 200
    data1 = res1.json()["data"]
    assert data1["is_saved"] is True
    assert data1["job_id"] == job.id
    assert data1["saved_job_id"] is not None
    assert "saved successfully" in data1["message"].lower()

    # Verify persisted in database
    saved_db = db_session.query(SavedJob).filter_by(learner_id=learner.id, job_id=job.id).first()
    assert saved_db is not None

    # 2. Second click: Toggle / Unsave
    res2 = client.post(f"/api/v1/jobs/{job.id}/save", headers=headers)
    assert res2.status_code == 200
    data2 = res2.json()["data"]
    assert data2["is_saved"] is False
    assert data2["saved_job_id"] is None
    assert "removed" in data2["message"].lower()

    # Verify removed from database
    saved_db2 = db_session.query(SavedJob).filter_by(learner_id=learner.id, job_id=job.id).first()
    assert saved_db2 is None

    # 3. Third click: Toggle back to Saved
    res3 = client.post(f"/api/v1/jobs/{job.id}/save", headers=headers)
    assert res3.status_code == 200
    assert res3.json()["data"]["is_saved"] is True


def test_explicit_save_and_unsave_endpoints(client: TestClient, db_session: Session):
    """Test explicit action parameters and DELETE /api/v1/jobs/{id}/save (SKL-6)."""
    company = create_company_user(db_session, "comp2@example.com", "Kona SL")
    job = seed_job(db_session, company, "Frontend React Developer")

    learner, headers = create_user_with_token(db_session, "learner_explicit@example.com", UserRole.LEARNER)

    # Explicit action=save
    res_save = client.post(f"/api/v1/jobs/{job.id}/save?action=save", headers=headers)
    assert res_save.status_code == 200
    assert res_save.json()["data"]["is_saved"] is True

    # Repeated explicit action=save is idempotent
    res_save_again = client.post(f"/api/v1/jobs/{job.id}/save?action=save", headers=headers)
    assert res_save_again.status_code == 200
    assert res_save_again.json()["data"]["is_saved"] is True

    # Explicit DELETE /api/v1/jobs/{id}/save
    res_del = client.delete(f"/api/v1/jobs/{job.id}/save", headers=headers)
    assert res_del.status_code == 200
    assert res_del.json()["data"]["is_saved"] is False


def test_get_saved_jobs_with_real_time_status(client: TestClient, db_session: Session):
    """Test real-time status reflection (Active, Closed, Expired) on saved jobs (SKL-6)."""
    company = create_company_user(db_session, "comp3@example.com", "Pathao")

    # Job A: ACTIVE with future deadline -> Active
    job_active = seed_job(db_session, company, "Active Backend Lead", status="ACTIVE", deadline_offset_days=10)

    # Job B: CLOSED status -> Closed
    job_closed = seed_job(db_session, company, "Closed DevOps Engineer", status="CLOSED", deadline_offset_days=10)

    # Job C: ACTIVE status with past deadline -> Expired
    job_expired = seed_job(db_session, company, "Expired QA Tester", status="ACTIVE", deadline_offset_days=-2)

    learner, headers = create_user_with_token(db_session, "status_learner@example.com", UserRole.LEARNER)

    # Save all three jobs
    client.post(f"/api/v1/jobs/{job_active.id}/save", headers=headers)
    client.post(f"/api/v1/jobs/{job_closed.id}/save", headers=headers)
    client.post(f"/api/v1/jobs/{job_expired.id}/save", headers=headers)

    # Retrieve saved jobs collection
    res = client.get("/api/v1/learners/saved-jobs", headers=headers)
    assert res.status_code == 200
    items = res.json()["data"]
    assert len(items) == 3

    status_map = {item["job_id"]: item for item in items}

    # Verify real-time status calculations
    assert status_map[job_active.id]["computed_status"] == "Active"
    assert status_map[job_active.id]["is_active"] is True
    assert status_map[job_active.id]["is_expired"] is False
    assert status_map[job_active.id]["is_closed"] is False

    assert status_map[job_closed.id]["computed_status"] == "Closed"
    assert status_map[job_closed.id]["is_active"] is False
    assert status_map[job_closed.id]["is_closed"] is True

    assert status_map[job_expired.id]["computed_status"] == "Expired"
    assert status_map[job_expired.id]["is_active"] is False
    assert status_map[job_expired.id]["is_expired"] is True

    # Test status filter: ?status=active
    res_filter = client.get("/api/v1/learners/saved-jobs?status=active", headers=headers)
    assert res_filter.status_code == 200
    filtered_items = res_filter.json()["data"]
    assert len(filtered_items) == 1
    assert filtered_items[0]["job_id"] == job_active.id


def test_saved_jobs_cross_user_isolation(client: TestClient, db_session: Session):
    """Test learners can only view and delete their own saved jobs (SKL-6)."""
    company = create_company_user(db_session, "comp4@example.com", "Chaldal")
    job = seed_job(db_session, company, "Data Analyst")

    learner_a, headers_a = create_user_with_token(db_session, "learner_a@example.com", UserRole.LEARNER)
    learner_b, headers_b = create_user_with_token(db_session, "learner_b@example.com", UserRole.LEARNER)

    # Learner A saves the job
    res_save = client.post(f"/api/v1/jobs/{job.id}/save", headers=headers_a)
    saved_id = res_save.json()["data"]["saved_job_id"]

    # Learner B's saved list should be empty
    res_list_b = client.get("/api/v1/learners/saved-jobs", headers=headers_b)
    assert res_list_b.status_code == 200
    assert len(res_list_b.json()["data"]) == 0

    # Learner B cannot delete Learner A's saved job (forbidden/not found)
    res_del_b = client.delete(f"/api/v1/learners/saved-jobs/{saved_id}", headers=headers_b)
    assert res_del_b.status_code in (403, 404)

    # Learner A can delete their own saved job
    res_del_a = client.delete(f"/api/v1/learners/saved-jobs/{saved_id}", headers=headers_a)
    assert res_del_a.status_code == 200

    # Ensure list is now empty for Learner A
    res_list_a = client.get("/api/v1/learners/saved-jobs", headers=headers_a)
    assert len(res_list_a.json()["data"]) == 0


def test_delete_saved_job_by_job_id(client: TestClient, db_session: Session):
    """Test deleting from saved collection using the job_id directly."""
    company = create_company_user(db_session, "comp5@example.com", "Samsung R&D")
    job = seed_job(db_session, company, "Systems Engineer")

    learner, headers = create_user_with_token(db_session, "learner_del_jobid@example.com", UserRole.LEARNER)
    client.post(f"/api/v1/jobs/{job.id}/save", headers=headers)

    # Delete passing the vacancy job_id
    res_del = client.delete(f"/api/v1/learners/saved-jobs/{job.id}", headers=headers)
    assert res_del.status_code == 200
    assert res_del.json()["data"]["job_id"] == job.id

    # Verify removed
    res_check = client.get("/api/v1/learners/saved-jobs", headers=headers)
    assert len(res_check.json()["data"]) == 0


def test_unauthorized_role_rejected(client: TestClient, db_session: Session):
    """Test unauthorized roles (Recruiters) and guests are rejected (HTTP 401/403)."""
    company_user = create_company_user(db_session, "recruiter_only@example.com", "TigerIT")
    token = create_access_token(
        subject=company_user.id,
        claims={"email": company_user.email, "role": company_user.role.value},
    )
    company_headers = {"Authorization": f"Bearer {token}"}

    job = seed_job(db_session, company_user, "Software Architect")

    # Unauthenticated -> 401
    res_unauth = client.post(f"/api/v1/jobs/{job.id}/save")
    assert res_unauth.status_code == 401

    # Company role -> 403
    res_company = client.post(f"/api/v1/jobs/{job.id}/save", headers=company_headers)
    assert res_company.status_code == 403


def test_recommended_jobs_skills_and_role_matching(client: TestClient, db_session: Session):
    """Test profile-to-job recommendation algorithm scoring matching skills & target_role (SKL-6)."""
    company = create_company_user(db_session, "comp_rec@example.com", "Optimizely")

    # Job 1: Highly matching Python & FastAPI backend role
    job_high = seed_job(
        db_session,
        company,
        title="Junior Python Backend Engineer",
        skills=["Python", "FastAPI", "PostgreSQL"],
        requirements="Looking for Python and FastAPI developers with PostgreSQL expertise.",
        category="Software Engineering",
    )

    # Job 2: Unrelated UI/UX design role
    job_low = seed_job(
        db_session,
        company,
        title="Senior UI/UX Product Designer",
        skills=["Figma", "Design Systems"],
        requirements="Must master Figma, user research, and wireframing.",
        category="Design",
    )

    learner, headers = create_user_with_token(db_session, "learner_rec@example.com", UserRole.LEARNER)

    # Configure learner profile with relevant skills and target role
    profile = LearnerProfile(
        user_id=learner.id,
        skills={"items": ["Python", "FastAPI", "SQL", "Git"]},
        target_role="Python Backend Engineer",
        primary_track="Software Engineering",
        completion_pct=75,
    )
    db_session.add(profile)
    db_session.commit()

    # Query recommendations
    res = client.get("/api/v1/learners/recommended-jobs", headers=headers)
    assert res.status_code == 200
    recommendations = res.json()["data"]
    assert len(recommendations) >= 2

    # High match job should be ranked first with a score >= 75
    top_job = recommendations[0]
    assert top_job["id"] == job_high.id
    assert top_job["match_score"] >= 75
    assert "Python" in top_job["matched_skills"]
    assert "FastAPI" in top_job["matched_skills"]
    assert top_job["recommendation_reason"] is not None

    # Lower match job should have lower score
    low_job = next(j for j in recommendations if j["id"] == job_low.id)
    assert top_job["match_score"] > low_job["match_score"]


def test_recommended_jobs_excludes_already_applied_vacancies(client: TestClient, db_session: Session):
    """Test recommendation engine filters out already applied vacancies (SKL-6 AC-3)."""
    company = create_company_user(db_session, "comp_app@example.com", "Therap BD")

    job_applied = seed_job(db_session, company, "Applied Python Vacancy", skills=["Python"])
    job_unapplied = seed_job(db_session, company, "Fresh Python Vacancy", skills=["Python"])

    learner, headers = create_user_with_token(db_session, "applied_learner@example.com", UserRole.LEARNER)

    profile = LearnerProfile(
        user_id=learner.id,
        skills={"items": ["Python"]},
        target_role="Python Developer",
    )
    db_session.add(profile)

    # Submit application for job_applied
    app_record = JobApplication(
        job_id=job_applied.id,
        learner_id=learner.id,
        status=ApplicationStatus.SUBMITTED.value,
    )
    db_session.add(app_record)
    db_session.commit()

    # Fetch recommendations
    res = client.get("/api/v1/learners/recommended-jobs", headers=headers)
    assert res.status_code == 200
    rec_ids = [j["id"] for j in res.json()["data"]]

    # job_applied MUST be excluded; job_unapplied MUST be included
    assert job_applied.id not in rec_ids
    assert job_unapplied.id in rec_ids


def test_recommended_jobs_excludes_unverified_company_jobs(client: TestClient, db_session: Session):
    """Test recommendations exclude vacancies from unverified or rejected company accounts (SKL-5 & SKL-6)."""
    approved_company = create_company_user(db_session, "approved_co@example.com", "Verified Co", "APPROVED")
    pending_company = create_company_user(db_session, "pending_co@example.com", "Unverified Co", "PENDING")

    job_verified = seed_job(db_session, approved_company, "Verified Python Opening", skills=["Python"])
    job_unverified = seed_job(db_session, pending_company, "Unverified Python Opening", skills=["Python"])

    learner, headers = create_user_with_token(db_session, "verify_test_learner@example.com", UserRole.LEARNER)
    profile = LearnerProfile(user_id=learner.id, skills={"items": ["Python"]})
    db_session.add(profile)
    db_session.commit()

    res = client.get("/api/v1/learners/recommended-jobs", headers=headers)
    assert res.status_code == 200
    rec_ids = [j["id"] for j in res.json()["data"]]

    assert job_verified.id in rec_ids
    assert job_unverified.id not in rec_ids


def test_recommended_jobs_reflects_saved_badge(client: TestClient, db_session: Session):
    """Test recommendation cards reflect `is_saved == True` when previously bookmarked."""
    company = create_company_user(db_session, "badge_co@example.com", "Badge Tech", "APPROVED")
    job = seed_job(db_session, company, "Django Engineer", skills=["Python", "Django"])

    learner, headers = create_user_with_token(db_session, "badge_learner@example.com", UserRole.LEARNER)
    profile = LearnerProfile(user_id=learner.id, skills={"items": ["Python"]})
    db_session.add(profile)
    db_session.commit()

    # Pre-save the job
    client.post(f"/api/v1/jobs/{job.id}/save", headers=headers)

    res = client.get("/api/v1/learners/recommended-jobs", headers=headers)
    assert res.status_code == 200
    rec = next(j for j in res.json()["data"] if j["id"] == job.id)
    assert rec["is_saved"] is True
