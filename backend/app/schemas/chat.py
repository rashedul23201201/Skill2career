from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class ChatParticipantResponse(BaseModel):
    """Schema representing chat conversation counterpart identity."""
    id: int
    name: str
    email: str
    role: str
    institution: Optional[str] = None
    designation: Optional[str] = None
    expertise_domain: Optional[str] = None
    avatar_url: Optional[str] = None
    is_online: bool = False

    model_config = ConfigDict(from_attributes=True)


class ChatMessageResponse(BaseModel):
    """Schema for individual chat message."""
    id: int
    conversation_id: int
    sender_id: int
    sender_name: str
    sender_role: str
    message_text: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatConversationResponse(BaseModel):
    """Schema representing an active conversation between learner and instructor."""
    id: int
    learner_id: int
    instructor_id: int
    participant: ChatParticipantResponse
    last_message: Optional[ChatMessageResponse] = None
    unread_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatCreateConversationRequest(BaseModel):
    """Request payload to initiate or access a conversation with an instructor."""
    instructor_id: int = Field(..., gt=0, description="Target instructor user ID")
    initial_message: Optional[str] = Field(
        default=None, max_length=5000, description="Optional opening message to send immediately"
    )

    model_config = ConfigDict(extra="ignore")


class ChatSendMessageRequest(BaseModel):
    """Request payload to send a message via REST."""
    message_text: str = Field(
        ..., min_length=1, max_length=5000, description="Message text content"
    )

    model_config = ConfigDict(extra="ignore")


class ChatMarkReadResponse(BaseModel):
    """Response returned upon marking conversation messages as read."""
    conversation_id: int
    marked_count: int

    model_config = ConfigDict(from_attributes=True)


class InstructorDirectoryItemResponse(BaseModel):
    """Catalog item for learners discovering instructors available for chat guidance."""
    id: int
    name: str
    email: str
    designation: Optional[str] = None
    institution: Optional[str] = None
    expertise_domain: Optional[str] = None
    years_experience: Optional[str] = None
    has_existing_conversation: bool = False
    existing_conversation_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
