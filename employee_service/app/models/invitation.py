# import secrets
# from datetime import UTC, datetime, timedelta
# from enum import Enum
# from typing import Optional
# from uuid import uuid4

# from app.models.base import BaseModel
# from sqlalchemy import DateTime, String, Text
# from sqlalchemy.orm import Mapped, mapped_column


# class InvitationStatus(str, Enum):
#     PENDING = "pending"
#     ACCEPTED = "accepted"
#     EXPIRED = "expired"
#     REVOKED = "revoked"


# class Invitation(BaseModel):
#     """
#     Invitation records for new employees
#     Stores invitation tokens and tracks status
#     """

#     __tablename__ = "invitations"

#     id: Mapped[str] = mapped_column(
#         String(36), primary_key=True, default=lambda: str(uuid4())
#     )

#     # Who is being invited
#     employee_id: Mapped[str] = mapped_column(
#         String(36), nullable=False, unique=True, index=True
#     )
#     email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

#     # Invitation token (URL-safe, cryptographically secure)
#     token: Mapped[str] = mapped_column(
#         String(100), unique=True, nullable=False, index=True
#     )

#     # Token expiry
#     expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

#     # Invitation status
#     status: Mapped[InvitationStatus] = mapped_column(
#         Enum(InvitationStatus), default=InvitationStatus.PENDING
#     )

#     # Who sent the invitation
#     invited_by: Mapped[str] = mapped_column(String(36), nullable=False)

#     # When was it accepted
#     accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

#     # Notes
#     notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

#     # Timestamps
#     created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(UTC))
#     updated_at: Mapped[datetime] = mapped_column(
#         DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC)
#     )

#     @staticmethod
#     def generate_token() -> str:
#         """Generate secure random token"""
#         return secrets.token_urlsafe(32)

#     @staticmethod
#     def get_expiry(hours: int = 48) -> datetime:
#         """Get expiry datetime (default 48 hours)"""
#         return datetime.now(UTC) + timedelta(hours=hours)

#     def is_valid(self) -> bool:
#         """Check if invitation is still valid"""
#         return (
#             self.status == InvitationStatus.PENDING
#             and self.expires_at > datetime.now(UTC)
#         )
