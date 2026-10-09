from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class EnrollmentResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    status: str
    progress_percentage: float
    completed_lessons_count: int
    last_accessed_lesson_id: Optional[int] = None
    enrolled_at: datetime
    completed_at: Optional[datetime] = None
    course_title: Optional[str] = None
    course_thumbnail_url: Optional[str] = None
    instructor_name: Optional[str] = None
    total_lessons: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class EnrollmentStatusResponse(BaseModel):
    is_enrolled: bool
    enrollment: Optional[EnrollmentResponse] = None


class LessonCompletionRequest(BaseModel):
    is_completed: bool = Field(default=True, description="Mark as completed or incomplete")


class LessonProgressResponse(BaseModel):
    lesson_id: int
    course_id: int
    is_completed: bool
    completed_at: Optional[datetime] = None
    course_progress_percentage: float
    completed_lessons_count: int
    total_lessons: int

    model_config = ConfigDict(from_attributes=True)


class CourseProgressResponse(BaseModel):
    course_id: int
    course_title: str
    total_lessons: int
    completed_lessons: int
    remaining_lessons: int
    progress_percentage: float
    completed_lesson_ids: List[int]
    is_enrolled: bool
    last_accessed_lesson_id: Optional[int] = None
    status: str = "ACTIVE"


class EnrolledCourseItem(BaseModel):
    enrollment_id: int
    course_id: int
    title: str
    description: str
    category: str
    level: str
    thumbnail_url: Optional[str] = None
    duration_weeks: int
    instructor_name: Optional[str] = None
    total_lessons: int
    completed_lessons: int
    progress_percentage: float
    status: str
    enrolled_at: datetime
    completed_at: Optional[datetime] = None
    last_accessed_lesson_id: Optional[int] = None


class EnrolledCoursesListResponse(BaseModel):
    items: List[EnrolledCourseItem]
    total: int
    average_progress: float
