import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.models.forum import ForumCategory, ForumPost, ForumComment
from app.core.security import hash_password, create_access_token


def create_test_user(
    db: Session,
    email: str,
    role: UserRole = UserRole.LEARNER,
    first_name: str = "Test",
    last_name: str = "User",
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
    return user


def get_auth_headers(user: User) -> dict:
    token = create_access_token(
        subject=user.id,
        claims={"email": user.email, "role": user.role.value},
    )
    return {"Authorization": f"Bearer {token}"}


def create_test_category(
    db: Session,
    name: str = "General Discussion",
    slug: str = "general-discussion",
) -> ForumCategory:
    cat = ForumCategory(
        name=name,
        slug=slug,
        description="General discussion topics",
        order_index=1,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def test_get_forum_categories_success(client: TestClient, db_session: Session):
    cat = create_test_category(db_session, "Programming", "programming-test")
    res = client.get("/api/v1/forum/categories")
    assert res.status_code == 200
    data = res.json()["data"]
    assert any(c["id"] == cat.id and c["name"] == "Programming" for c in data)


def test_create_forum_post_success(client: TestClient, db_session: Session):
    learner = create_test_user(db_session, "learner_post@example.com", UserRole.LEARNER)
    cat = create_test_category(db_session, "Interview Prep", "interview-prep-post")
    headers = get_auth_headers(learner)

    payload = {
        "title": "How to prepare for FastAPI technical interviews?",
        "category_id": cat.id,
        "content": "What are the common async patterns and dependency injection concepts to practice?",
    }
    res = client.post("/api/v1/forum/posts", json=payload, headers=headers)
    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True
    data = body["data"]
    assert data["title"] == payload["title"]
    assert data["author"]["id"] == learner.id
    assert data["category_id"] == cat.id


def test_create_forum_post_validation_error(client: TestClient, db_session: Session):
    learner = create_test_user(db_session, "learner_val@example.com", UserRole.LEARNER)
    headers = get_auth_headers(learner)

    payload = {
        "title": "Hi",
        "category_id": 99999,
        "content": "Short",
    }
    res = client.post("/api/v1/forum/posts", json=payload, headers=headers)
    assert res.status_code == 422


def test_get_forum_posts_pagination_and_filter(client: TestClient, db_session: Session):
    user = create_test_user(db_session, "user_pag@example.com", UserRole.LEARNER)
    cat1 = create_test_category(db_session, "Cat One", "cat-one")
    cat2 = create_test_category(db_session, "Cat Two", "cat-two")

    post1 = ForumPost(category_id=cat1.id, author_id=user.id, title="Post 1 in Cat 1", content="Content of first post")
    post2 = ForumPost(category_id=cat2.id, author_id=user.id, title="Post 2 in Cat 2", content="Content of second post")
    db_session.add_all([post1, post2])
    db_session.commit()

    res = client.get(f"/api/v1/forum/posts?category_id={cat1.id}")
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    assert len(items) >= 1
    assert all(p["category_id"] == cat1.id for p in items)


def test_search_forum_posts_by_keyword(client: TestClient, db_session: Session):
    user = create_test_user(db_session, "user_search@example.com", UserRole.LEARNER, first_name="Sakib", last_name="Hasan")
    cat = create_test_category(db_session, "Databases", "db-search")

    post = ForumPost(
        category_id=cat.id,
        author_id=user.id,
        title="Microservices Event Sourcing Architecture",
        content="Exploring Kafka and Debezium for real-time change data capture.",
    )
    db_session.add(post)
    db_session.commit()

    res = client.get("/api/v1/forum/posts?search=Debezium")
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    assert any(p["id"] == post.id for p in items)

    # Search by author name
    res_author = client.get("/api/v1/forum/posts?search=Sakib")
    assert res_author.status_code == 200
    items_author = res_author.json()["data"]["items"]
    assert any(p["id"] == post.id for p in items_author)


def test_get_post_detail_thread_and_views(client: TestClient, db_session: Session):
    user = create_test_user(db_session, "detail_author@example.com", UserRole.LEARNER)
    cat = create_test_category(db_session, "Web Dev", "web-dev-detail")
    post = ForumPost(category_id=cat.id, author_id=user.id, title="React 19 Server Actions", content="How will actions affect state management?", views_count=0)
    db_session.add(post)
    db_session.commit()

    res = client.get(f"/api/v1/forum/posts/{post.id}")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["id"] == post.id
    assert data["views_count"] == 1

    # Also fetch with auth headers to verify authenticated like status lookup
    headers = get_auth_headers(user)
    res_auth = client.get(f"/api/v1/forum/posts/{post.id}", headers=headers)
    assert res_auth.status_code == 200
    assert res_auth.json()["data"]["is_liked_by_me"] is False


def test_add_comment_learner_and_instructor(client: TestClient, db_session: Session):
    learner = create_test_user(db_session, "learner_comm@example.com", UserRole.LEARNER)
    instructor = create_test_user(db_session, "instructor_comm@example.com", UserRole.INSTRUCTOR, first_name="Dr.", last_name="Kamal")
    cat = create_test_category(db_session, "Algorithms", "algo-comm")

    post = ForumPost(category_id=cat.id, author_id=learner.id, title="Dijkstra vs A* Algorithm", content="When is A* strictly better than Dijkstra?")
    db_session.add(post)
    db_session.commit()

    # Learner adds comment
    learner_headers = get_auth_headers(learner)
    res_learner = client.post(
        f"/api/v1/forum/posts/{post.id}/comments",
        json={"content": "I noticed A* uses a heuristic function h(n)."},
        headers=learner_headers,
    )
    assert res_learner.status_code == 201
    assert res_learner.json()["data"]["is_instructor_reply"] is False

    # Instructor adds comment
    instructor_headers = get_auth_headers(instructor)
    res_inst = client.post(
        f"/api/v1/forum/posts/{post.id}/comments",
        json={"content": "A* is optimal and faster whenever the heuristic is admissible and consistent."},
        headers=instructor_headers,
    )
    assert res_inst.status_code == 201
    inst_comment = res_inst.json()["data"]
    assert inst_comment["is_instructor_reply"] is True

    # Verify post detail now has has_instructor_reply=True and instructor_reply_name
    res_detail = client.get(f"/api/v1/forum/posts/{post.id}")
    detail_data = res_detail.json()["data"]
    assert detail_data["has_instructor_reply"] is True
    assert "Kamal" in detail_data["instructor_reply_name"]
    assert detail_data["replies_count"] == 2


def test_edit_own_post_success(client: TestClient, db_session: Session):
    user = create_test_user(db_session, "edit_owner@example.com", UserRole.LEARNER)
    cat = create_test_category(db_session, "Testing Cat", "test-edit")
    post = ForumPost(category_id=cat.id, author_id=user.id, title="Old Title", content="Original content here")
    db_session.add(post)
    db_session.commit()

    headers = get_auth_headers(user)
    res = client.put(
        f"/api/v1/forum/posts/{post.id}",
        json={"title": "Updated Discussion Title", "content": "Updated content with additional clarity"},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["data"]["title"] == "Updated Discussion Title"


def test_edit_post_unauthorized_user_forbidden(client: TestClient, db_session: Session):
    owner = create_test_user(db_session, "owner@example.com", UserRole.LEARNER)
    attacker = create_test_user(db_session, "attacker@example.com", UserRole.LEARNER)
    cat = create_test_category(db_session, "Security Cat", "sec-cat")
    post = ForumPost(category_id=cat.id, author_id=owner.id, title="Protected Post", content="Original content")
    db_session.add(post)
    db_session.commit()

    headers = get_auth_headers(attacker)
    res = client.put(
        f"/api/v1/forum/posts/{post.id}",
        json={"title": "Hacked Title"},
        headers=headers,
    )
    assert res.status_code == 403


def test_delete_own_post_success(client: TestClient, db_session: Session):
    user = create_test_user(db_session, "delete_owner@example.com", UserRole.LEARNER)
    cat = create_test_category(db_session, "Del Cat", "del-cat")
    post = ForumPost(category_id=cat.id, author_id=user.id, title="Post to Delete", content="Content to delete")
    db_session.add(post)
    db_session.commit()

    headers = get_auth_headers(user)
    res = client.delete(f"/api/v1/forum/posts/{post.id}", headers=headers)
    assert res.status_code == 200

    # Ensure it's gone
    res_check = client.get(f"/api/v1/forum/posts/{post.id}")
    assert res_check.status_code == 404


def test_admin_can_moderate_any_post_and_comment(client: TestClient, db_session: Session):
    admin = create_test_user(db_session, "admin_mod@example.com", UserRole.ADMIN)
    user = create_test_user(db_session, "user_mod@example.com", UserRole.LEARNER)
    cat = create_test_category(db_session, "Mod Cat", "mod-cat")
    post = ForumPost(category_id=cat.id, author_id=user.id, title="Inappropriate Post", content="Bad content")
    db_session.add(post)
    db_session.commit()

    admin_headers = get_auth_headers(admin)
    res = client.delete(f"/api/v1/forum/posts/{post.id}", headers=admin_headers)
    assert res.status_code == 200


def test_toggle_post_and_comment_likes(client: TestClient, db_session: Session):
    user = create_test_user(db_session, "like_user@example.com", UserRole.LEARNER)
    cat = create_test_category(db_session, "Like Cat", "like-cat")
    post = ForumPost(category_id=cat.id, author_id=user.id, title="Discussion to Like", content="Content here", likes_count=0)
    db_session.add(post)
    db_session.commit()

    comment = ForumComment(post_id=post.id, author_id=user.id, content="Comment to like", likes_count=0)
    db_session.add(comment)
    db_session.commit()

    headers = get_auth_headers(user)

    # Like post
    res_like = client.post(f"/api/v1/forum/posts/{post.id}/like", headers=headers)
    assert res_like.status_code == 200
    assert res_like.json()["data"]["is_liked"] is True
    assert res_like.json()["data"]["likes_count"] == 1

    # Unlike post
    res_unlike = client.post(f"/api/v1/forum/posts/{post.id}/like", headers=headers)
    assert res_unlike.status_code == 200
    assert res_unlike.json()["data"]["is_liked"] is False
    assert res_unlike.json()["data"]["likes_count"] == 0

    # Like comment
    res_comm_like = client.post(f"/api/v1/forum/comments/{comment.id}/like", headers=headers)
    assert res_comm_like.status_code == 200
    assert res_comm_like.json()["data"]["is_liked"] is True
    assert res_comm_like.json()["data"]["likes_count"] == 1


def test_report_inappropriate_content_and_admin_review(client: TestClient, db_session: Session):
    learner = create_test_user(db_session, "reporter@example.com", UserRole.LEARNER)
    admin = create_test_user(db_session, "admin_reviewer@example.com", UserRole.ADMIN)
    cat = create_test_category(db_session, "Report Cat", "report-cat")
    post = ForumPost(category_id=cat.id, author_id=learner.id, title="Reported Topic", content="Questionable material")
    db_session.add(post)
    db_session.commit()

    learner_headers = get_auth_headers(learner)
    report_payload = {
        "post_id": post.id,
        "reason": "Spam",
        "details": "Contains promotional affiliate links and spam content.",
    }
    res_report = client.post("/api/v1/forum/reports", json=report_payload, headers=learner_headers)
    assert res_report.status_code == 201
    report_id = res_report.json()["data"]["id"]

    # Admin reviews reports
    admin_headers = get_auth_headers(admin)
    res_list = client.get("/api/v1/forum/reports", headers=admin_headers)
    assert res_list.status_code == 200
    reports = res_list.json()["data"]
    assert any(r["id"] == report_id for r in reports)

    # Admin updates status to RESOLVED
    res_update = client.patch(
        f"/api/v1/forum/reports/{report_id}",
        json={"status": "RESOLVED"},
        headers=admin_headers,
    )
    assert res_update.status_code == 200
    assert res_update.json()["data"]["status"] == "RESOLVED"
