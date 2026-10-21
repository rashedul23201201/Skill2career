import logging
from typing import List, Optional
from fastapi import (
    APIRouter,
    Depends,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy.orm import Session

from app.database.session import get_db, SessionLocal
from app.dependencies.auth import get_current_user
from app.core.security import decode_access_token
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import ApiResponse
from app.schemas.chat import (
    ChatConversationResponse,
    ChatMessageResponse,
    ChatCreateConversationRequest,
    ChatSendMessageRequest,
    ChatMarkReadResponse,
    InstructorDirectoryItemResponse,
)
from app.services.chat_service import ChatService
from app.services.websocket_manager import connection_manager

logger = logging.getLogger("chat.router")

router = APIRouter(prefix="/chat", tags=["Real-time Chat System (SKL-16)"])
ws_router = APIRouter(prefix="/ws", tags=["WebSocket Real-time Channel (SKL-16)"])

chat_service = ChatService()


# ============================================================================
# REST Endpoints for Chat State & Historical Logs
# ============================================================================

@router.get(
    "/conversations",
    response_model=ApiResponse[List[ChatConversationResponse]],
    status_code=status.HTTP_200_OK,
    summary="List authenticated user's active conversations (SKL-16 AC-1)",
)
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[List[ChatConversationResponse]]:
    """Retrieve all conversations for the calling learner or instructor with last message snippet."""
    conversations = chat_service.list_conversations(db=db, current_user=current_user)
    return ApiResponse[List[ChatConversationResponse]](
        success=True,
        message="Conversations retrieved successfully",
        data=conversations,
    )


@router.post(
    "/conversations",
    response_model=ApiResponse[ChatConversationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Initiate or retrieve direct conversation with an instructor (SKL-16 AC-1)",
)
async def create_or_get_conversation(
    request: ChatCreateConversationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[ChatConversationResponse]:
    """Start a new chat thread or open existing conversation with an instructor."""
    conv = await chat_service.create_conversation(
        db=db, current_user=current_user, request=request
    )
    return ApiResponse[ChatConversationResponse](
        success=True,
        message="Conversation initialized successfully",
        data=conv,
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ApiResponse[ChatConversationResponse],
    status_code=status.HTTP_200_OK,
    summary="Get conversation details by ID (SKL-16 AC-4, AC-5)",
)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[ChatConversationResponse]:
    """Retrieve conversation details and participant information with RBAC guard."""
    conv = chat_service.get_conversation_details(
        db=db, current_user=current_user, conversation_id=conversation_id
    )
    return ApiResponse[ChatConversationResponse](
        success=True,
        message="Conversation details retrieved successfully",
        data=conv,
    )


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=ApiResponse[List[ChatMessageResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get paginated historical messages for a conversation (SKL-16 AC-4, AC-5)",
)
def get_conversation_messages(
    conversation_id: int,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[List[ChatMessageResponse]]:
    """Retrieve historical chat log for a conversation with authorization protection."""
    messages = chat_service.get_messages(
        db=db,
        current_user=current_user,
        conversation_id=conversation_id,
        limit=limit,
        offset=offset,
    )
    return ApiResponse[List[ChatMessageResponse]](
        success=True,
        message="Historical messages retrieved successfully",
        data=messages,
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=ApiResponse[ChatMessageResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Send a chat message via REST (SKL-16 AC-2)",
)
async def send_message_rest(
    conversation_id: int,
    request: ChatSendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[ChatMessageResponse]:
    """Send and persist a chat message, pushing real-time notification to active recipient."""
    msg = await chat_service.send_message(
        db=db,
        current_user=current_user,
        conversation_id=conversation_id,
        message_text=request.message_text,
    )
    return ApiResponse[ChatMessageResponse](
        success=True,
        message="Message delivered and stored successfully",
        data=msg,
    )


@router.post(
    "/conversations/{conversation_id}/read",
    response_model=ApiResponse[ChatMarkReadResponse],
    status_code=status.HTTP_200_OK,
    summary="Mark incoming conversation messages as read (SKL-16)",
)
async def mark_messages_read(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[ChatMarkReadResponse]:
    """Mark incoming unread messages as read and send real-time read receipt."""
    result = await chat_service.mark_as_read(
        db=db, current_user=current_user, conversation_id=conversation_id
    )
    return ApiResponse[ChatMarkReadResponse](
        success=True,
        message="Messages marked as read",
        data=result,
    )


@router.get(
    "/instructors",
    response_model=ApiResponse[List[InstructorDirectoryItemResponse]],
    status_code=status.HTTP_200_OK,
    summary="List available instructors for direct chat guidance (SKL-16)",
)
def get_instructors_directory(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[List[InstructorDirectoryItemResponse]]:
    """List instructors that learners can start direct real-time guidance conversations with."""
    directory = chat_service.get_instructors_directory(db=db, current_user=current_user)
    return ApiResponse[List[InstructorDirectoryItemResponse]](
        success=True,
        message="Instructors directory retrieved successfully",
        data=directory,
    )


# ============================================================================
# WebSocket Duplex Channel Endpoint (SKL-16 AC-2, AC-3)
# ============================================================================

@ws_router.websocket("/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> None:
    """Duplex WebSocket channel for real-time messaging, typing events, and read receipts (SKL-16).
    Authentication: query parameter ?token={jwt}.
    """
    if not token:
        logger.warning("WebSocket rejected: Missing token query parameter")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
        return

    # Authenticate JWT token
    try:
        payload = decode_access_token(token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token claims")
            return
        user_id = int(user_id_str)
    except Exception as exc:
        logger.warning("WebSocket authentication failed: %s", exc)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
        return

    # Verify user existence and active status in DB
    user = UserRepository.get_by_id(db, user_id)
    if not user or not user.is_active:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User inactive or not found")
        return

    # Register active socket connection
    await connection_manager.connect(user_id, websocket)

    # Deliver connected handshake confirmation
    await websocket.send_json(
        {
            "type": "connected",
            "user_id": user_id,
            "message": "Real-time chat duplex connection established",
        }
    )

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "send_message":
                conversation_id = data.get("conversation_id")
                message_text = data.get("message_text", "")
                if not conversation_id or not message_text.strip():
                    await websocket.send_json(
                        {"type": "error", "message": "conversation_id and message_text required"}
                    )
                    continue

                current_user = UserRepository.get_by_id(db, user_id)
                try:
                    await chat_service.send_message(
                        db=db,
                        current_user=current_user,
                        conversation_id=int(conversation_id),
                        message_text=message_text,
                    )
                except Exception as err:
                    await websocket.send_json({"type": "error", "message": str(err)})

            elif action == "typing":
                conversation_id = data.get("conversation_id")
                is_typing = bool(data.get("is_typing", True))
                if conversation_id:
                    conv = chat_service.repo.get_conversation_by_id(db, int(conversation_id))
                    if conv and user_id in [conv.learner_id, conv.instructor_id]:
                        recipient_id = (
                            conv.instructor_id if user_id == conv.learner_id else conv.learner_id
                        )
                        await connection_manager.send_personal_message(
                            recipient_id,
                            {
                                "type": "typing_status",
                                "conversation_id": int(conversation_id),
                                "user_id": user_id,
                                "is_typing": is_typing,
                            },
                        )

            elif action == "mark_read":
                conversation_id = data.get("conversation_id")
                if conversation_id:
                    current_user = UserRepository.get_by_id(db, user_id)
                    try:
                        await chat_service.mark_as_read(
                            db=db,
                            current_user=current_user,
                            conversation_id=int(conversation_id),
                        )
                    except Exception as err:
                        logger.debug("Error marking read via WebSocket: %s", err)

            elif action == "ping":
                await websocket.send_json({"type": "pong"})

            else:
                logger.debug("Unhandled WebSocket action: %s", action)

    except WebSocketDisconnect:
        connection_manager.disconnect(user_id, websocket)
    except Exception as exc:
        logger.warning("Unexpected WebSocket error for User ID %s: %s", user_id, exc)
        connection_manager.disconnect(user_id, websocket)
