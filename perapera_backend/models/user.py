import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    String,
    Enum as SAEnum,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column
import enum

from core.database import Base


# ── Enum types (mirrors PostgreSQL ENUM columns) ──────────────────────────────

class AgeGroup(str, enum.Enum):
    under16     = "under16"
    high_school = "high_school"
    college     = "college"
    age_26_35   = "26_35"
    age_36_50   = "36_50"
    age_51_plus = "51_plus"


class EnglishLevel(str, enum.Enum):
    beginner           = "beginner"
    elementary         = "elementary"
    intermediate       = "intermediate"
    upper_intermediate = "upper_intermediate"


class UserStatus(str, enum.Enum):
    active  = "active"
    deleted = "deleted"


# ── Model ─────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(15), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(20), nullable=True)

    age_group: Mapped[AgeGroup] = mapped_column(
        SAEnum(AgeGroup, name="age_group_enum"), nullable=False
    )

    # Session tracking — set at registration based on age_group
    max_free_sessions: Mapped[int] = mapped_column(Integer, nullable=False)
    used_free_sessions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Set to True once user confirms their own OpenAI API key works
    api_key_registered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Set after onboarding interview
    english_level: Mapped[EnglishLevel | None] = mapped_column(
        SAEnum(EnglishLevel, name="english_level_enum"), nullable=True
    )
    primary_goal: Mapped[str | None] = mapped_column(String(500), nullable=True)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Abuse prevention (see Flow F3, F8)
    device_fingerprint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    referred_by: Mapped[str | None] = mapped_column(String(36), nullable=True)  # prepared for 1.2

    # Timestamps — always UTC
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Soft delete — never hard-delete users (see Flow F7)
    status: Mapped[UserStatus] = mapped_column(
        SAEnum(UserStatus, name="user_status_enum"),
        nullable=False,
        default=UserStatus.active,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Computed helpers (not DB columns) ────────────────────────────────────

    @property
    def remaining_sessions(self) -> int:
        return max(0, self.max_free_sessions - self.used_free_sessions)

    @property
    def can_practice(self) -> bool:
        return self.remaining_sessions > 0 or self.api_key_registered

    # ── Table-level constraints & indexes ─────────────────────────────────────
    # UNIQUE constraints on email/phone auto-create indexes.
    # Additional indexes below for common query patterns.

    __table_args__ = (
        Index("idx_users_status", "status"),
        Index("idx_users_created_at", "created_at"),
    )