from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.models.course import CourseLevel, CourseStatus


class AttachmentItem(BaseModel):
    """File attachment within a lesson."""
    name: str
    size: Optional[str] = None
    url: Optional[str] = None


class LessonSchema(BaseModel):
    """Serialized representation of a lesson."""
    id: int
    course_id: int
    module_id: Optional[int] = None
    title: str
    content_type: str = "video"
    video_url: Optional[str] = None
    study_material_url: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    duration_minutes: int = 30
    order_index: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CourseModuleSchema(BaseModel):
    """Serialized representation of a curriculum module."""
    id: int
    course_id: int
    title: str
    order_index: int = 0
    lessons: List[LessonSchema] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CourseCreateRequest(BaseModel):
    """Request payload to create a new course (SKL-53)."""
    title: str = Field(min_length=3, max_length=200, description="Title of the course")
    description: str = Field(min_length=10, description="Detailed syllabus or course summary")
    category: str = Field(min_length=2, max_length=100, description="Course domain category (e.g., Programming, Web Development)")
    level: CourseLevel = Field(default=CourseLevel.BEGINNER, description="Target skill level")
    price: float = Field(default=0.0, ge=0.0, description="Course price (BDT)")
    is_free: bool = Field(default=True, description="Whether the course is free of charge")
    duration_weeks: int = Field(default=8, ge=1, le=52, description="Estimated duration in weeks")
    thumbnail_url: Optional[str] = Field(default=None, max_length=255)
    status: CourseStatus = Field(default=CourseStatus.DRAFT, description="Initial publication status")

    model_config = ConfigDict(extra="ignore")


class CourseUpdateRequest(BaseModel):
    """Request payload to update an existing course (SKL-53)."""
    title: Optional[str] = Field(default=None, min_length=3, max_length=200)
    description: Optional[str] = Field(default=None, min_length=10)
    category: Optional[str] = Field(default=None, min_length=2, max_length=100)
    level: Optional[CourseLevel] = None
    price: Optional[float] = Field(default=None, ge=0.0)
    is_free: Optional[bool] = None
    duration_weeks: Optional[int] = Field(default=None, ge=1, le=52)
    thumbnail_url: Optional[str] = None
    status: Optional[CourseStatus] = None

    model_config = ConfigDict(extra="ignore")


class CourseStatusUpdateRequest(BaseModel):
    """Request payload for publishing or admin moderation unpublishing (SKL-53)."""
    status: CourseStatus
    reason: Optional[str] = Field(default=None, max_length=500, description="Optional administrative moderation note")


class CourseResponse(BaseModel):
    """Card and catalog summary representation of a course (Courses.png)."""
    id: int
    instructor_id: int
    instructor_name: str
    instructor_designation: Optional[str] = None
    title: str
    description: str
    category: str
    level: str
    price: float
    is_free: bool
    status: str
    thumbnail_url: Optional[str] = None
    duration_weeks: int
    lessons_count: int = 0
    modules_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CourseDetailResponse(CourseResponse):
    """Comprehensive course representation with module outline and lesson content (Course Management.png)."""
    modules: List[CourseModuleSchema] = []
    lessons: List[LessonSchema] = []


class CurriculumLessonInput(BaseModel):
    """Input payload for a lesson in curriculum batch sync."""
    id: Optional[int] = None
    title: str = Field(min_length=1, max_length=200)
    content_type: str = "video"
    video_url: Optional[str] = None
    study_material_url: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    duration_minutes: int = Field(default=30, ge=1)
    order_index: int = 0


class CurriculumModuleInput(BaseModel):
    """Input payload for a module in curriculum batch sync."""
    id: Optional[int] = None
    title: str = Field(min_length=1, max_length=200)
    order_index: int = 0
    lessons: List[CurriculumLessonInput] = []


class CurriculumSyncRequest(BaseModel):
    """Request payload for synchronizing the full curriculum outline (SKL-53)."""
    modules: List[CurriculumModuleInput] = []


class PaginatedCourseResponse(BaseModel):
    """Paginated collection of course cards."""
    items: List[CourseResponse]
    total: int
    page: int
    size: int
    total_pages: int
