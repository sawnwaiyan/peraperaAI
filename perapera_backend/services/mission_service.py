"""
mission_service.py
DB operations for missions.
Orchestrates: generate → save → return.
"""

import uuid
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.mission import Mission, MissionStatus
from models.user import User, EnglishLevel
from schemas.mission import MissionGenerateRequest
from services.onboarding_service import generate_missions_from_openai


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _level_str_to_enum(level: str) -> EnglishLevel | None:
    mapping = {
        "beginner": EnglishLevel.beginner,
        "elementary": EnglishLevel.elementary,
        "intermediate": EnglishLevel.intermediate,
        "upper_intermediate": EnglishLevel.upper_intermediate,
    }
    return mapping.get(level)


async def _update_user_profile(
    db: AsyncSession,
    user: User,
    primary_goal: str,
    english_level: str,
) -> None:
    """Write goal + level back to the users table after onboarding."""
    user.primary_goal = primary_goal
    level_enum = _level_str_to_enum(english_level)
    if level_enum:
        user.english_level = level_enum
    user.onboarding_completed = True
    user.last_active_at = datetime.now(timezone.utc)
    await db.commit()


# ─── Generate + Save ─────────────────────────────────────────────────────────

async def generate_and_save_missions(
    db: AsyncSession,
    user: User,
    req: MissionGenerateRequest,
) -> list[Mission]:
    """
    1. Call OpenAI to generate missions
    2. Persist each mission to DB
    3. Update user profile (goal + level + onboarding_completed)
    4. Return the saved Mission objects
    """
    count = max(1, min(req.count, 3))  # clamp 1–3

    raw_missions = await generate_missions_from_openai(
        primary_goal=req.primary_goal,
        goal_detail=req.goal_detail,
        english_level=req.english_level,
        speaking_comfort=req.speaking_comfort,
        count=count,
    )

    saved: list[Mission] = []
    for raw in raw_missions:
        mission = Mission(
            mission_id=str(uuid.uuid4()),
            user_id=user.user_id,
            title_en=raw.get("title_en", ""),
            title_ja=raw.get("title_ja", ""),
            description=raw.get("description", ""),
            difficulty_level=int(raw.get("difficulty_level", 2)),
            generated_content={
                "key_phrases":       raw.get("key_phrases", []),
                "vocabulary":        raw.get("vocabulary", []),
                "dialogue_preview":  raw.get("dialogue_preview", []),
                "objectives":        raw.get("objectives", []),
                "ai_role":           raw.get("ai_role", ""),
                "user_role":         raw.get("user_role", ""),
                "system_prompt":     raw.get("system_prompt", ""),
            },
        )
        db.add(mission)
        saved.append(mission)

    await _update_user_profile(db, user, req.primary_goal, req.english_level)
    await db.commit()

    # Refresh each object so JSONB fields load correctly
    for m in saved:
        await db.refresh(m)

    return saved


# ─── CRUD ────────────────────────────────────────────────────────────────────

async def get_user_missions(db: AsyncSession, user_id: str) -> list[Mission]:
    result = await db.execute(
        select(Mission)
        .where(Mission.user_id == user_id)
        .order_by(Mission.created_at)
    )
    return list(result.scalars().all())


async def get_mission_by_id(
    db: AsyncSession, mission_id: str, user_id: str
) -> Mission:
    result = await db.execute(
        select(Mission).where(
            Mission.mission_id == mission_id,
            Mission.user_id == user_id,
        )
    )
    mission = result.scalar_one_or_none()
    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ミッションが見つかりません",
        )
    return mission


async def update_mission_status(
    db: AsyncSession,
    mission: Mission,
    new_status: MissionStatus,
) -> Mission:
    mission.status = new_status
    if new_status == MissionStatus.completed:
        mission.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(mission)
    return mission