"""
routers/missions.py
Endpoints:
  POST /onboarding/chat       — B2: single interview turn
  POST /generate              — B3: generate + save missions from onboarding data
  GET  /                      — list user's missions
  GET  /{mission_id}          — single mission
  PATCH/{mission_id}/status   — update in_progress / completed
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db, get_current_user
from models.user import User
from schemas.mission import (
    OnboardingChatRequest,
    OnboardingChatResponse,
    MissionGenerateRequest,
    MissionResponse,
    MissionStatusUpdate,
)
from services.onboarding_service import run_interview_turn
from services.mission_service import (
    generate_and_save_missions,
    get_user_missions,
    get_mission_by_id,
    update_mission_status,
)

router = APIRouter()


# ─── B2: Onboarding interview ────────────────────────────────────────────────

@router.post(
    "/onboarding/chat",
    response_model=OnboardingChatResponse,
    summary="Single turn of the AI onboarding interview (B2)",
)
async def onboarding_chat(
    body: OnboardingChatRequest,
    current_user: User = Depends(get_current_user),
    # db not needed — pure LLM call; profile is updated in /generate
):
    """
    Stateless: Flutter sends full message history + new user_message each call.
    Returns the AI reply and, on the final turn, is_complete=True and extracted_data.

    Swagger test flow:
      Call 1: messages=[], user_message="海外旅行"
      Call 2: messages=[{...turn1...}], user_message="レストランで注文したい"
      Call 3: messages=[...], user_message="My name is Taro. I study English."
      Call 4: messages=[...], user_message="苦手です…"
      → is_complete: true, extracted_data populated
    """
    return await run_interview_turn(body)


# ─── B3: Mission generation ──────────────────────────────────────────────────

@router.post(
    "/generate",
    response_model=list[MissionResponse],
    status_code=201,
    summary="Generate and save missions after onboarding (B3)",
)
async def generate_missions(
    body: MissionGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Flutter calls this once after /onboarding/chat returns is_complete=True.
    Pass extracted_data fields directly as the request body.
    Saves 1–3 missions to DB and marks onboarding_completed=True on the user.

    Swagger test:
      {
        "primary_goal": "海外旅行",
        "goal_detail": "レストランで注文、ホテルチェックイン",
        "english_level": "beginner",
        "speaking_comfort": "uncomfortable",
        "count": 3
      }
    """
    missions = await generate_and_save_missions(db, current_user, body)
    return [
        MissionResponse(
            mission_id=m.mission_id,
            user_id=m.user_id,
            title_en=m.title_en,
            title_ja=m.title_ja,
            description=m.description,
            difficulty_level=m.difficulty_level,
            generated_content=m.generated_content,
            status=m.status,
        )
        for m in missions
    ]


# ─── Mission CRUD ────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=list[MissionResponse],
    summary="List all missions for current user (D1 Home screen)",
)
async def list_missions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    missions = await get_user_missions(db, current_user.user_id)
    return [
        MissionResponse(
            mission_id=m.mission_id,
            user_id=m.user_id,
            title_en=m.title_en,
            title_ja=m.title_ja,
            description=m.description,
            difficulty_level=m.difficulty_level,
            generated_content=m.generated_content,
            status=m.status,
        )
        for m in missions
    ]


@router.get(
    "/{mission_id}",
    response_model=MissionResponse,
    summary="Get a single mission by ID (C1 Briefing screen)",
)
async def get_mission(
    mission_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    m = await get_mission_by_id(db, mission_id, current_user.user_id)
    return MissionResponse(
        mission_id=m.mission_id,
        user_id=m.user_id,
        title_en=m.title_en,
        title_ja=m.title_ja,
        description=m.description,
        difficulty_level=m.difficulty_level,
        generated_content=m.generated_content,
        status=m.status,
    )


@router.patch(
    "/{mission_id}/status",
    response_model=MissionResponse,
    summary="Update mission status (in_progress / completed)",
)
async def patch_mission_status(
    mission_id: str,
    body: MissionStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Flutter calls this at:
      - Practice start  → status: "in_progress"
      - Review complete → status: "completed"  (session counter decremented separately)
    """
    m = await get_mission_by_id(db, mission_id, current_user.user_id)
    m = await update_mission_status(db, m, body.status)
    return MissionResponse(
        mission_id=m.mission_id,
        user_id=m.user_id,
        title_en=m.title_en,
        title_ja=m.title_ja,
        description=m.description,
        difficulty_level=m.difficulty_level,
        generated_content=m.generated_content,
        status=m.status,
    )