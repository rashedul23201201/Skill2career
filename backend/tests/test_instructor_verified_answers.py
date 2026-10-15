import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.models.profile import InstructorProfile
from app.models.forum import ForumCategory, ForumPost, ForumComment
from app.core.security import hash_password, create_access_token


def create_test_user(
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

    if role == UserRole.INSTRUCTOR and designation:
        profile = InstructorProfile(
            user_id=user.id,
            designation=designation,
            institution="University of Dhaka",
            onboarding_status="APPROVED",
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


def create_test_category(
    db: Session,
    name: str = "Data Structures",
    slug: str = "data-structures",
) -> ForumCategory:
    cat = ForumCategory(
        name=name,
        slug=slug,
        description="Data structures and algorithm questions",
        order_index=1,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def create_test_post(
    db: Session,
    author: User,
    category: ForumCategory,
    title: str = "How do binary search trees balance?",
    content: str = "Can someone explain how AVL trees maintain balance factors?",
) -> ForumPost:
    post = ForumPost(
        category_id=category.id,
        author_id=author.id,
        title=title,
        content=content,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def test_instructor_can_post_verified_answer_directly(client: TestClient, db_session: Session):
    """SKL-15 AC-1, AC-2, AC-6: Instructor submits answer marked as verified."""
    instructor = create_test_user(
        db_session,
        "prof_karim@example.com",
        UserRole.INSTRUCTOR,
        first_name="Karim",
        last_name="Chowdhury",
        designation="Senior Algorithm Instructor",
    )
    learner = create_test_user(db_session, "learner_trees@example.com", UserRole.LEARNER)
    cat = create_test_category(db_session, "Trees", "trees-test")
    post = create_test_post(db_session, learner, cat)

    headers = get_auth_headers(instructor)
    payload = {
        "content": "AVL trees perform single and double rotations (LL, RR, LR, RL) whenever balance factor falls outside [-1, 1].",
        "mark_as_verified": True,
    }

    res = client.post(f"/api/v1/forum/posts/{post.id}/comments", json=payload, headers=headers)
    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True
    comment_data = body["data"]

    # Verify AC-1 & AC-2: Stored with instructor identity and verified indicator
    assert comment_data["content"] == payload["content"]
    assert comment_data["is_verified"] is True
    assert comment_data["is_instructor_reply"] is True
    assert comment_data["verified_by"]["id"] == instructor.id
    assert comment_data["verified_by"]["designation"] == "Senior Algorithm Instructor"
    assert comment_data["verified_at"] is not None

    # Check post updated flag
    post_res = client.get(f"/api/v1/forum/posts/{post.id}")
    assert post_res.status_code == 200
    post_data = post_res.json()["data"]
    assert post_data["has_verified_answer"] is True
    assert post_data["has_instructor_reply"] is True


def test_instructor_can_mark_existing_comment_as_verified(client: TestClient, db_session: Session):
    """SKL-15 AC-2, AC-6: Instructor marks an existing comment as verified."""
    instructor = create_test_user(db_session, "instructor_mod@example.com", UserRole.INSTRUCTOR)
    learner1 = create_test_user(db_session, "learner_q@example.com", UserRole.LEARNER)
    learner2 = create_test_user(db_session, "learner_ans@example.com", UserRole.LEARNER)
    cat = create_test_category(db_session, "Algorithms", "algorithms-test")
    post = create_test_post(db_session, learner1, cat)

    # Learner2 posts a great answer
    learner_headers = get_auth_headers(learner2)
    comment_res = client.post(
        f"/api/v1/forum/posts/{post.id}/comments",
        json={"content": "Here is the textbook proof of logarithmic search bounds."},
        headers=learner_headers,
    )
    assert comment_res.status_code == 201
    comment_id = comment_res.json()["data"]["id"]
    assert comment_res.json()["data"]["is_verified"] is False

    # Instructor reviews and marks as verified
    inst_headers = get_auth_headers(instructor)
    verify_res = client.patch(
        f"/api/v1/forum/comments/{comment_id}/verify",
        json={"is_verified": True},
        headers=inst_headers,
    )
    assert verify_res.status_code == 200
    verify_data = verify_res.json()["data"]
    assert verify_data["is_verified"] is True
    assert verify_data["verified_by"]["id"] == instructor.id
    assert verify_data["verified_at"] is not None

    # Verify post reflects has_verified_answer
    post_res = client.get(f"/api/v1/forum/posts/{post.id}")
    assert post_res.json()["data"]["has_verified_answer"] is True


def test_learner_cannot_mark_comment_as_verified(client: TestClient, db_session: Session):
    """SKL-15 AC-5: Non-instructor / Non-admin cannot mark an answer as verified."""
    learner1 = create_test_user(db_session, "student1@example.com", UserRole.LEARNER)
    learner2 = create_test_user(db_session, "student2@example.com", UserRole.LEARNER)
    cat = create_test_category(db_session, "Web Dev", "web-dev-test")
    post = create_test_post(db_session, learner1, cat)

    # Post comment
    c_res = client.post(
        f"/api/v1/forum/posts/{post.id}/comments",
        json={"content": "Use React query for caching."},
        headers=get_auth_headers(learner2),
    )
    comment_id = c_res.json()["data"]["id"]

    # Learner attempts to verify
    hack_res = client.patch(
        f"/api/v1/forum/comments/{comment_id}/verify",
        json={"is_verified": True},
        headers=get_auth_headers(learner1),
    )
    assert hack_res.status_code == 403
    assert "Only verified instructors and administrators" in hack_res.json()["message"]


def test_learner_cannot_create_verified_comment(client: TestClient, db_session: Session):
    """SKL-15 AC-5: Learner cannot pass mark_as_verified: true on creation."""
    learner = create_test_user(db_session, "student_sneak@example.com", UserRole.LEARNER)
    cat = create_test_category(db_session, "Database", "database-test")
    post = create_test_post(db_session, learner, cat)

    res = client.post(
        f"/api/v1/forum/posts/{post.id}/comments",
        json={"content": "Fake verified answer", "mark_as_verified": True},
        headers=get_auth_headers(learner),
    )
    assert res.status_code == 403


def test_unauthenticated_cannot_verify(client: TestClient, db_session: Session):
    """SKL-15 Error Cases: Unauthenticated verification rejected."""
    cat = create_test_category(db_session, "Security", "security-test")
    user = create_test_user(db_session, "author@example.com", UserRole.LEARNER)
    post = create_test_post(db_session, user, cat)

    comment = ForumComment(
        post_id=post.id,
        author_id=user.id,
        content="Some test response",
    )
    db_session.add(comment)
    db_session.commit()

    res = client.patch(f"/api/v1/forum/comments/{comment.id}/verify", json={"is_verified": True})
    assert res.status_code == 401


def test_verified_comments_pinned_first_in_post_detail(client: TestClient, db_session: Session):
    """SKL-15 AC-3: Verified answers are ordered first for learner visibility."""
    instructor = create_test_user(db_session, "prof_pin@example.com", UserRole.INSTRUCTOR)
    learner = create_test_user(db_session, "learner_pin@example.com", UserRole.LEARNER)
    cat = create_test_category(db_session, "Pinning", "pinning-test")
    post = create_test_post(db_session, learner, cat)

    # 1st: Regular comment
    c1_res = client.post(
        f"/api/v1/forum/posts/{post.id}/comments",
        json={"content": "First chronological comment (regular learner)."},
        headers=get_auth_headers(learner),
    )
    c1_id = c1_res.json()["data"]["id"]

    # 2nd: Verified comment posted later
    c2_res = client.post(
        f"/api/v1/forum/posts/{post.id}/comments",
        json={"content": "Second chronological comment, but VERIFIED by Instructor.", "mark_as_verified": True},
        headers=get_auth_headers(instructor),
    )
    c2_id = c2_res.json()["data"]["id"]

    # 3rd: Another regular comment
    c3_res = client.post(
        f"/api/v1/forum/posts/{post.id}/comments",
        json={"content": "Third chronological comment (regular learner)."},
        headers=get_auth_headers(learner),
    )
    c3_id = c3_res.json()["data"]["id"]

    # Fetch post detail
    detail_res = client.get(f"/api/v1/forum/posts/{post.id}")
    assert detail_res.status_code == 200
    comments = detail_res.json()["data"]["comments"]
    assert len(comments) == 3

    # Verified comment must be the FIRST item in the comments list
    assert comments[0]["id"] == c2_id
    assert comments[0]["is_verified"] is True
    assert comments[1]["id"] == c1_id
    assert comments[2]["id"] == c3_id


def test_instructor_can_unverify_comment(client: TestClient, db_session: Session):
    """SKL-15 AC-2: Instructor can unmark a verified comment."""
    instructor = create_test_user(db_session, "inst_unmark@example.com", UserRole.INSTRUCTOR)
    learner = create_test_user(db_session, "learner_unmark@example.com", UserRole.LEARNER)
    cat = create_test_category(db_session, "Unmark", "unmark-test")
    post = create_test_post(db_session, learner, cat)

    # Create verified comment
    c_res = client.post(
        f"/api/v1/forum/posts/{post.id}/comments",
        json={"content": "Initially verified answer.", "mark_as_verified": True},
        headers=get_auth_headers(instructor),
    )
    comment_id = c_res.json()["data"]["id"]
    assert c_res.json()["data"]["is_verified"] is True

    # Unverify
    unverify_res = client.patch(
        f"/api/v1/forum/comments/{comment_id}/verify",
        json={"is_verified": False},
        headers=get_auth_headers(instructor),
    )
    assert unverify_res.status_code == 200
    assert unverify_res.json()["data"]["is_verified"] is False
    assert unverify_res.json()["data"]["verified_by"] is None

    # Check post flag is updated
    post_res = client.get(f"/api/v1/forum/posts/{post.id}")
    assert post_res.json()["data"]["has_verified_answer"] is False


def test_instructor_can_update_own_answer(client: TestClient, db_session: Session):
    """SKL-15 AC-4: Instructor can edit their own answer."""
    instructor = create_test_user(db_session, "inst_edit@example.com", UserRole.INSTRUCTOR)
    cat = create_test_category(db_session, "Editing", "editing-test")
    post = create_test_post(db_session, instructor, cat)

    c_res = client.post(
        f"/api/v1/forum/posts/{post.id}/comments",
        json={"content": "Original guidance.", "mark_as_verified": True},
        headers=get_auth_headers(instructor),
    )
    comment_id = c_res.json()["data"]["id"]

    edit_res = client.put(
        f"/api/v1/forum/comments/{comment_id}",
        json={"content": "Updated and clarified expert guidance."},
        headers=get_auth_headers(instructor),
    )
    assert edit_res.status_code == 200
    assert edit_res.json()["data"]["content"] == "Updated and clarified expert guidance."
    assert edit_res.json()["data"]["is_verified"] is True


def test_instructor_can_delete_own_answer_and_recalculates_flag(client: TestClient, db_session: Session):
    """SKL-15 AC-4: Deleting verified answer removes verified status from post."""
    instructor = create_test_user(db_session, "inst_del@example.com", UserRole.INSTRUCTOR)
    cat = create_test_category(db_session, "Delete", "delete-test")
    post = create_test_post(db_session, instructor, cat)

    c_res = client.post(
        f"/api/v1/forum/posts/{post.id}/comments",
        json={"content": "Temporary verified answer.", "mark_as_verified": True},
        headers=get_auth_headers(instructor),
    )
    comment_id = c_res.json()["data"]["id"]

    post_check = client.get(f"/api/v1/forum/posts/{post.id}")
    assert post_check.json()["data"]["has_verified_answer"] is True

    # Delete comment
    del_res = client.delete(f"/api/v1/forum/comments/{comment_id}", headers=get_auth_headers(instructor))
    assert del_res.status_code == 200

    # Post has_verified_answer should now be False
    post_after = client.get(f"/api/v1/forum/posts/{post.id}")
    assert post_after.json()["data"]["has_verified_answer"] is False


def test_filter_discussions_by_has_verified_answer(client: TestClient, db_session: Session):
    """SKL-15 AC-3: Filter posts by verified answers."""
    instructor = create_test_user(db_session, "inst_filt@example.com", UserRole.INSTRUCTOR)
    learner = create_test_user(db_session, "learner_filt@example.com", UserRole.LEARNER)
    cat = create_test_category(db_session, "Filtering", "filtering-test")

    # Post with verified answer
    post_verified = create_test_post(db_session, learner, cat, title="Question with verified answer")
    client.post(
        f"/api/v1/forum/posts/{post_verified.id}/comments",
        json={"content": "Verified solution.", "mark_as_verified": True},
        headers=get_auth_headers(instructor),
    )

    # Post without verified answer
    post_unverified = create_test_post(db_session, learner, cat, title="Question without verified answer")

    # Filter with has_verified_answer=true
    res = client.get("/api/v1/forum/posts?has_verified_answer=true")
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    assert any(p["id"] == post_verified.id for p in items)
    assert not any(p["id"] == post_unverified.id for p in items)
