from pydantic import BaseModel
from models.mission import MissionStatus


# ─── Onboarding Chat (B2) ────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    """One turn in the conversation history sent from Flutter."""
    role: str   # "user" or "assistant"
    content: str


class OnboardingChatRequest(BaseModel):
    """
    Flutter sends the full conversation history plus the new user message.
    Stateless: backend reconstructs context every call.
    """
    messages: list[ChatMessage] = []   # previous turns (empty on first call)
    user_message: str                  # new user input


class OnboardingData(BaseModel):
    """Extracted after interview completes."""
    primary_goal: str      # e.g. "海外旅行"
    goal_detail: str       # e.g. "レストランで注文、ホテルチェックイン"
    english_level: str     # beginner | elementary | intermediate | upper_intermediate
    speaking_comfort: str  # comfortable | neutral | uncomfortable


class OnboardingChatResponse(BaseModel):
    assistant_message: str
    is_complete: bool
    extracted_data: OnboardingData | None  # populated only when is_complete=True


# ─── Mission Generation (B3) ─────────────────────────────────────────────────

class MissionGenerateRequest(BaseModel):
    """
    Sent after onboarding completes.
    Flutter passes the extracted_data from the final OnboardingChatResponse.
    """
    primary_goal: str
    goal_detail: str
    english_level: str
    speaking_comfort: str
    count: int = 3  # how many missions to generate (1–3)


# ─── Mission CRUD ────────────────────────────────────────────────────────────

class MissionResponse(BaseModel):
    mission_id: str
    user_id: str
    title_en: str
    title_ja: str
    description: str
    difficulty_level: int
    generated_content: dict
    status: MissionStatus

    class Config:
        from_attributes = True


class MissionStatusUpdate(BaseModel):
    status: MissionStatus