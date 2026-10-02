from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from app.models.token import RefreshToken, PasswordResetToken, EmailVerificationToken


class TokenRepository:
    """Repository handling database operations for refresh, password reset, and verification tokens."""

    @staticmethod
    def create_refresh_token(db: Session, user_id: int, token_hash: str, expires_at: datetime) -> RefreshToken:
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            revoked=False
        )
        db.add(token)
        db.commit()
        db.refresh(token)
        return token

    @staticmethod
    def get_active_refresh_token(db: Session, token_hash: str) -> Optional[RefreshToken]:
        now = datetime.now(timezone.utc)
        statement = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,
            RefreshToken.expires_at > now
        )
        return db.execute(statement).scalar_one_or_none()

    @staticmethod
    def revoke_refresh_token(db: Session, refresh_token: RefreshToken) -> None:
        refresh_token.revoked = True
        db.commit()

    @staticmethod
    def revoke_all_user_refresh_tokens(db: Session, user_id: int) -> None:
        statement = update(RefreshToken).where(RefreshToken.user_id == user_id).values(revoked=True)
        db.execute(statement)
        db.commit()

    @staticmethod
    def create_password_reset(db: Session, user_id: int, token_hash: str, expires_at: datetime) -> PasswordResetToken:
        record = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            used=False
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_valid_password_reset(db: Session, token_hash: str) -> Optional[PasswordResetToken]:
        now = datetime.now(timezone.utc)
        statement = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used == False,
            PasswordResetToken.expires_at > now
        )
        return db.execute(statement).scalar_one_or_none()

    @staticmethod
    def mark_password_reset_used(db: Session, reset_record: PasswordResetToken) -> None:
        reset_record.used = True
        db.commit()

    @staticmethod
    def create_email_verification(db: Session, user_id: int, token_hash: str, expires_at: datetime) -> EmailVerificationToken:
        record = EmailVerificationToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            used=False
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_valid_email_verification(db: Session, token_hash: str) -> Optional[EmailVerificationToken]:
        now = datetime.now(timezone.utc)
        statement = select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash,
            EmailVerificationToken.used == False,
            EmailVerificationToken.expires_at > now
        )
        return db.execute(statement).scalar_one_or_none()

    @staticmethod
    def mark_email_verification_used(db: Session, verification_record: EmailVerificationToken) -> None:
        verification_record.used = True
        db.commit()
