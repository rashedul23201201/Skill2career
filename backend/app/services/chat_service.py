import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    BadRequestException,
)
from app.models.user import User, UserRole
from app.models.chat import ChatConversation, ChatMessage
from app.repositories.chat_repository import ChatRepository
from app.repositories.user_repository import UserRepository
from app.services.websocket_manager import connection_manager
from app.schemas.chat import (
    ChatParticipantResponse,
    ChatMessageResponse,
    ChatConversationResponse,
    ChatCreateConversationRequest,
    ChatSendMessageRequest,
    ChatMarkReadResponse,
    InstructorDirectoryItemResponse,
)

logger = logging.getLogger("chat.service")


class ChatService:
    """Coordinates business logic, authorization, and duplex messaging for SKL-16."""

    def __init__(self, repo: Optional[ChatRepository] = None):
        self.repo = repo or ChatRepository()

    def _resolve_participant(
        self, conversation: ChatConversation, current_user_id: int
    ) -> Tuple[User, ChatParticipantResponse]:
        """Extract the counterpart in the conversation with profile identity details."""
        if conversation.learner_id == current_user_id:
            participant_user = conversation.instructor
        else:
            participant_user = conversation.learner

        inst_profile = getattr(participant_user, "instructor_profile", None)
        learner_profile = getattr(participant_user, "learner_profile", None)

        designation = None
        institution = None
        expertise_domain = None

        if inst_profile:
            designation = inst_profile.designation
            institution = inst_profile.institution
            expertise_domain = inst_profile.expertise_domain
        elif learner_profile:
            designation = learner_profile.target_role
            institution = learner_profile.institution

        name = f"{participant_user.first_name} {participant_user.last_name}".strip()
        is_online = connection_manager.is_user_online(participant_user.id)

        participant_response = ChatParticipantResponse(
            id=participant_user.id,
            name=name or participant_user.email,
            email=participant_user.email,
            role=participant_user.role.value,
            institution=institution,
            designation=designation,
            expertise_domain=expertise_domain,
            avatar_url=None,
            is_online=is_online,
        )
        return participant_user, participant_response

    def _to_message_response(self, message: ChatMessage) -> ChatMessageResponse:
        """Convert database ChatMessage to API response schema."""
        sender_name = "User"
        sender_role = "LEARNER"
        if message.sender:
            sender_name = f"{message.sender.first_name} {message.sender.last_name}".strip() or message.sender.email
            sender_role = message.sender.role.value

        return ChatMessageResponse(
            id=message.id,
            conversation_id=message.conversation_id,
            sender_id=message.sender_id,
            sender_name=sender_name,
            sender_role=sender_role,
            message_text=message.message_text,
            is_read=message.is_read,
            created_at=message.created_at,
        )

    def _to_conversation_response(
        self, db: Session, conversation: ChatConversation, current_user_id: int
    ) -> ChatConversationResponse:
        """Convert database ChatConversation to full response with participant and unread count."""
        _, participant_resp = self._resolve_participant(conversation, current_user_id)

        last_msg = self.repo.get_last_message(db, conversation.id)
        last_msg_resp = self._to_message_response(last_msg) if last_msg else None

        unread_count = self.repo.get_unread_count(db, conversation.id, current_user_id)

        return ChatConversationResponse(
            id=conversation.id,
            learner_id=conversation.learner_id,
            instructor_id=conversation.instructor_id,
            participant=participant_resp,
            last_message=last_msg_resp,
            unread_count=unread_count,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )

    def list_conversations(
        self, db: Session, current_user: User
    ) -> List[ChatConversationResponse]:
        """Fetch all active conversations for the authenticated user (SKL-16 AC-1)."""
        conversations = self.repo.get_user_conversations(db, current_user.id)
        return [
            self._to_conversation_response(db, conv, current_user.id)
            for conv in conversations
        ]

    def get_conversation_details(
        self, db: Session, current_user: User, conversation_id: int
    ) -> ChatConversationResponse:
        """Retrieve conversation by ID enforcing participant authorization (SKL-16 AC-4, AC-5)."""
        conv = self.repo.get_conversation_by_id(db, conversation_id)
        if not conv:
            raise NotFoundException(f"Conversation #{conversation_id} not found")

        # Authorization guard (AC-5): Only conversation participants or Admins may access
        is_participant = current_user.id in [conv.learner_id, conv.instructor_id]
        if not is_participant and current_user.role != UserRole.ADMIN:
            raise ForbiddenException(
                "You do not have permission to access this conversation",
                error_code="CONVERSATION_ACCESS_DENIED",
            )

        return self._to_conversation_response(db, conv, current_user.id)

    def get_messages(
        self,
        db: Session,
        current_user: User,
        conversation_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ChatMessageResponse]:
        """Fetch message history for a conversation (SKL-16 AC-4, AC-5)."""
        conv = self.repo.get_conversation_by_id(db, conversation_id)
        if not conv:
            raise NotFoundException(f"Conversation #{conversation_id} not found")

        is_participant = current_user.id in [conv.learner_id, conv.instructor_id]
        if not is_participant and current_user.role != UserRole.ADMIN:
            raise ForbiddenException(
                "You do not have permission to view messages in this conversation",
                error_code="CONVERSATION_ACCESS_DENIED",
            )

        messages = self.repo.get_conversation_messages(
            db, conversation_id, limit=limit, offset=offset
        )
        return [self._to_message_response(m) for m in messages]

    async def create_conversation(
        self,
        db: Session,
        current_user: User,
        request: ChatCreateConversationRequest,
    ) -> ChatConversationResponse:
        """Initialize or retrieve a direct conversation between learner and instructor (SKL-16 AC-1, AC-2)."""
        target_instructor = UserRepository.get_by_id(db, request.instructor_id)
        if not target_instructor:
            raise NotFoundException("Instructor user not found")

        if target_instructor.role != UserRole.INSTRUCTOR and current_user.role != UserRole.ADMIN:
            raise BadRequestException("Direct chat conversations can only be established with instructors")

        if target_instructor.id == current_user.id:
            raise BadRequestException("You cannot start a conversation with yourself")

        # Determine learner and instructor positions
        if current_user.role == UserRole.INSTRUCTOR:
            learner_id = target_instructor.id
            instructor_id = current_user.id
        else:
            learner_id = current_user.id
            instructor_id = target_instructor.id

        conv, is_created = self.repo.get_or_create_conversation(
            db, learner_id=learner_id, instructor_id=instructor_id
        )

        # If opening message provided, persist and dispatch immediately
        if request.initial_message and request.initial_message.strip():
            await self.send_message(
                db=db,
                current_user=current_user,
                conversation_id=conv.id,
                message_text=request.initial_message.strip(),
            )

        return self._to_conversation_response(db, conv, current_user.id)

    async def send_message(
        self,
        db: Session,
        current_user: User,
        conversation_id: int,
        message_text: str,
    ) -> ChatMessageResponse:
        """Send and persist a chat message, delivering duplex push to recipient (SKL-16 AC-2, AC-3)."""
        cleaned_text = message_text.strip()
        if not cleaned_text:
            raise BadRequestException("Message content cannot be empty")

        conv = self.repo.get_conversation_by_id(db, conversation_id)
        if not conv:
            raise NotFoundException(f"Conversation #{conversation_id} not found")

        # Authorization guard (AC-5)
        is_participant = current_user.id in [conv.learner_id, conv.instructor_id]
        if not is_participant and current_user.role != UserRole.ADMIN:
            raise ForbiddenException(
                "You are not authorized to send messages in this conversation",
                error_code="CONVERSATION_ACCESS_DENIED",
            )

        # Persist message to MySQL
        msg = self.repo.create_message(
            db=db,
            conversation_id=conversation_id,
            sender_id=current_user.id,
            message_text=cleaned_text,
        )

        msg_resp = self._to_message_response(msg)

        # Resolve counterpart user ID for duplex WebSocket delivery
        recipient_id = (
            conv.instructor_id
            if current_user.id == conv.learner_id
            else conv.learner_id
        )

        # Real-time WebSocket delivery (AC-3)
        ws_payload = {
            "type": "new_message",
            "conversation_id": conversation_id,
            "message": {
                "id": msg_resp.id,
                "conversation_id": msg_resp.conversation_id,
                "sender_id": msg_resp.sender_id,
                "sender_name": msg_resp.sender_name,
                "sender_role": msg_resp.sender_role,
                "message_text": msg_resp.message_text,
                "is_read": msg_resp.is_read,
                "created_at": msg_resp.created_at.isoformat(),
            },
        }

        # Deliver to recipient and echo back to sender's other connected tabs
        await connection_manager.send_personal_message(recipient_id, ws_payload)
        await connection_manager.send_personal_message(current_user.id, ws_payload)

        return msg_resp

    async def mark_as_read(
        self, db: Session, current_user: User, conversation_id: int
    ) -> ChatMarkReadResponse:
        """Mark messages as read and notify sender via WebSocket read receipt."""
        conv = self.repo.get_conversation_by_id(db, conversation_id)
        if not conv:
            raise NotFoundException("Conversation not found")

        is_participant = current_user.id in [conv.learner_id, conv.instructor_id]
        if not is_participant and current_user.role != UserRole.ADMIN:
            raise ForbiddenException("Access denied to conversation")

        marked_count = self.repo.mark_messages_as_read(
            db, conversation_id=conversation_id, reader_id=current_user.id
        )

        if marked_count > 0:
            sender_id = (
                conv.instructor_id
                if current_user.id == conv.learner_id
                else conv.learner_id
            )
            # Send real-time read receipt to the original message sender
            await connection_manager.send_personal_message(
                sender_id,
                {
                    "type": "messages_read",
                    "conversation_id": conversation_id,
                    "reader_id": current_user.id,
                    "marked_count": marked_count,
                },
            )

        return ChatMarkReadResponse(
            conversation_id=conversation_id, marked_count=marked_count
        )

    def get_instructors_directory(
        self, db: Session, current_user: User
    ) -> List[InstructorDirectoryItemResponse]:
        """Fetch list of verified instructors available for learner guidance."""
        items = self.repo.get_instructors_for_chat(db, current_user.id)
        results = []
        for inst, existing_conv_id in items:
            name = f"{inst.first_name} {inst.last_name}".strip() or inst.email
            profile = getattr(inst, "instructor_profile", None)
            results.append(
                InstructorDirectoryItemResponse(
                    id=inst.id,
                    name=name,
                    email=inst.email,
                    designation=profile.designation if profile else None,
                    institution=profile.institution if profile else None,
                    expertise_domain=profile.expertise_domain if profile else None,
                    years_experience=profile.years_experience if profile else None,
                    has_existing_conversation=existing_conv_id is not None,
                    existing_conversation_id=existing_conv_id,
                )
            )
        return results
