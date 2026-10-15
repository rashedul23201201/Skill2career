import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.profile import CompanyProfile
from app.models.job import JobPosting, JobStatus
from app.core.security import hash_password, create_access_token


def create_company_with_status(
    db: Session,
    email: str,
    company_name: str,
    verification_status: str = "APPROVED",
    is_active: bool = True,
) -> User:
    user = User(
        email=email,
        hashed_password=hash_password("Password123!"),
        role=UserRole.COMPANY,
        first_name="Lead",
        last_name="Recruiter",
        is_active=is_active,
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
    posting_type: str = "Job",
    work_mode: str = "On-site",
    location: str = "Dhaka",
    description: str = "Job description text",
    requirements: str = "Job requirements text",
    compensation: str = "৳40K – ৳60K",
    salary_min: int = 40000,
    salary_max: int = 60000,
    experience_level: str = "Entry Level",
    category: str = "Software Engineering",
    status: str = "ACTIVE",
    deadline_days: int = 15,
    created_days_ago: int = 1,
) -> JobPosting:
    now = datetime.now(timezone.utc)
    job = JobPosting(
        company_id=company.id,
        title=title,
        posting_type=posting_type,
        work_mode=work_mode,
        location=location,
        description=description,
        requirements=requirements,
        skills=["Python", "FastAPI"],
        compensation=compensation,
        salary_min=salary_min,
        salary_max=salary_max,
        experience_level=experience_level,
        category=category,
        status=status,
        deadline=now + timedelta(days=deadline_days),
        created_at=now - timedelta(days=created_days_ago),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def test_skl5_taxonomies_endpoint(client: TestClient, db_session: Session):
    """SKL-5: Taxonomies endpoint returns facet categories, modes, locations, and salary presets."""
    response = client.get("/api/v1/jobs/taxonomies")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    facets = data["data"]
    assert "posting_types" in facets
    assert "work_modes" in facets
    assert "experience_levels" in facets
    assert "categories" in facets
    assert "locations" in facets
    assert "salary_presets" in facets
    assert any(p["label"] == "৳25,000 - ৳50,000" for p in facets["salary_presets"])


def test_skl5_keyword_search_across_multiple_fields(client: TestClient, db_session: Session):
    """SKL-5 AC-1: Keyword search matches on title, description, requirements, location, and company name."""
    company = create_company_with_status(db_session, "corp_search1@skill2career.com", "Brain Station 23")

    seed_job(
        db_session,
        company,
        title="Full Stack Django Developer",
        description="Build high-performance web backends.",
        requirements="Python, Django, PostgreSQL, and React.",
        location="Dhaka",
    )
    seed_job(
        db_session,
        company,
        title="Machine Learning Engineer",
        description="Develop neural networks and PyTorch pipelines.",
        requirements="Deep learning, NumPy, Scikit-learn.",
        location="Chittagong",
    )

    # 1. Search by title keyword (case-insensitive)
    r1 = client.get("/api/v1/jobs/search?search=django")
    assert r1.status_code == 200
    items1 = r1.json()["data"]["items"]
    assert len(items1) == 1
    assert items1[0]["title"] == "Full Stack Django Developer"

    # 2. Search by requirements keyword
    r2 = client.get("/api/v1/jobs/search?search=pytorch")
    assert r2.status_code == 200
    items2 = r2.json()["data"]["items"]
    assert len(items2) == 1
    assert items2[0]["title"] == "Machine Learning Engineer"

    # 3. Search by company name
    r3 = client.get("/api/v1/jobs/search?search=Brain Station")
    assert r3.status_code == 200
    assert len(r3.json()["data"]["items"]) == 2


def test_skl5_multi_criteria_filtering(client: TestClient, db_session: Session):
    """SKL-5 AC-2: Simultaneous filtering by type, work mode, experience level, and salary ranges."""
    company = create_company_with_status(db_session, "corp_filter1@skill2career.com", "Pathao")

    # Job A: Remote Internship, Entry Level, ৳20K
    seed_job(
        db_session,
        company,
        title="Remote Mobile Intern",
        posting_type="Internship",
        work_mode="Remote",
        experience_level="Internship",
        compensation="৳20K / month",
        salary_min=20000,
        salary_max=20000,
    )

    # Job B: On-site Job, Senior, ৳90K - ৳120K
    seed_job(
        db_session,
        company,
        title="Lead Infrastructure Engineer",
        posting_type="Job",
        work_mode="On-site",
        experience_level="Senior",
        compensation="৳90K – ৳120K",
        salary_min=90000,
        salary_max=120000,
    )

    # Filter 1: Internship + Remote
    r1 = client.get("/api/v1/jobs/search?posting_type=Internship&work_mode=Remote")
    assert r1.status_code == 200
    items1 = r1.json()["data"]["items"]
    assert len(items1) == 1
    assert items1[0]["title"] == "Remote Mobile Intern"

    # Filter 2: Min salary ৳80K (should match Senior Engineer)
    r2 = client.get("/api/v1/jobs/search?min_salary=80000")
    assert r2.status_code == 200
    items2 = r2.json()["data"]["items"]
    assert len(items2) == 1
    assert items2[0]["title"] == "Lead Infrastructure Engineer"

    # Filter 3: Max salary ৳25K (should match Intern)
    r3 = client.get("/api/v1/jobs/search?max_salary=25000")
    assert r3.status_code == 200
    items3 = r3.json()["data"]["items"]
    assert any(j["title"] == "Remote Mobile Intern" for j in items3)


def test_skl5_dynamic_sorting(client: TestClient, db_session: Session):
    """SKL-5 AC-3: Dynamic sorting by highest salary, most recent, and nearest deadline."""
    company = create_company_with_status(db_session, "corp_sort@skill2career.com", "bKash Limited")

    # Job 1: Low salary, created 3 days ago, deadline in 5 days
    j1 = seed_job(
        db_session,
        company,
        title="Junior Developer",
        salary_min=30000,
        salary_max=40000,
        deadline_days=5,
        created_days_ago=3,
    )
    # Job 2: High salary, created 1 day ago, deadline in 20 days
    j2 = seed_job(
        db_session,
        company,
        title="Principal Architect",
        salary_min=150000,
        salary_max=200000,
        deadline_days=20,
        created_days_ago=1,
    )
    # Job 3: Mid salary, created 2 days ago, deadline in 2 days (urgent)
    j3 = seed_job(
        db_session,
        company,
        title="QA Automation Lead",
        salary_min=70000,
        salary_max=90000,
        deadline_days=2,
        created_days_ago=2,
    )

    # 1. Sort by Highest Salary (salary_high)
    r_sal = client.get("/api/v1/jobs/search?sort_by=salary_high")
    assert r_sal.status_code == 200
    items_sal = r_sal.json()["data"]["items"]
    assert items_sal[0]["title"] == "Principal Architect"

    # 2. Sort by Most Recent (recent)
    r_rec = client.get("/api/v1/jobs/search?sort_by=recent")
    assert r_rec.status_code == 200
    items_rec = r_rec.json()["data"]["items"]
    assert items_rec[0]["title"] == "Principal Architect"

    # 3. Sort by Application Deadline (deadline ascending)
    r_dl = client.get("/api/v1/jobs/search?sort_by=deadline")
    assert r_dl.status_code == 200
    items_dl = r_dl.json()["data"]["items"]
    assert items_dl[0]["title"] == "QA Automation Lead"


def test_skl5_verified_company_listing_enforcement(client: TestClient, db_session: Session):
    """SKL-5 AC-4: Only approved verified companies' vacancies appear in public search."""
    verified_company = create_company_with_status(
        db_session, "corp_approved@skill2career.com", "Approved Tech Ltd", verification_status="APPROVED"
    )
    unapproved_company = create_company_with_status(
        db_session, "corp_pending_search@skill2career.com", "Suspicious Corp", verification_status="PENDING"
    )

    # Job by approved company
    seed_job(db_session, verified_company, title="Verified Legitimate Job", status="ACTIVE")

    # Job by unapproved company (even if status is ACTIVE)
    seed_job(db_session, unapproved_company, title="Unverified Company Vacancy", status="ACTIVE")

    # Public candidate searches
    response = client.get("/api/v1/jobs/search")
    assert response.status_code == 200
    items = response.json()["data"]["items"]

    titles = [j["title"] for j in items]
    assert "Verified Legitimate Job" in titles
    assert "Unverified Company Vacancy" not in titles


def test_skl5_empty_state_handling(client: TestClient, db_session: Session):
    """SKL-5 AC-3: Clean empty state returned when no vacancies match filter criteria."""
    response = client.get("/api/v1/jobs/search?search=NonExistentSkillXYZ12345")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total"] == 0
    assert len(data["data"]["items"]) == 0
