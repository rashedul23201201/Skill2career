from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.user import User


class UserRepository:
    """Repository handling all database operations for User entity."""

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        """Retrieve a user by primary key ID."""
        statement = select(User).where(User.id == user_id)
        return db.execute(statement).scalar_one_or_none()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """Retrieve a user by email address (case-insensitive)."""
        statement = select(User).where(User.email == email.strip().lower())
        return db.execute(statement).scalar_one_or_none()

    @staticmethod
    def create(db: Session, user: User) -> User:
        """Persist a new user to the database and refresh attributes."""
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update(db: Session, user: User) -> User:
        """Save updates to an existing user."""
        db.commit()
        db.refresh(user)
        return user
