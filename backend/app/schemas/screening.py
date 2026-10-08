from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.models.screening import QuestionType, DealBreakerRule, CandidateStatus


def _coerce_enum(enum_cls: Any, val: Any) -> Any:
    if val is None or isinstance(val, enum_cls):
        return val
    val_str = str(val).strip().replace("-", "_").upper()
    for member in enum_cls:
        if member.value.upper() == val_str or member.name.upper() == val_str:
            return member
    return val


class ScreeningQuestionCreateRequest(BaseModel):
    question_text: str = Field(min_length=3, max_length=500)
    question_type: QuestionType = Field(default=QuestionType.TEXT)
    options: Optional[List[str]] = None
    expected_answer: Optional[str] = None
    is_required: bool = True
    is_deal_breaker: bool = False
    deal_breaker_rule: Optional[DealBreakerRule] = None
    deal_breaker_value: Optional[str] = None
    deal_breaker_label: Optional[str] = None
    weight: int = Field(default=10, ge=1, le=100)
    order_index: int = 0

    model_config = ConfigDict(extra="ignore")

    @field_validator("question_type", mode="before")
    @classmethod
    def validate_question_type(cls, v: Any) -> Any:
        return _coerce_enum(QuestionType, v)

    @field_validator("deal_breaker_rule", mode="before")
    @classmethod
    def validate_deal_breaker_rule(cls, v: Any) -> Any:
        return _coerce_enum(DealBreakerRule, v)


class ScreeningQuestionUpdateRequest(BaseModel):
    question_text: Optional[str] = Field(default=None, min_length=3, max_length=500)
    question_type: Optional[QuestionType] = None
    options: Optional[List[str]] = None
    expected_answer: Optional[str] = None
    is_required: Optional[bool] = None
    is_deal_breaker: Optional[bool] = None
    deal_breaker_rule: Optional[DealBreakerRule] = None
    deal_breaker_value: Optional[str] = None
    deal_breaker_label: Optional[str] = None
    weight: Optional[int] = Field(default=None, ge=1, le=100)
    order_index: Optional[int] = None

    model_config = ConfigDict(extra="ignore")

    @field_validator("question_type", mode="before")
    @classmethod
    def validate_question_type(cls, v: Any) -> Any:
        return _coerce_enum(QuestionType, v)

    @field_validator("deal_breaker_rule", mode="before")
    @classmethod
    def validate_deal_breaker_rule(cls, v: Any) -> Any:
        return _coerce_enum(DealBreakerRule, v)


class ScreeningQuestionResponse(BaseModel):
    id: int
    job_id: int
    question_text: str
    question_type: str
    options: Optional[List[str]] = None
    expected_answer: Optional[str] = None
    is_required: bool
    is_deal_breaker: bool
    deal_breaker_rule: Optional[str] = None
    deal_breaker_value: Optional[str] = None
    deal_breaker_label: Optional[str] = None
    weight: int
    order_index: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CandidateEvaluationCreateRequest(BaseModel):
    candidate_name: str = Field(min_length=2, max_length=150)
    candidate_email: str = Field(min_length=5, max_length=150)
    candidate_avatar_url: Optional[str] = None
    answers: Dict[str, Any] = Field(default_factory=dict)
    resume_url: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class CandidateEvaluationStatusUpdateRequest(BaseModel):
    status: CandidateStatus
    notes: Optional[str] = Field(default=None, max_length=500)

    model_config = ConfigDict(extra="ignore")

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v: Any) -> Any:
        return _coerce_enum(CandidateStatus, v)


class CandidateEvaluationResponse(BaseModel):
    id: int
    job_id: int
    candidate_id: Optional[int] = None
    candidate_name: str
    candidate_email: str
    candidate_avatar_url: Optional[str] = None
    match_score: int
    deal_breaker_passed: bool
    deal_breaker_failed_reason: Optional[str] = None
    status: str
    answers: Optional[Dict[str, Any]] = None
    key_answers_preview: Optional[str] = None
    resume_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedCandidateEvaluationResponse(BaseModel):
    items: List[CandidateEvaluationResponse]
    total: int
    page: int
    size: int
    total_pages: int
    passed_count: int = 0
    disqualified_count: int = 0
    avg_match_score: float = 0.0
