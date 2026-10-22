"""Pydantic schemas for Learner & Instructor Role Dashboards (SKL-59).

Fulfills Sprint 4 Acceptance Criteria:
- AC-1: Learner-specific information (enrolled courses, progress, test scores, job applications).
- AC-2: Instructor-specific information (active courses, total learners, mock tests, upcoming interviews).
- AC-3: Exact summary math across courses, attempts, and recruitment pipelines.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ==============================================================================
# Learner Dashboard Schemas (SKL-59)
# ==============================================================================

class LearnerDashboardMetrics(BaseModel):
    """4 key telemetry counters matching Learners dashboard.png."""
    enrolled_courses: int = Field(default=0, description="Count of courses learner is enrolled in")
    course_progress: float = Field(default=0.0, description="Average progress percentage across active courses")
    mock_test_score: float = Field(default=0.0, description="Latest or average mock test score percentage")
    applications_count: int = Field(default=0, description="Total job applications submitted")
    unread_notifications: int = Field(default=0, description="Unread notification items")


class LearnerActiveCurriculum(BaseModel):
    """Primary active learning track matching Learners dashboard.png."""
    course_id: int
    title: str
    description: Optional[str] = None
    completed_lessons: int = 0
    total_lessons: int = 0
    progress_percentage: float = 0.0
    estimated_hours_remaining: int = 4
    thumbnail_url: Optional[str] = None


class LearnerEnrolledCourseSummary(BaseModel):
    """Snippet of each enrolled course for learner dashboard."""
    course_id: int
    title: str
    category: Optional[str] = None
    progress_percentage: float = 0.0
    status: str = "ACTIVE"
    completed_lessons: int = 0
    total_lessons: int = 0


class LearnerInterviewSummary(BaseModel):
    """Upcoming candidate interview schedule item."""
    id: int
    job_id: Optional[int] = None
    job_title: str = "Junior Software Developer"
    company_name: str = "Brain Station 23"
    interview_type: str = "Technical Interview"
    scheduled_at: Optional[datetime] = None
    meeting_platform: Optional[str] = "Google Meet"
    meeting_link: Optional[str] = None


class LearnerMockTestSummary(BaseModel):
    """Most recent mock test result card."""
    id: int
    test_id: int
    test_title: str
    score: float
    total_marks: float
    percentage: float
    is_passed: bool
    evaluated_at: Optional[datetime] = None


class LearnerApplicationSummary(BaseModel):
    """Most recent job application pipeline card."""
    id: int
    job_id: int
    job_title: str
    company_name: str
    status: str
    applied_at: Optional[datetime] = None


class LearnerCareerProfileSummary(BaseModel):
    """Candidate profile badge and career summary."""
    first_name: str
    last_name: str
    email: str
    institution: Optional[str] = "CSE @ UAP"
    department: Optional[str] = "B.Sc. in Computer Science & Engineering"
    target_role: Optional[str] = "Junior Software Developer"
    experience: Optional[str] = "1 year"
    skills: List[str] = Field(default_factory=list)
    completion_pct: int = 85
    profile_photo_url: Optional[str] = None


class LearnerActivityItem(BaseModel):
    """Recent learner activity notification or submission item."""
    id: Optional[str] = None
    activity_type: str
    title: str
    description: str
    timestamp: Optional[datetime] = None


class LearnerDashboardSummaryResponse(BaseModel):
    """Consolidated payload for GET /api/v1/learners/dashboard-summary."""
    metrics: LearnerDashboardMetrics
    active_curriculum: Optional[LearnerActiveCurriculum] = None
    enrolled_courses: List[LearnerEnrolledCourseSummary] = Field(default_factory=list)
    latest_interview: Optional[LearnerInterviewSummary] = None
    latest_mock_test: Optional[LearnerMockTestSummary] = None
    latest_application: Optional[LearnerApplicationSummary] = None
    career_profile: LearnerCareerProfileSummary
    recent_activities: List[LearnerActivityItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Instructor Dashboard Schemas (SKL-59)
# ==============================================================================

class InstructorDashboardMetrics(BaseModel):
    """4 key telemetry counters matching Instructors dashboard.png."""
    active_courses: int = Field(default=0, description="Published course count created by instructor")
    total_learners: int = Field(default=0, description="Total unique students enrolled in instructor's courses")
    mock_tests: int = Field(default=0, description="Question banks authored by instructor")
    upcoming_interviews: int = Field(default=0, description="Scheduled candidate interview sessions")
    unread_inquiries: int = Field(default=0, description="Unread chat messages from students")


class InstructorCourseItem(BaseModel):
    """Authored course card in My Courses widget."""
    id: int
    title: str
    category: Optional[str] = None
    status: str = "PUBLISHED"
    enrolled_learners: int = 0
    average_progress: float = 0.0
    lessons_count: int = 0
    duration_weeks: Optional[int] = 8


class InstructorLearnerPerformance(BaseModel):
    """Cohort progress and test score distribution."""
    average_course_progress: float = 0.0
    average_test_score: float = 0.0
    completed_courses_learners: int = 0
    cohort_label: str = "Batch 2026"


class InstructorInterviewSummary(BaseModel):
    """Upcoming mock or candidate interview widget."""
    id: int
    topic_or_role: str = "Backend Development"
    candidate_name: str = "Candidate"
    candidate_avatar: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    meeting_platform: Optional[str] = "Google Meet"
    meeting_link: Optional[str] = None
    interview_type: str = "Mock Interview"


class InstructorActivityItem(BaseModel):
    """Real-time instructor event feed (enrollments, test submissions)."""
    id: Optional[str] = None
    event_type: str
    title: str
    description: str
    timestamp: Optional[datetime] = None


class InstructorProfileSummary(BaseModel):
    """Instructor header credentials badge."""
    first_name: str
    last_name: str
    email: str
    designation: Optional[str] = "CSE Instructor"
    institution: Optional[str] = "Independent Educator"
    specialization: Optional[str] = "Software Engineering"
    published_courses: int = 0
    onboarding_status: str = "PENDING_REVIEW"
    profile_completion_pct: int = 90
    profile_photo_url: Optional[str] = None


class InstructorDashboardSummaryResponse(BaseModel):
    """Consolidated payload for GET /api/v1/instructors/dashboard-summary."""
    metrics: InstructorDashboardMetrics
    my_courses: List[InstructorCourseItem] = Field(default_factory=list)
    learner_performance: InstructorLearnerPerformance
    upcoming_interview: Optional[InstructorInterviewSummary] = None
    recent_activities: List[InstructorActivityItem] = Field(default_factory=list)
    profile: InstructorProfileSummary

    model_config = ConfigDict(from_attributes=True)
