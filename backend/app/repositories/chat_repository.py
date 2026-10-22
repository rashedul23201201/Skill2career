from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy import select, func, and_, or_, update
from sqlalchemy.orm import Session, joinedload

from app.models.chat import ChatConversation, ChatMessage
from app.models.user import User, UserRole
from app.models.profile import LearnerProfile, InstructorProfile


class ChatRepository:
    """Persistence operations for Chat conversations and messages (SKL-16)."""

    @staticmethod
    def get_or_create_conversation(
        db: Session, learner_id: int, instructor_id: int
    ) -> Tuple[ChatConversation, bool]:
        """Find existing conversation or create a new one between a learner and instructor.
        Returns (conversation, is_created).
        """
        stmt = (
            select(ChatConversation)
            .options(
                joinedload(ChatConversation.learner).joinedload(User.learner_profile),
                joinedload(ChatConversation.instructor).joinedload(User.instructor_profile),
            )
            .where(
                and_(
                    ChatConversation.learner_id == learner_id,
                    ChatConversation.instructor_id == instructor_id,
                )
            )
        )
        existing = db.execute(stmt).scalars().first()
        if existing:
            return existing, False

        new_conv = ChatConversation(
            learner_id=learner_id,
            instructor_id=instructor_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(new_conv)
        db.commit()
        db.refresh(new_conv)

        # Reload with relations
        reloaded = (
            db.execute(
                select(ChatConversation)
                .options(
                    joinedload(ChatConversation.learner).joinedload(User.learner_profile),
                    joinedload(ChatConversation.instructor).joinedload(User.instructor_profile),
                )
                .where(ChatConversation.id == new_conv.id)
            )
            .scalars()
            .first()
        )
        return reloaded or new_conv, True

    @staticmethod
    def get_conversation_by_id(
        db: Session, conversation_id: int
    ) -> Optional[ChatConversation]:
        """Retrieve conversation with eager-loaded participants."""
        stmt = (
            select(ChatConversation)
            .options(
                joinedload(ChatConversation.learner).joinedload(User.learner_profile),
                joinedload(ChatConversation.instructor).joinedload(User.instructor_profile),
            )
            .where(ChatConversation.id == conversation_id)
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def get_user_conversations(
        db: Session, user_id: int
    ) -> List[ChatConversation]:
        """Retrieve all active conversations for a user, ordered by latest activity."""
        stmt = (
            select(ChatConversation)
            .options(
                joinedload(ChatConversation.learner).joinedload(User.learner_profile),
                joinedload(ChatConversation.instructor).joinedload(User.instructor_profile),
                joinedload(ChatConversation.messages),
            )
            .where(
                or_(
                    ChatConversation.learner_id == user_id,
                    ChatConversation.instructor_id == user_id,
                )
            )
            .order_by(ChatConversation.updated_at.desc())
        )
        return list(db.execute(stmt).unique().scalars().all())

    @staticmethod
    def get_conversation_messages(
        db: Session, conversation_id: int, limit: int = 100, offset: int = 0
    ) -> List[ChatMessage]:
        """Fetch chronological messages for a conversation."""
        stmt = (
            select(ChatMessage)
            .options(joinedload(ChatMessage.sender))
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_last_message(
        db: Session, conversation_id: int
    ) -> Optional[ChatMessage]:
        """Retrieve the most recent message in a conversation."""
        stmt = (
            select(ChatMessage)
            .options(joinedload(ChatMessage.sender))
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(1)
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def create_message(
        db: Session, conversation_id: int, sender_id: int, message_text: str
    ) -> ChatMessage:
        """Create and persist a new chat message, updating conversation timestamp."""
        now = datetime.now(timezone.utc)
        message = ChatMessage(
            conversation_id=conversation_id,
            sender_id=sender_id,
            message_text=message_text,
            is_read=False,
            created_at=now,
        )
        db.add(message)

        # Update parent conversation updated_at
        db.execute(
            update(ChatConversation)
            .where(ChatConversation.id == conversation_id)
            .values(updated_at=now)
        )

        db.commit()
        db.refresh(message)

        # Reload with sender
        reloaded = (
            db.execute(
                select(ChatMessage)
                .options(joinedload(ChatMessage.sender))
                .where(ChatMessage.id == message.id)
            )
            .scalars()
            .first()
        )
        return reloaded or message

    @staticmethod
    def mark_messages_as_read(
        db: Session, conversation_id: int, reader_id: int
    ) -> int:
        """Mark all incoming unread messages as read."""
        stmt = (
            update(ChatMessage)
            .where(
                and_(
                    ChatMessage.conversation_id == conversation_id,
                    ChatMessage.sender_id != reader_id,
                    ChatMessage.is_read.is_(False),
                )
            )
            .values(is_read=True)
        )
        result = db.execute(stmt)
        db.commit()
        return result.rowcount or 0

    @staticmethod
    def get_unread_count(
        db: Session, conversation_id: int, user_id: int
    ) -> int:
        """Get count of unread incoming messages for user in a conversation."""
        stmt = select(func.count(ChatMessage.id)).where(
            and_(
                ChatMessage.conversation_id == conversation_id,
                ChatMessage.sender_id != user_id,
                ChatMessage.is_read.is_(False),
            )
        )
        return db.execute(stmt).scalar() or 0

    @staticmethod
    def get_total_unread_for_user(db: Session, user_id: int) -> int:
        """Get total unread messages count across all conversations for a user."""
        stmt = (
            select(func.count(ChatMessage.id))
            .join(ChatConversation, ChatMessage.conversation_id == ChatConversation.id)
            .where(
                and_(
                    or_(
                        ChatConversation.learner_id == user_id,
                        ChatConversation.instructor_id == user_id,
                    ),
                    ChatMessage.sender_id != user_id,
                    ChatMessage.is_read.is_(False),
                )
            )
        )
        return db.execute(stmt).scalar() or 0

    @staticmethod
    def get_instructors_for_chat(
        db: Session, learner_id: int
    ) -> List[Tuple[User, Optional[int]]]:
        """List active instructors with existing conversation IDs if already started."""
        instructors_stmt = (
            select(User)
            .options(joinedload(User.instructor_profile))
            .where(
                and_(
                    User.role == UserRole.INSTRUCTOR,
                    User.is_active.is_(True),
                )
            )
            .order_by(User.first_name.asc())
        )
        instructors = list(db.execute(instructors_stmt).unique().scalars().all())

        # Check existing conversations for this learner (maps instructor_id -> conversation_id)
        conv_stmt = select(ChatConversation.instructor_id, ChatConversation.id).where(
            ChatConversation.learner_id == learner_id
        )
        conv_map = dict(db.execute(conv_stmt).all())

        results = []
        for inst in instructors:
            conv_id = conv_map.get(inst.id)
            results.append((inst, conv_id))

        return results
