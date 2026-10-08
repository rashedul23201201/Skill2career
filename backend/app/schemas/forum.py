from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.user import UserRole


class ForumCategoryResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None
    order_index: int = 0
    posts_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ForumCategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = None
    order_index: int = 0


class ForumAuthorResponse(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    avatar_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ForumPostCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=255, description="Discussion title")
    category_id: int = Field(..., description="ID of the forum category")
    content: str = Field(..., min_length=10, description="Discussion markdown/text content")


class ForumPostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=255)
    category_id: Optional[int] = None
    content: Optional[str] = Field(None, min_length=10)


class ForumCommentCreate(BaseModel):
    content: str = Field(..., min_length=2, description="Comment response content")
    parent_id: Optional[int] = Field(None, description="Optional parent comment ID for threading")


class ForumCommentUpdate(BaseModel):
    content: str = Field(..., min_length=2, description="Updated comment content")


class ForumCommentResponse(BaseModel):
    id: int
    post_id: int
    author: ForumAuthorResponse
    parent_id: Optional[int] = None
    content: str
    is_instructor_reply: bool = False
    likes_count: int = 0
    is_liked_by_me: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ForumPostResponse(BaseModel):
    id: int
    category_id: int
    category_name: str
    author: ForumAuthorResponse
    title: str
    content: str
    views_count: int = 0
    likes_count: int = 0
    replies_count: int = 0
    has_instructor_reply: bool = False
    instructor_reply_name: Optional[str] = None
    is_pinned: bool = False
    is_locked: bool = False
    is_liked_by_me: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ForumPostDetailResponse(ForumPostResponse):
    comments: List[ForumCommentResponse] = []


class PaginatedForumPostResponse(BaseModel):
    items: List[ForumPostResponse]
    total: int
    page: int
    size: int
    total_pages: int
    category_counts: dict = {}


class ForumLikeToggleResponse(BaseModel):
    is_liked: bool
    likes_count: int


class ForumReportCreate(BaseModel):
    post_id: Optional[int] = None
    comment_id: Optional[int] = None
    reason: str = Field(..., min_length=3, max_length=100)
    details: Optional[str] = Field(None, max_length=1000)


class ForumReportResponse(BaseModel):
    id: int
    reporter: ForumAuthorResponse
    post_id: Optional[int] = None
    comment_id: Optional[int] = None
    reason: str
    details: Optional[str] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ForumReportStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(PENDING|RESOLVED|DISMISSED)$")
