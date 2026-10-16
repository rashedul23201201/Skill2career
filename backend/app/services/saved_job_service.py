import logging
import math
import re
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple, Set
from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    BadRequestException,
)
from app.models.user import User, UserRole
from app.models.job import JobPosting, JobStatus, SavedJob
from app.models.profile import LearnerProfile, CompanyProfile
from app.models.application import JobApplication
from app.repositories.saved_job_repository import SavedJobRepository
from app.repositories.job_repository import JobRepository
from app.repositories.learner_repository import LearnerRepository
from app.services.job_service import JobService
from app.services.learner_service import LearnerService
from app.schemas.job import (
    JobPostingResponse,
    SavedJobItemResponse,
    SavedJobToggleResponse,
    RecommendedJobResponse,
)

logger = logging.getLogger(__name__)


class SavedJobService:
    """Service handling saved vacancies, real-time status reflection, and profile-to-job recommendations (SKL-6)."""

    def __init__(
        self,
        saved_repo: SavedJobRepository = SavedJobRepository(),
        job_repo: JobRepository = JobRepository(),
        learner_repo: LearnerRepository = LearnerRepository(),
        job_service: JobService = JobService(),
    ):
        self.saved_repo = saved_repo
        self.job_repo = job_repo
        self.learner_repo = learner_repo
        self.job_service = job_service

    @staticmethod
    def compute_job_status(job: JobPosting) -> Tuple[str, bool, bool, bool]:
        """Compute real-time lifecycle status of a job vacancy.
        
        Returns:
            Tuple of (computed_status, is_active, is_expired, is_closed)
            where computed_status is one of 'Active', 'Closed', 'Expired'.
        """
        now = datetime.now(timezone.utc)
        deadline = job.deadline
        if deadline and deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)

        is_expired = bool(deadline and deadline < now)
        is_closed = bool(job.status != JobStatus.ACTIVE.value and not is_expired)
        is_active = bool(job.status == JobStatus.ACTIVE.value and not is_expired)

        if is_expired:
            computed_status = "Expired"
        elif is_closed:
            computed_status = "Closed"
        else:
            computed_status = "Active"

        return computed_status, is_active, is_expired, is_closed

    def toggle_save_job(
        self,
        db: Session,
        job_id: int,
        current_user: User,
        action: Optional[str] = None,
    ) -> SavedJobToggleResponse:
        """1-click save, unsave, or toggle bookmark for a vacancy (SKL-6)."""
        # RBAC: Only learners and admins may save vacancies
        if current_user.role not in (UserRole.LEARNER, UserRole.ADMIN):
            raise ForbiddenException("Only registered learners may bookmark and save vacancies")

        # Verify vacancy exists
        job = self.job_repo.get_by_id(db, job_id)
        if not job:
            raise NotFoundException(f"Job vacancy #{job_id} does not exist")

        computed_status, _, _, _ = self.compute_job_status(job)
        existing = self.saved_repo.get_by_learner_and_job(db, current_user.id, job_id)

        # Handle explicit actions
        if action == "save":
            if existing:
                return SavedJobToggleResponse(
                    job_id=job_id,
                    is_saved=True,
                    saved_job_id=existing.id,
                    message="Job is already in your saved list",
                    computed_status=computed_status,
                )
            created = self.saved_repo.create(db, current_user.id, job_id)
            return SavedJobToggleResponse(
                job_id=job_id,
                is_saved=True,
                saved_job_id=created.id,
                message="Job saved successfully",
                computed_status=computed_status,
            )

        if action == "unsave":
            if existing:
                self.saved_repo.delete(db, existing)
            return SavedJobToggleResponse(
                job_id=job_id,
                is_saved=False,
                saved_job_id=None,
                message="Job removed from saved list",
                computed_status=computed_status,
            )

        # Default: 1-click toggle
        if existing:
            self.saved_repo.delete(db, existing)
            return SavedJobToggleResponse(
                job_id=job_id,
                is_saved=False,
                saved_job_id=None,
                message="Job removed from saved list",
                computed_status=computed_status,
            )
        else:
            created = self.saved_repo.create(db, current_user.id, job_id)
            return SavedJobToggleResponse(
                job_id=job_id,
                is_saved=True,
                saved_job_id=created.id,
                message="Job saved successfully",
                computed_status=computed_status,
            )

    def get_saved_jobs(
        self,
        db: Session,
        current_user: User,
        status_filter: Optional[str] = None,
    ) -> List[SavedJobItemResponse]:
        """Fetch authenticated learner's saved vacancies collection with real-time status (SKL-6)."""
        if current_user.role not in (UserRole.LEARNER, UserRole.ADMIN):
            raise ForbiddenException("Only registered learners can access saved vacancies")

        saved_records = self.saved_repo.list_by_learner(db, current_user.id)
        results: List[SavedJobItemResponse] = []

        for record in saved_records:
            job = record.job
            if not job:
                continue

            computed_status, is_active, is_expired, is_closed = self.compute_job_status(job)

            # Optional status filtering: 'active', 'closed', 'expired'
            if status_filter:
                filter_norm = status_filter.strip().lower()
                if filter_norm != "all" and computed_status.lower() != filter_norm:
                    continue

            job_resp = self.job_service._to_job_response(job)
            results.append(
                SavedJobItemResponse(
                    id=record.id,
                    saved_job_id=record.id,
                    job_id=record.job_id,
                    learner_id=record.learner_id,
                    saved_at=record.saved_at,
                    computed_status=computed_status,
                    is_active=is_active,
                    is_expired=is_expired,
                    is_closed=is_closed,
                    job=job_resp,
                )
            )

        return results

    def delete_saved_job(
        self,
        db: Session,
        current_user: User,
        target_id: int,
    ) -> dict:
        """Remove a vacancy from the learner's saved collection by saved_job_id or job_id (SKL-6)."""
        if current_user.role not in (UserRole.LEARNER, UserRole.ADMIN):
            raise ForbiddenException("Only registered learners can modify saved vacancies")

        # 1. Try finding by saved_job.id for current user
        record = self.saved_repo.get_by_id(db, target_id)
        if record:
            if record.learner_id != current_user.id and current_user.role != UserRole.ADMIN:
                raise ForbiddenException("You cannot delete another learner's saved vacancy")
            job_id = record.job_id
            self.saved_repo.delete(db, record)
            return {
                "saved_job_id": target_id,
                "job_id": job_id,
                "message": "Saved job removed successfully",
            }

        # 2. Try finding by job_id for current user
        record = self.saved_repo.get_by_learner_and_job(db, current_user.id, target_id)
        if record:
            saved_id = record.id
            self.saved_repo.delete(db, record)
            return {
                "saved_job_id": saved_id,
                "job_id": target_id,
                "message": "Saved job removed successfully",
            }

        raise NotFoundException(f"Saved job record #{target_id} not found")

    def get_recommended_jobs(
        self,
        db: Session,
        current_user: User,
        limit: int = 10,
    ) -> List[RecommendedJobResponse]:
        """Profile-to-Job Smart Recommendation scoring engine comparing LearnerProfile skills & target_role (SKL-6)."""
        if current_user.role not in (UserRole.LEARNER, UserRole.ADMIN):
            raise ForbiddenException("Only registered learners can access smart recommendations")

        limit = min(50, max(1, limit))

        # 1. Retrieve learner profile metadata
        profile = self.learner_repo.get_by_user_id(db, current_user.id)
        learner_skills = LearnerService.extract_skills_list(profile.skills if profile else None)
        target_role = (profile.target_role or "").strip() if profile else ""
        primary_track = (profile.primary_track or "").strip() if profile else ""

        # 2. Filter out vacancies already applied by the learner (SKL-6 AC-3)
        applied_stmt = select(JobApplication.job_id).where(JobApplication.learner_id == current_user.id)
        applied_job_ids = set(db.execute(applied_stmt).scalars().all())

        # 3. Retrieve saved job IDs for badge reflection
        saved_job_ids = self.saved_repo.get_saved_job_ids(db, current_user.id)

        # 4. Query active vacancies from approved companies
        now = datetime.now(timezone.utc)
        stmt = (
            select(JobPosting)
            .options(
                joinedload(JobPosting.company).joinedload(User.company_profile)
            )
            .join(User, JobPosting.company_id == User.id)
            .outerjoin(CompanyProfile, User.id == CompanyProfile.user_id)
            .where(
                JobPosting.status == JobStatus.ACTIVE.value,
                User.is_active.is_(True),
                func.upper(CompanyProfile.verification_status) == "APPROVED",
            )
        )

        # Exclude applied vacancies
        if applied_job_ids:
            stmt = stmt.where(JobPosting.id.not_in(applied_job_ids))

        # Exclude expired vacancies
        stmt = stmt.where(or_(JobPosting.deadline.is_(None), JobPosting.deadline >= now))

        candidate_jobs = list(db.execute(stmt).scalars().all())

        # 5. Score vacancies using skill overlap and role alignment
        scored_jobs: List[Tuple[int, RecommendedJobResponse]] = []

        learner_skills_clean = [s.strip() for s in learner_skills if s and s.strip()]
        learner_skills_lower = {s.lower(): s for s in learner_skills_clean}

        for job in candidate_jobs:
            score, matched_skills, missing_skills, reason = self._calculate_match_score(
                job=job,
                learner_skills_clean=learner_skills_clean,
                learner_skills_lower=learner_skills_lower,
                target_role=target_role,
                primary_track=primary_track,
            )

            job_resp = self.job_service._to_job_response(job)
            rec_item = RecommendedJobResponse(
                id=job_resp.id,
                company_id=job_resp.company_id,
                company_name=job_resp.company_name,
                company_logo_url=job_resp.company_logo_url,
                company_location=job_resp.company_location,
                company_industry=job_resp.company_industry,
                company_website=job_resp.company_website,
                title=job_resp.title,
                posting_type=job_resp.posting_type,
                work_mode=job_resp.work_mode,
                location=job_resp.location,
                description=job_resp.description,
                requirements=job_resp.requirements,
                skills=job_resp.skills,
                compensation=job_resp.compensation,
                salary_min=job_resp.salary_min,
                salary_max=job_resp.salary_max,
                duration=job_resp.duration,
                experience_level=job_resp.experience_level,
                category=job_resp.category,
                deadline=job_resp.deadline,
                status=job_resp.status,
                applications_count=job_resp.applications_count,
                created_at=job_resp.created_at,
                updated_at=job_resp.updated_at,
                match_score=score,
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                is_saved=(job.id in saved_job_ids),
                has_applied=False,
                recommendation_reason=reason,
                job=job_resp,
            )
            scored_jobs.append((score, rec_item))

        # 6. Sort descending by match score, then by recency
        scored_jobs.sort(key=lambda x: (x[0], x[1].created_at), reverse=True)

        return [item[1] for item in scored_jobs[:limit]]

    def _calculate_match_score(
        self,
        job: JobPosting,
        learner_skills_clean: List[str],
        learner_skills_lower: Dict[str, str],
        target_role: str,
        primary_track: str,
    ) -> Tuple[int, List[str], List[str], str]:
        """Internal heuristic scoring comparing skills (60%) and target role/track (40%)."""
        job_skills_clean = [s.strip() for s in (job.skills or []) if s and s.strip()]
        job_skills_lower = {s.lower(): s for s in job_skills_clean}

        req_text = f"{job.title} {job.category} {job.requirements} {job.description}".lower()

        matched_skills_map: Dict[str, str] = {}
        for skl_lower, orig in learner_skills_lower.items():
            if skl_lower in job_skills_lower:
                matched_skills_map[skl_lower] = orig
            elif re.search(r'\b' + re.escape(skl_lower) + r'\b', req_text):
                matched_skills_map[skl_lower] = orig

        matched_skills = list(matched_skills_map.values())
        missing_skills = [orig for skl_lower, orig in job_skills_lower.items() if skl_lower not in matched_skills_map]

        # 1. Skills Score (0 - 100)
        if job_skills_clean:
            explicit_match_cnt = sum(1 for skl_lower in job_skills_lower if skl_lower in matched_skills_map)
            explicit_ratio = explicit_match_cnt / max(1, len(job_skills_clean))
            coverage_ratio = len(matched_skills) / max(1, len(learner_skills_clean)) if learner_skills_clean else 0
            skill_score = min(100.0, (explicit_ratio * 0.70 + coverage_ratio * 0.30) * 100)
        elif learner_skills_clean:
            match_cnt = len(matched_skills)
            skill_score = min(100.0, (match_cnt / max(1, min(len(learner_skills_clean), 4))) * 100)
        else:
            skill_score = 45.0

        # 2. Role & Track Score (0 - 100)
        role_score = 45.0
        if target_role:
            clean_target = target_role.lower()
            clean_title = job.title.lower()
            if clean_target in clean_title or clean_title in clean_target:
                role_score = 100.0
            else:
                stop_words = {"a", "an", "the", "in", "for", "at", "to", "and", "of", "developer", "engineer"}
                target_words = [w for w in re.findall(r'\w+', clean_target) if len(w) > 2]
                meaningful_target = [w for w in target_words if w not in stop_words] or target_words
                matched_words = [w for w in meaningful_target if w in clean_title or w in job.category.lower()]
                if meaningful_target:
                    role_score = min(100.0, (len(matched_words) / len(meaningful_target)) * 95.0)
        elif primary_track:
            clean_track = primary_track.lower()
            if clean_track in job.category.lower() or clean_track in job.title.lower():
                role_score = 80.0

        # Weighted aggregate score
        raw_score = 0.60 * skill_score + 0.40 * role_score
        if skill_score >= 90 and role_score >= 90:
            final_score = min(98, round(raw_score))
        else:
            final_score = max(35, min(95, round(raw_score)))

        # Qualitative reason tag
        if matched_skills and role_score >= 70:
            reason = f"Matches {len(matched_skills)} of your skills ({', '.join(matched_skills[:2])}) & aligns with {job.title}"
        elif matched_skills:
            reason = f"Direct skill match: {', '.join(matched_skills[:2])}"
        elif role_score >= 70:
            reason = f"Matches target role ({target_role or job.title})"
        else:
            reason = f"Featured vacancy in {job.category}"

        return final_score, matched_skills, missing_skills, reason
