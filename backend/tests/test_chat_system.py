import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.profile import LearnerProfile, InstructorProfile
from app.models.chat import ChatConversation, ChatMessage
from app.core.security import hash_password, create_access_token


def create_user(
    db: Session,
    email: str,
    role: UserRole = UserRole.LEARNER,
    first_name: str = "Test",
    last_name: str = "User",
    designation: str = None,
) -> User:
    user = User(
        email=email,
        hashed_password=hash_password("Password123!"),
        role=role,
        first_name=first_name,
        last_name=last_name,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if role == UserRole.INSTRUCTOR:
        profile = InstructorProfile(
            user_id=user.id,
            designation=designation or "Senior AI Engineer",
            institution="University of Dhaka",
            onboarding_status="APPROVED",
        )
        db.add(profile)
        db.commit()
        db.refresh(user)
    elif role == UserRole.LEARNER:
        profile = LearnerProfile(
            user_id=user.id,
            target_role="Software Engineer",
            institution="BUET",
        )
        db.add(profile)
        db.commit()
        db.refresh(user)

    return user


def get_auth_headers(user: User) -> dict:
    token = create_access_token(
        subject=user.id,
        claims={"email": user.email, "role": user.role.value},
    )
    return {"Authorization": f"Bearer {token}"}


def get_token(user: User) -> str:
    return create_access_token(
        subject=user.id,
        claims={"email": user.email, "role": user.role.value},
    )


# ============================================================================
# Acceptance Criteria Tests
# ============================================================================

def test_create_and_list_conversations_ac1(client: TestClient, db_session: Session):
    """AC-1: Given an authenticated user, when Chat is opened, then available conversations must be displayed."""
    learner = create_user(db_session, "learner_ac1@example.com", UserRole.LEARNER, "Rashedul", "Islam")
    instructor = create_user(db_session, "inst_ac1@example.com", UserRole.INSTRUCTOR, "Farhana", "Kabir")

    learner_headers = get_auth_headers(learner)
    inst_headers = get_auth_headers(instructor)

    # 1. Initialize conversation
    init_res = client.post(
        "/api/v1/chat/conversations",
        headers=learner_headers,
        json={"instructor_id": instructor.id, "initial_message": "Hello Professor Kabir!"},
    )
    assert init_res.status_code == 201
    init_data = init_res.json()["data"]
    assert init_data["learner_id"] == learner.id
    assert init_data["instructor_id"] == instructor.id
    assert init_data["participant"]["name"] == "Farhana Kabir"
    assert init_data["last_message"]["message_text"] == "Hello Professor Kabir!"

    conv_id = init_data["id"]

    # 2. Learner lists conversations
    learner_list_res = client.get("/api/v1/chat/conversations", headers=learner_headers)
    assert learner_list_res.status_code == 200
    conversations = learner_list_res.json()["data"]
    assert len(conversations) == 1
    assert conversations[0]["id"] == conv_id
    assert conversations[0]["participant"]["role"] == "INSTRUCTOR"

    # 3. Instructor lists conversations
    inst_list_res = client.get("/api/v1/chat/conversations", headers=inst_headers)
    assert inst_list_res.status_code == 200
    inst_conversations = inst_list_res.json()["data"]
    assert len(inst_conversations) == 1
    assert inst_conversations[0]["id"] == conv_id
    assert inst_conversations[0]["participant"]["name"] == "Rashedul Islam"
    assert inst_conversations[0]["participant"]["role"] == "LEARNER"
    assert inst_conversations[0]["unread_count"] == 1


def test_send_and_persist_message_ac2(client: TestClient, db_session: Session):
    """AC-2: Given an authorized user, when a valid message is sent, then it must be delivered and stored."""
    learner = create_user(db_session, "learner_ac2@example.com", UserRole.LEARNER)
    instructor = create_user(db_session, "inst_ac2@example.com", UserRole.INSTRUCTOR)

    learner_headers = get_auth_headers(learner)
    inst_headers = get_auth_headers(instructor)

    # Start conversation
    init_res = client.post(
        "/api/v1/chat/conversations",
        headers=learner_headers,
        json={"instructor_id": instructor.id},
    )
    conv_id = init_res.json()["data"]["id"]

    # Send message from instructor
    send_res = client.post(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        headers=inst_headers,
        json={"message_text": "Welcome to the Machine Learning guidance thread."},
    )
    assert send_res.status_code == 201
    msg_data = send_res.json()["data"]
    assert msg_data["conversation_id"] == conv_id
    assert msg_data["sender_id"] == instructor.id
    assert msg_data["message_text"] == "Welcome to the Machine Learning guidance thread."
    assert msg_data["is_read"] is False

    # Verify directly in database
    db_msg = db_session.query(ChatMessage).filter_by(id=msg_data["id"]).first()
    assert db_msg is not None
    assert db_msg.message_text == "Welcome to the Machine Learning guidance thread."
    assert db_msg.is_read is False


def test_retrieve_previous_messages_ac4(client: TestClient, db_session: Session):
    """AC-4: Given an existing conversation, when it is opened, then previous messages must be displayed."""
    learner = create_user(db_session, "learner_ac4@example.com", UserRole.LEARNER)
    instructor = create_user(db_session, "inst_ac4@example.com", UserRole.INSTRUCTOR)

    learner_headers = get_auth_headers(learner)
    inst_headers = get_auth_headers(instructor)

    # Setup conversation with two messages
    init_res = client.post(
        "/api/v1/chat/conversations",
        headers=learner_headers,
        json={"instructor_id": instructor.id, "initial_message": "Message 1 from learner"},
    )
    conv_id = init_res.json()["data"]["id"]

    client.post(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        headers=inst_headers,
        json={"message_text": "Message 2 reply from instructor"},
    )

    # Retrieve messages
    get_msgs_res = client.get(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        headers=learner_headers,
    )
    assert get_msgs_res.status_code == 200
    messages = get_msgs_res.json()["data"]
    assert len(messages) == 2
    assert messages[0]["message_text"] == "Message 1 from learner"
    assert messages[1]["message_text"] == "Message 2 reply from instructor"

    # Mark as read
    read_res = client.post(
        f"/api/v1/chat/conversations/{conv_id}/read",
        headers=learner_headers,
    )
    assert read_res.status_code == 200
    assert read_res.json()["data"]["marked_count"] == 1


def test_unauthorized_access_denied_ac5(client: TestClient, db_session: Session):
    """AC-5: Given an unauthorized user, when a restricted conversation is accessed, then access must be denied."""
    learner1 = create_user(db_session, "learner1_ac5@example.com", UserRole.LEARNER)
    instructor1 = create_user(db_session, "inst1_ac5@example.com", UserRole.INSTRUCTOR)
    intruder = create_user(db_session, "intruder_ac5@example.com", UserRole.LEARNER)

    l1_headers = get_auth_headers(learner1)
    intruder_headers = get_auth_headers(intruder)

    # Create conversation between learner1 and instructor1
    init_res = client.post(
        "/api/v1/chat/conversations",
        headers=l1_headers,
        json={"instructor_id": instructor1.id, "initial_message": "Confidential academic chat"},
    )
    conv_id = init_res.json()["data"]["id"]

    # Intruder tries to view details
    detail_res = client.get(f"/api/v1/chat/conversations/{conv_id}", headers=intruder_headers)
    assert detail_res.status_code == 403

    # Intruder tries to view messages
    msg_res = client.get(f"/api/v1/chat/conversations/{conv_id}/messages", headers=intruder_headers)
    assert msg_res.status_code == 403

    # Intruder tries to post a message
    send_res = client.post(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        headers=intruder_headers,
        json={"message_text": "I am an unauthorized third party"},
    )
    assert send_res.status_code == 403


def test_empty_message_validation(client: TestClient, db_session: Session):
    """Ensure empty or whitespace-only messages are rejected with 400 Bad Request."""
    learner = create_user(db_session, "learner_val@example.com", UserRole.LEARNER)
    instructor = create_user(db_session, "inst_val@example.com", UserRole.INSTRUCTOR)

    learner_headers = get_auth_headers(learner)

    init_res = client.post(
        "/api/v1/chat/conversations",
        headers=learner_headers,
        json={"instructor_id": instructor.id},
    )
    conv_id = init_res.json()["data"]["id"]

    res = client.post(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        headers=learner_headers,
        json={"message_text": "   "},
    )
    assert res.status_code in [400, 422]


def test_instructors_directory(client: TestClient, db_session: Session):
    """Verify learner can discover instructors directory with existing conversation badge."""
    learner = create_user(db_session, "learner_dir@example.com", UserRole.LEARNER)
    inst1 = create_user(db_session, "inst1_dir@example.com", UserRole.INSTRUCTOR, "Rahim", "Chowdhury")
    inst2 = create_user(db_session, "inst2_dir@example.com", UserRole.INSTRUCTOR, "Karim", "Uddin")

    learner_headers = get_auth_headers(learner)

    # Initial directory
    dir_res = client.get("/api/v1/chat/instructors", headers=learner_headers)
    assert dir_res.status_code == 200
    items = dir_res.json()["data"]
    assert len(items) >= 2

    # Start chat with inst1
    client.post(
        "/api/v1/chat/conversations",
        headers=learner_headers,
        json={"instructor_id": inst1.id},
    )

    # Check directory again: inst1 should have has_existing_conversation=True
    dir_res2 = client.get("/api/v1/chat/instructors", headers=learner_headers)
    items2 = dir_res2.json()["data"]
    inst1_item = next(it for it in items2 if it["id"] == inst1.id)
    assert inst1_item["has_existing_conversation"] is True
    assert inst1_item["existing_conversation_id"] is not None


def test_websocket_channel_handshake_and_messaging_ac3(client: TestClient, db_session: Session):
    """AC-3: WebSocket connection handshake, rejection of bad tokens, and duplex messaging."""
    learner = create_user(db_session, "learner_ws@example.com", UserRole.LEARNER)
    instructor = create_user(db_session, "inst_ws@example.com", UserRole.INSTRUCTOR)

    learner_token = get_token(learner)

    # 1. Reject without token
    with pytest.raises(Exception):
        with client.websocket_connect("/api/v1/ws/chat") as ws:
            pass

    # 2. Reject with invalid token
    with pytest.raises(Exception):
        with client.websocket_connect("/api/v1/ws/chat?token=invalid_token") as ws:
            pass

    # 3. Create conversation first
    l_headers = get_auth_headers(learner)
    conv_res = client.post(
        "/api/v1/chat/conversations",
        headers=l_headers,
        json={"instructor_id": instructor.id},
    )
    conv_id = conv_res.json()["data"]["id"]

    # 4. Valid WebSocket connection
    with client.websocket_connect(f"/api/v1/ws/chat?token={learner_token}") as ws:
        connected_payload = ws.receive_json()
        assert connected_payload["type"] == "connected"
        assert connected_payload["user_id"] == learner.id

        # Send ping
        ws.send_json({"action": "ping"})
        pong = ws.receive_json()
        assert pong["type"] == "pong"

        # Send message via WebSocket
        ws.send_json(
            {
                "action": "send_message",
                "conversation_id": conv_id,
                "message_text": "Live WebSocket message from learner",
            }
        )

        ack = ws.receive_json()
        assert ack["type"] == "new_message"
        assert ack["message"]["message_text"] == "Live WebSocket message from learner"

        # Verify message persisted in database
        persisted = db_session.query(ChatMessage).filter_by(
            conversation_id=conv_id, message_text="Live WebSocket message from learner"
        ).first()
        assert persisted is not None
        assert persisted.sender_id == learner.id
