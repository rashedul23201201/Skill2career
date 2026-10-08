from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.models.mock_test import MockTestStatus


def _coerce_enum(enum_cls: Any, val: Any) -> Any:
    if val is None or isinstance(val, enum_cls):
        return val
    val_str = str(val).strip().upper()
    for member in enum_cls:
        if member.value == val_str or member.name == val_str:
            return member
    return val


class TestQuestionCreate(BaseModel):
    __test__ = False
    question_text: str = Field(min_length=3, description="Question description or prompt")
    options: List[str] = Field(min_length=2, max_length=6, description="Multiple choice options")
    correct_option: str = Field(min_length=1, max_length=10, description="Correct option key e.g. A, B, C, D")
    marks: int = Field(default=1, ge=1, le=100, description="Score awarded for correct answer")
    explanation: Optional[str] = Field(default=None, description="Detailed explanation of the solution")
    order_index: int = Field(default=0, ge=0, description="Display order index")

    model_config = ConfigDict(extra="ignore")


class TestQuestionUpdate(BaseModel):
    __test__ = False
    question_text: Optional[str] = Field(default=None, min_length=3)
    options: Optional[List[str]] = Field(default=None, min_length=2, max_length=6)
    correct_option: Optional[str] = Field(default=None, min_length=1, max_length=10)
    marks: Optional[int] = Field(default=None, ge=1, le=100)
    explanation: Optional[str] = None
    order_index: Optional[int] = Field(default=None, ge=0)

    model_config = ConfigDict(extra="ignore")


class TestQuestionResponse(BaseModel):
    __test__ = False
    id: int
    test_id: int
    question_text: str
    options: List[str]
    correct_option: Optional[str] = None
    marks: int = 1
    explanation: Optional[str] = None
    order_index: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MockTestCreateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200, description="Mock test title")
    description: Optional[str] = Field(default=None, description="Test overview and topics covered")
    category: str = Field(default="Programming", min_length=2, max_length=100, description="Subject category")
    duration_minutes: int = Field(default=60, ge=1, le=360, description="Time limit in minutes")
    passing_score: int = Field(default=50, ge=1, le=100, description="Passing score percentage (e.g. 50%)")
    status: MockTestStatus = Field(default=MockTestStatus.DRAFT, description="Initial publication status")

    model_config = ConfigDict(extra="ignore")

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v: Any) -> Any:
        return _coerce_enum(MockTestStatus, v)


class MockTestUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = Field(default=None, min_length=2, max_length=100)
    duration_minutes: Optional[int] = Field(default=None, ge=1, le=360)
    passing_score: Optional[int] = Field(default=None, ge=1, le=100)
    status: Optional[MockTestStatus] = None

    model_config = ConfigDict(extra="ignore")

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v: Any) -> Any:
        return _coerce_enum(MockTestStatus, v)


class MockTestStatusUpdateRequest(BaseModel):
    status: MockTestStatus

    model_config = ConfigDict(extra="ignore")

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v: Any) -> Any:
        return _coerce_enum(MockTestStatus, v)


class MockTestResponse(BaseModel):
    id: int
    instructor_id: int
    instructor_name: str
    title: str
    description: Optional[str] = None
    category: str
    duration_minutes: int
    passing_score: int
    total_questions: int = 0
    status: str
    is_published: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MockTestDetailResponse(MockTestResponse):
    questions: List[TestQuestionResponse] = []


class MockTestSyncQuestionsRequest(BaseModel):
    questions: List[TestQuestionCreate] = []

    model_config = ConfigDict(extra="ignore")


class PaginatedMockTestResponse(BaseModel):
    items: List[MockTestResponse]
    total: int
    page: int
    size: int
    total_pages: int


class TestAttemptStartResponse(BaseModel):
    __test__ = False
    id: int
    test_id: int
    learner_id: int
    started_at: datetime
    expires_at: datetime
    duration_minutes: int
    duration_seconds: int
    remaining_seconds: int
    status: str
    answers: Optional[dict] = None
    marked_for_review: Optional[List[int]] = []
    test_title: str
    category: str
    total_questions: int
    passing_score: int
    questions: List[TestQuestionResponse] = []

    model_config = ConfigDict(from_attributes=True)


class TestAttemptSaveAnswersRequest(BaseModel):
    __test__ = False
    answers: dict = Field(default_factory=dict, description="Dictionary mapping question_id str to selected option key")
    marked_for_review: Optional[List[int]] = Field(default_factory=list, description="Question IDs marked for review")

    model_config = ConfigDict(extra="ignore")


class TestAttemptSubmitRequest(BaseModel):
    __test__ = False
    answers: Optional[dict] = Field(default=None, description="Final submitted answers")
    marked_for_review: Optional[List[int]] = Field(default=None, description="Question IDs marked for review")

    model_config = ConfigDict(extra="ignore")


class TestAttemptResponse(BaseModel):
    __test__ = False
    id: int
    test_id: int
    learner_id: int
    started_at: datetime
    submitted_at: Optional[datetime] = None
    status: str
    score: float
    total_marks: int
    percentage: float
    is_passed: bool
    time_taken_seconds: int
    answers: Optional[dict] = None
    marked_for_review: Optional[List[int]] = None
    test_title: Optional[str] = None
    category: Optional[str] = None
    duration_minutes: Optional[int] = None
    passing_score: Optional[int] = None
    total_questions: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

