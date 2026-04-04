import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
import enum

from core.database import Base


class MissionStatus(str, enum.Enum):
    available = "available"
    in_progress = "in_progress"
    completed = "completed"


class Mission(Base):
    __tablename__ = "missions"

    mission_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.user_id"), nullable=False, index=True
    )
    title_en: Mapped[str] = mapped_column(String(255))
    title_ja: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    difficulty_level: Mapped[int] = mapped_column(Integer)  # 1–5
    generated_content: Mapped[dict] = mapped_column(JSONB)
    # generated_content shape:
    # {
    #   key_phrases:    [{en, ja}, ...]
    #   vocabulary:     [{word, pronunciation_hint, ja}, ...]
    #   dialogue_preview: [{speaker: "ai"|"user_example", text}, ...]
    #   objectives:     [str, ...]
    #   ai_role:        str
    #   user_role:      str
    #   system_prompt:  str   ← used during Practice phase
    # }
    status: Mapped[MissionStatus] = mapped_column(
        SAEnum(MissionStatus, name="mission_status_enum"),
        default=MissionStatus.available,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )