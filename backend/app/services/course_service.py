import logging
import math
import mimetypes
import os
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    BadRequestException,
)
from app.models.user import User, UserRole
from app.models.course import Course, CourseModule, Lesson, CourseStatus, CourseLevel
from app.repositories.course_repository import CourseRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.course import (
    CourseCreateRequest,
    CourseUpdateRequest,
    CourseResponse,
    CourseDetailResponse,
    CourseModuleSchema,
    LessonSchema,
    CurriculumSyncRequest,
    PaginatedCourseResponse,
    LessonCreateRequest,
    LessonUpdateRequest,
    StudyMaterialUploadResponse,
    CourseModuleCreateRequest,
    CourseModuleUpdateRequest,
)

logger = logging.getLogger(__name__)


class CourseService:
    """Service handling LMS course authoring, discovery, curriculum hierarchies, and administration (SKL-53)."""

    def __init__(
        self,
        course_repo: CourseRepository = CourseRepository(),
        audit_repo: AuditLogRepository = AuditLogRepository(),
    ):
        self.course_repo = course_repo
        self.audit_repo = audit_repo

    def _to_course_response(self, course: Course) -> CourseResponse:
        """Helper to transform Course ORM into standard CourseResponse."""
        instructor_name = "Instructor"
        instructor_designation = "Course Instructor"
        if course.instructor:
            instructor_name = f"{course.instructor.first_name} {course.instructor.last_name}".strip()
            if hasattr(course.instructor, "instructor_profile") and course.instructor.instructor_profile:
                instructor_designation = course.instructor.instructor_profile.designation or course.instructor.instructor_profile.qualification or "Instructor"

        lessons_count = len(course.lessons) if course.lessons else 0
        modules_count = len(course.modules) if course.modules else 0

        return CourseResponse(
            id=course.id,
            instructor_id=course.instructor_id,
            instructor_name=instructor_name,
            instructor_designation=instructor_designation,
            title=course.title,
            description=course.description,
            category=course.category,
            level=course.level,
            price=course.price,
            is_free=course.is_free,
            status=course.status,
            thumbnail_url=course.thumbnail_url,
            duration_weeks=course.duration_weeks,
            lessons_count=lessons_count,
            modules_count=modules_count,
            created_at=course.created_at,
            updated_at=course.updated_at,
        )

    def _to_course_detail_response(self, course: Course) -> CourseDetailResponse:
        """Helper to transform Course ORM into CourseDetailResponse with full curriculum tree."""
        base_res = self._to_course_response(course)
        
        # Serialize modules and nested lessons
        modules_list: List[CourseModuleSchema] = []
        for mod in (course.modules or []):
            mod_lessons = [
                LessonSchema.model_validate(les) for les in (mod.lessons or [])
            ]
            modules_list.append(
                CourseModuleSchema(
                    id=mod.id,
                    course_id=mod.course_id,
                    title=mod.title,
                    order_index=mod.order_index,
                    lessons=mod_lessons,
                    created_at=mod.created_at,
                    updated_at=mod.updated_at,
                )
            )

        all_lessons = [
            LessonSchema.model_validate(les) for les in (course.lessons or [])
        ]

        return CourseDetailResponse(
            **base_res.model_dump(),
            modules=modules_list,
            lessons=all_lessons,
        )

    def create_course(self, db: Session, current_user: User, request: CourseCreateRequest) -> CourseDetailResponse:
        """Author a new course with instructor ownership (SKL-53 AC-1)."""
        if current_user.role not in [UserRole.INSTRUCTOR, UserRole.ADMIN]:
            raise ForbiddenException(
                message="Only approved instructors or administrators can create courses",
                error_code="INSUFFICIENT_COURSE_PERMISSIONS",
            )

        new_course = Course(
            instructor_id=current_user.id,
            title=request.title.strip(),
            description=request.description.strip(),
            category=request.category.strip(),
            level=request.level.value if hasattr(request.level, "value") else request.level,
            price=request.price,
            is_free=request.is_free,
            status=request.status.value if hasattr(request.status, "value") else request.status,
            thumbnail_url=request.thumbnail_url,
            duration_weeks=request.duration_weeks,
        )
        created = self.course_repo.create(db, new_course)

        # Create initial default module and lesson for immediate curriculum building experience
        default_module = self.course_repo.add_module(
            db, course_id=created.id, title="Module 1: Getting Started", order_index=0
        )
        self.course_repo.add_lesson(
            db,
            course_id=created.id,
            module_id=default_module.id,
            title="Introduction to Course",
            content_type="video",
            duration_minutes=15,
            order_index=0,
        )

        db.refresh(created)
        logger.info("User ID %d created new course ID %d: '%s'", current_user.id, created.id, created.title)
        return self._to_course_detail_response(created)

    def get_course_by_id(self, db: Session, course_id: int, current_user: Optional[User] = None) -> CourseDetailResponse:
        """Fetch course details with syllabus and security checks for drafts (SKL-53)."""
        course = self.course_repo.get_by_id(db, course_id)
        if not course:
            raise NotFoundException(
                message=f"Course with ID {course_id} was not found",
                error_code="COURSE_NOT_FOUND",
            )

        # If not published, only the authoring instructor or platform admin can view it
        if course.status != CourseStatus.PUBLISHED.value:
            if not current_user or (
                current_user.id != course.instructor_id and current_user.role != UserRole.ADMIN
            ):
                raise NotFoundException(
                    message=f"Course with ID {course_id} is currently unavailable or unpublished",
                    error_code="COURSE_NOT_AVAILABLE",
                )

        return self._to_course_detail_response(course)

    def update_course(
        self, db: Session, course_id: int, current_user: User, request: CourseUpdateRequest
    ) -> CourseDetailResponse:
        """Update existing course metadata (SKL-53 AC-2)."""
        course = self.course_repo.get_by_id(db, course_id)
        if not course:
            raise NotFoundException(
                message=f"Course with ID {course_id} was not found",
                error_code="COURSE_NOT_FOUND",
            )

        # Guard: ownership check
        if course.instructor_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise ForbiddenException(
                message="You do not have permission to modify this course",
                error_code="COURSE_ACCESS_DENIED",
            )

        if request.title is not None:
            course.title = request.title.strip()
        if request.description is not None:
            course.description = request.description.strip()
        if request.category is not None:
            course.category = request.category.strip()
        if request.level is not None:
            course.level = request.level.value if hasattr(request.level, "value") else request.level
        if request.price is not None:
            course.price = request.price
        if request.is_free is not None:
            course.is_free = request.is_free
        if request.duration_weeks is not None:
            course.duration_weeks = request.duration_weeks
        if request.thumbnail_url is not None:
            course.thumbnail_url = request.thumbnail_url
        if request.status is not None:
            course.status = request.status.value if hasattr(request.status, "value") else request.status

        updated = self.course_repo.update(db, course)
        logger.info("Course ID %d updated by User ID %d", course_id, current_user.id)
        return self._to_course_detail_response(updated)

    def delete_course(self, db: Session, course_id: int, current_user: User) -> None:
        """Remove a course and all associated lessons (SKL-53 AC-5)."""
        course = self.course_repo.get_by_id(db, course_id)
        if not course:
            raise NotFoundException(
                message=f"Course with ID {course_id} was not found",
                error_code="COURSE_NOT_FOUND",
            )

        # Guard: ownership check
        if course.instructor_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise ForbiddenException(
                message="You do not have permission to delete this course",
                error_code="COURSE_ACCESS_DENIED",
            )

        self.course_repo.delete(db, course)
        logger.info("Course ID %d deleted by User ID %d", course_id, current_user.id)

    def update_course_status(
        self,
        db: Session,
        course_id: int,
        current_user: User,
        status: CourseStatus,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> CourseDetailResponse:
        """Publish, unpublish, or administratively moderate a course (SKL-53 AC-5)."""
        course = self.course_repo.get_by_id(db, course_id)
        if not course:
            raise NotFoundException(
                message=f"Course with ID {course_id} was not found",
                error_code="COURSE_NOT_FOUND",
            )

        new_status_str = status.value if hasattr(status, "value") else status
        previous_status = course.status

        # Permission logic
        if current_user.role == UserRole.ADMIN:
            # Admin oversight: unpublish / moderate policy-violating course
            course = self.course_repo.update_status(db, course, new_status_str)
            self.audit_repo.create(
                db=db,
                admin_id=current_user.id,
                target_user_id=course.instructor_id,
                action="COURSE_STATUS_OVERRIDE",
                details={
                    "course_id": course.id,
                    "course_title": course.title,
                    "previous_status": previous_status,
                    "new_status": new_status_str,
                    "reason": reason or "Administrative content moderation",
                },
                ip_address=ip_address,
            )
            logger.info("Admin ID %d updated Course ID %d status to %s", current_user.id, course_id, new_status_str)
        elif current_user.role == UserRole.INSTRUCTOR:
            if course.instructor_id != current_user.id:
                raise ForbiddenException(
                    message="You do not have permission to modify the status of this course",
                    error_code="COURSE_ACCESS_DENIED",
                )
            course = self.course_repo.update_status(db, course, new_status_str)
            logger.info("Instructor ID %d updated Course ID %d status to %s", current_user.id, course_id, new_status_str)
        else:
            raise ForbiddenException(
                message="You do not have permission to alter course lifecycle status",
                error_code="INSUFFICIENT_COURSE_PERMISSIONS",
            )

        return self._to_course_detail_response(course)

    def list_courses_paginated(
        self,
        db: Session,
        page: int = 1,
        size: int = 12,
        category: Optional[str] = None,
        level: Optional[str] = None,
        search: Optional[str] = None,
        my_courses: bool = False,
        status: Optional[str] = None,
        current_user: Optional[User] = None,
    ) -> PaginatedCourseResponse:
        """Retrieve paginated courses for public catalog, instructor portal, or admin governance (Courses.png)."""
        page = max(1, page)
        size = min(100, max(1, size))

        query_instructor_id: Optional[int] = None
        query_status: Optional[str] = None

        if my_courses:
            if not current_user:
                raise ForbiddenException(
                    message="Authentication required to view authored courses",
                    error_code="AUTHENTICATION_REQUIRED",
                )
            query_instructor_id = current_user.id
            query_status = status  # May be None to see all statuses of their own courses
        elif current_user and current_user.role == UserRole.ADMIN:
            query_status = status  # Admin can filter by status or see all
        else:
            # Public catalog: only PUBLISHED courses are visible
            query_status = CourseStatus.PUBLISHED.value

        courses, total = self.course_repo.get_courses_paginated(
            db=db,
            page=page,
            size=size,
            category=category,
            level=level,
            status=query_status,
            search=search,
            instructor_id=query_instructor_id,
        )

        total_pages = math.ceil(total / size) if size > 0 else 0

        return PaginatedCourseResponse(
            items=[self._to_course_response(c) for c in courses],
            total=total,
            page=page,
            size=size,
            total_pages=total_pages,
        )

    def sync_curriculum(
        self, db: Session, course_id: int, current_user: User, request: CurriculumSyncRequest
    ) -> CourseDetailResponse:
        """Batch save and synchronize entire curriculum tree for Curriculum Builder (Course Management.png)."""
        course = self.course_repo.get_by_id(db, course_id)
        if not course:
            raise NotFoundException(
                message=f"Course with ID {course_id} was not found",
                error_code="COURSE_NOT_FOUND",
            )

        if course.instructor_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise ForbiddenException(
                message="You do not have permission to edit this curriculum",
                error_code="COURSE_ACCESS_DENIED",
            )

        modules_data = [m.model_dump() for m in request.modules]
        updated_course = self.course_repo.sync_curriculum(db, course, modules_data)
        return self._to_course_detail_response(updated_course)

    def create_lesson(
        self, db: Session, course_id: int, current_user: User, request: LessonCreateRequest
    ) -> LessonSchema:
        """Add a new lesson and study material to a course (SKL-55 AC-1)."""
        course = self.course_repo.get_by_id(db, course_id)
        if not course:
            raise NotFoundException(
                message=f"Course with ID {course_id} was not found",
                error_code="COURSE_NOT_FOUND",
            )

        if course.instructor_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise ForbiddenException(
                message="You do not have permission to add lessons to this course",
                error_code="LESSON_ACCESS_DENIED",
            )

        if request.module_id is not None:
            module = self.course_repo.get_module_by_id(db, request.module_id)
            if not module or module.course_id != course_id:
                raise BadRequestException(
                    message="The specified module does not belong to this course",
                    error_code="INVALID_MODULE",
                )

        if not request.title or not request.title.strip():
            raise BadRequestException(
                message="Lesson title cannot be empty",
                error_code="INVALID_LESSON_TITLE",
            )

        order_idx = request.order_index
        if order_idx == 0:
            existing = self.course_repo.get_lessons_by_course(db, course_id)
            order_idx = len(existing)

        new_lesson = Lesson(
            course_id=course.id,
            module_id=request.module_id,
            title=request.title.strip(),
            content_type=request.content_type or "video",
            video_url=request.video_url.strip() if request.video_url else None,
            study_material_url=request.study_material_url.strip() if request.study_material_url else None,
            attachments=request.attachments or [],
            duration_minutes=request.duration_minutes,
            order_index=order_idx,
        )
        db.add(new_lesson)
        db.commit()
        db.refresh(new_lesson)

        logger.info("Lesson created successfully: ID %d in course %d", new_lesson.id, course_id)
        return LessonSchema.model_validate(new_lesson)

    def get_lessons_for_course(
        self, db: Session, course_id: int, current_user: Optional[User] = None
    ) -> List[LessonSchema]:
        """Fetch all lessons for an available course (SKL-55 AC-3)."""
        course = self.course_repo.get_by_id(db, course_id)
        if not course:
            raise NotFoundException(
                message=f"Course with ID {course_id} was not found",
                error_code="COURSE_NOT_FOUND",
            )

        if course.status != CourseStatus.PUBLISHED.value:
            if not current_user or (
                current_user.id != course.instructor_id and current_user.role != UserRole.ADMIN
            ):
                raise NotFoundException(
                    message=f"Course with ID {course_id} is currently unavailable or unpublished",
                    error_code="COURSE_NOT_AVAILABLE",
                )

        lessons = self.course_repo.get_lessons_by_course(db, course_id)
        return [LessonSchema.model_validate(les) for les in lessons]

    def get_lesson_by_id(
        self, db: Session, lesson_id: int, current_user: Optional[User] = None
    ) -> LessonSchema:
        """Fetch a single lesson by ID with security checks (SKL-55 AC-3)."""
        lesson = self.course_repo.get_lesson_by_id(db, lesson_id)
        if not lesson:
            raise NotFoundException(
                message=f"Lesson with ID {lesson_id} was not found",
                error_code="LESSON_NOT_FOUND",
            )

        if lesson.course.status != CourseStatus.PUBLISHED.value:
            if not current_user or (
                current_user.id != lesson.course.instructor_id and current_user.role != UserRole.ADMIN
            ):
                raise NotFoundException(
                    message=f"Lesson with ID {lesson_id} is currently unavailable",
                    error_code="LESSON_NOT_AVAILABLE",
                )

        return LessonSchema.model_validate(lesson)

    def update_lesson(
        self, db: Session, lesson_id: int, current_user: User, request: LessonUpdateRequest
    ) -> LessonSchema:
        """Update an existing lesson's details and materials (SKL-55 AC-2)."""
        lesson = self.course_repo.get_lesson_by_id(db, lesson_id)
        if not lesson:
            raise NotFoundException(
                message=f"Lesson with ID {lesson_id} was not found",
                error_code="LESSON_NOT_FOUND",
            )

        if lesson.course.instructor_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise ForbiddenException(
                message="You do not have permission to modify this lesson",
                error_code="LESSON_ACCESS_DENIED",
            )

        if request.module_id is not None:
            if request.module_id > 0:
                module = self.course_repo.get_module_by_id(db, request.module_id)
                if not module or module.course_id != lesson.course_id:
                    raise BadRequestException(
                        message="The specified module does not belong to this course",
                        error_code="INVALID_MODULE",
                    )
                lesson.module_id = request.module_id
            else:
                lesson.module_id = None

        if request.title is not None:
            if not request.title.strip():
                raise BadRequestException(
                    message="Lesson title cannot be empty",
                    error_code="INVALID_LESSON_TITLE",
                )
            lesson.title = request.title.strip()

        if request.content_type is not None:
            lesson.content_type = request.content_type

        if request.video_url is not None:
            lesson.video_url = request.video_url.strip() if request.video_url else None

        if request.study_material_url is not None:
            lesson.study_material_url = request.study_material_url.strip() if request.study_material_url else None

        if request.attachments is not None:
            lesson.attachments = request.attachments

        if request.duration_minutes is not None:
            lesson.duration_minutes = request.duration_minutes

        if request.order_index is not None:
            lesson.order_index = request.order_index

        updated = self.course_repo.update_lesson(db, lesson)
        logger.info("Lesson %d updated successfully by user %d", lesson_id, current_user.id)
        return LessonSchema.model_validate(updated)

    def delete_lesson(self, db: Session, lesson_id: int, current_user: User) -> dict:
        """Delete a lesson (SKL-55 AC-5)."""
        lesson = self.course_repo.get_lesson_by_id(db, lesson_id)
        if not lesson:
            raise NotFoundException(
                message=f"Lesson with ID {lesson_id} was not found",
                error_code="LESSON_NOT_FOUND",
            )

        if lesson.course.instructor_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise ForbiddenException(
                message="You do not have permission to delete this lesson",
                error_code="LESSON_ACCESS_DENIED",
            )

        self.course_repo.delete_lesson(db, lesson)
        logger.info("Lesson %d deleted by user %d", lesson_id, current_user.id)
        return {"lesson_id": lesson_id, "deleted": True}

    def upload_lesson_material(
        self, db: Session, lesson_id: int, current_user: User, file: UploadFile
    ) -> StudyMaterialUploadResponse:
        """Upload and associate study material document with a lesson (SKL-55 AC-2)."""
        lesson = self.course_repo.get_lesson_by_id(db, lesson_id)
        if not lesson:
            raise NotFoundException(
                message=f"Lesson with ID {lesson_id} was not found",
                error_code="LESSON_NOT_FOUND",
            )

        if lesson.course.instructor_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise ForbiddenException(
                message="You do not have permission to upload materials to this lesson",
                error_code="LESSON_ACCESS_DENIED",
            )

        filename = file.filename or "study_material.pdf"
        file_ext = Path(filename).suffix.lower()

        allowed_extensions = {
            ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".txt", ".zip", ".rar", ".png", ".jpg", ".jpeg"
        }
        if file_ext not in allowed_extensions:
            raise BadRequestException(
                message=f"Unsupported file format '{file_ext}'. Allowed formats: PDF, DOCX, PPTX, TXT, ZIP, PNG, JPG.",
                error_code="UNSUPPORTED_MATERIAL_FORMAT",
            )

        try:
            contents = file.file.read()
        except Exception as e:
            logger.error("Failed to read uploaded file: %s", e)
            raise BadRequestException(message="Failed to read uploaded file.", error_code="FILE_READ_ERROR")

        file_size = len(contents)
        if file_size == 0:
            raise BadRequestException(message="Uploaded file is empty (0 bytes).", error_code="EMPTY_FILE")

        max_size = 25 * 1024 * 1024
        if file_size > max_size:
            raise BadRequestException(
                message="File size exceeds maximum allowable limit of 25MB.",
                error_code="FILE_TOO_LARGE",
            )

        upload_dir = Path("uploads/materials") / f"course_{lesson.course_id}" / f"lesson_{lesson.id}"
        upload_dir.mkdir(parents=True, exist_ok=True)

        clean_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", filename)
        target_path = upload_dir / clean_name
        with open(target_path, "wb") as f:
            f.write(contents)

        if file_size >= 1024 * 1024:
            size_label = f"{file_size / (1024 * 1024):.1f} MB"
        else:
            size_label = f"{max(1, math.ceil(file_size / 1024))} KB"

        download_url = f"/api/v1/lessons/{lesson.id}/materials/{clean_name}/download"

        existing_attachments = list(lesson.attachments or [])
        # Avoid duplicate attachment entries with same name
        existing_attachments = [a for a in existing_attachments if a.get("name") != filename and a.get("filename") != clean_name]
        existing_attachments.append({
            "name": filename,
            "filename": clean_name,
            "size": size_label,
            "url": download_url,
            "type": file_ext.lstrip("."),
        })
        lesson.attachments = existing_attachments
        if not lesson.study_material_url:
            lesson.study_material_url = download_url

        self.course_repo.update_lesson(db, lesson)
        logger.info("Material '%s' (%s) attached to lesson %d", clean_name, size_label, lesson.id)

        mime_type, _ = mimetypes.guess_type(str(target_path))
        return StudyMaterialUploadResponse(
            filename=clean_name,
            file_url=download_url,
            name=filename,
            size=size_label,
            content_type=mime_type or "application/octet-stream",
            message="Study material uploaded and attached successfully",
        )

    def download_lesson_material(
        self, db: Session, lesson_id: int, filename: str, current_user: Optional[User] = None
    ) -> FileResponse:
        """Download or stream study material for an enrolled/available lesson (SKL-55 AC-3)."""
        lesson = self.course_repo.get_lesson_by_id(db, lesson_id)
        if not lesson:
            raise NotFoundException(
                message=f"Lesson with ID {lesson_id} was not found",
                error_code="LESSON_NOT_FOUND",
            )

        if lesson.course.status != CourseStatus.PUBLISHED.value:
            if not current_user or (
                current_user.id != lesson.course.instructor_id and current_user.role != UserRole.ADMIN
            ):
                raise NotFoundException(
                    message="Material is unavailable or course is unpublished",
                    error_code="MATERIAL_NOT_AVAILABLE",
                )

        target_file = Path("uploads/materials") / f"course_{lesson.course_id}" / f"lesson_{lesson.id}" / filename
        if not target_file.exists():
            raise NotFoundException(
                message=f"Material file '{filename}' was not found",
                error_code="FILE_NOT_FOUND",
            )

        mime_type, _ = mimetypes.guess_type(str(target_file))
        return FileResponse(
            path=str(target_file),
            filename=filename,
            media_type=mime_type or "application/octet-stream",
        )

    def delete_lesson_material(
        self, db: Session, lesson_id: int, filename: str, current_user: User
    ) -> LessonSchema:
        """Remove a study material attachment from a lesson."""
        lesson = self.course_repo.get_lesson_by_id(db, lesson_id)
        if not lesson:
            raise NotFoundException(
                message=f"Lesson with ID {lesson_id} was not found",
                error_code="LESSON_NOT_FOUND",
            )

        if lesson.course.instructor_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise ForbiddenException(
                message="You do not have permission to delete materials from this lesson",
                error_code="LESSON_ACCESS_DENIED",
            )

        existing = list(lesson.attachments or [])
        lesson.attachments = [a for a in existing if a.get("name") != filename and a.get("filename") != filename]

        target_file = Path("uploads/materials") / f"course_{lesson.course_id}" / f"lesson_{lesson.id}" / filename
        if target_file.exists():
            try:
                target_file.unlink()
            except Exception as e:
                logger.warning("Could not delete file %s: %s", target_file, e)

        updated = self.course_repo.update_lesson(db, lesson)
        return LessonSchema.model_validate(updated)

    def create_module(
        self, db: Session, course_id: int, current_user: User, request: CourseModuleCreateRequest
    ) -> CourseModuleSchema:
        """Create a new module within a course."""
        course = self.course_repo.get_by_id(db, course_id)
        if not course:
            raise NotFoundException(
                message=f"Course with ID {course_id} was not found",
                error_code="COURSE_NOT_FOUND",
            )

        if course.instructor_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise ForbiddenException(
                message="You do not have permission to modify this course",
                error_code="COURSE_ACCESS_DENIED",
            )

        module = self.course_repo.add_module(
            db, course_id=course_id, title=request.title.strip(), order_index=request.order_index
        )
        return CourseModuleSchema.model_validate(module)

    def update_module(
        self, db: Session, module_id: int, current_user: User, request: CourseModuleUpdateRequest
    ) -> CourseModuleSchema:
        """Update an existing module's title or order."""
        module = self.course_repo.get_module_by_id(db, module_id)
        if not module:
            raise NotFoundException(
                message=f"Module with ID {module_id} was not found",
                error_code="MODULE_NOT_FOUND",
            )

        course = self.course_repo.get_by_id(db, module.course_id)
        if course.instructor_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise ForbiddenException(
                message="You do not have permission to modify this module",
                error_code="COURSE_ACCESS_DENIED",
            )

        if request.title is not None:
            module.title = request.title.strip()
        if request.order_index is not None:
            module.order_index = request.order_index

        updated = self.course_repo.update_module(db, module)
        return CourseModuleSchema.model_validate(updated)

    def delete_module(self, db: Session, module_id: int, current_user: User) -> dict:
        """Delete a curriculum module."""
        module = self.course_repo.get_module_by_id(db, module_id)
        if not module:
            raise NotFoundException(
                message=f"Module with ID {module_id} was not found",
                error_code="MODULE_NOT_FOUND",
            )

        course = self.course_repo.get_by_id(db, module.course_id)
        if course.instructor_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise ForbiddenException(
                message="You do not have permission to delete this module",
                error_code="COURSE_ACCESS_DENIED",
            )

        self.course_repo.delete_module(db, module)
        return {"module_id": module_id, "deleted": True}
