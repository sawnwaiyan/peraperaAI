"""
onboarding_service.py
Handles two Gemini calls:
  1. onboarding interview chat (B2) — multi-turn, stateless
  2. mission generation (B3)        — single call, returns JSON array

Uses the official google-genai SDK (same as Google's sample code).
"""

import json
import re
from fastapi import HTTPException, status
from google import genai
from google.genai import types

from config import get_settings
from schemas.mission import (
    OnboardingChatRequest,
    OnboardingChatResponse,
    OnboardingData,
)

settings = get_settings()

MODEL = "gemini-2.5-flash-lite"

# ─── Prompts ─────────────────────────────────────────────────────────────────

INTERVIEW_SYSTEM_PROMPT = """\
You are a friendly interview assistant for PeraperaAI, a Japanese English learning app.
Interview the user in Japanese to learn their goal and English level.

Follow these 5 steps IN ORDER. Complete every step exactly once, then stop.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1 — Goal detection
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ask: 「英語を使いたい場面はどんなところですか？」
Offer examples: 海外旅行 / 仕事・ビジネス / 留学準備 / 日常会話 / 試験対策

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 2 — Goal narrowing
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ask one follow-up to find the specific situation.
Example if travel: 「レストランで注文？ホテルのチェックイン？道を聞く？」

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 3 — English level check  ← switch to English for THIS message only
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Say exactly: "By the way, can you tell me a little about yourself in English? Just 1-2 sentences is fine!"
Add below: 「簡単な英語で自己紹介してみてください！」

Internally map their reply to ONE of: beginner / elementary / intermediate / upper_intermediate
  beginner:           very simple phrases, many errors, tiny vocabulary
  elementary:         basic sentences, clear errors, limited vocabulary
  intermediate:       decent sentences, some errors, reasonable vocabulary
  upper_intermediate: complex sentences, few errors, good vocabulary

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 4 — Speaking comfort  ← back to Japanese
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ask: 「英語を声に出して練習するのは得意ですか？苦手ですか？」
Hints: 「得意！」「まあまあ」「苦手…」
Map answer to: comfortable / neutral / uncomfortable

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 5 — Summary + REQUIRED completion output
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Write a warm 2-3 sentence Japanese summary of: goal + level impression + missions incoming.
Example: 「わかりました！海外旅行での英語を練習しましょう。初中級レベルに合わせたミッションを作りますね！」

Then, ON THE VERY NEXT LINE with NO other text between them, output the completion block:

__INTERVIEW_COMPLETE__
{"primary_goal":"<goal>","goal_detail":"<detail>","english_level":"<level>","speaking_comfort":"<comfortable|neutral|uncomfortable>"}

The completion block is MANDATORY. Step 5 is not finished until you output it.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GENERAL RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Stay in Japanese for all steps except Step 3
- Be warm and encouraging; keep each reply to 2-4 sentences
- Do NOT skip or reorder steps
- Do NOT output __INTERVIEW_COMPLETE__ before Step 5
- Do NOT add any text after the JSON on the completion line
"""

MISSION_GENERATION_SYSTEM_PROMPT = """\
You are a mission designer for PeraperaAI, a Japanese English learning app.
Generate English practice missions tailored to the user profile below.

OUTPUT: Return ONLY a valid JSON array — no markdown, no preamble, no explanation.

Each mission object:
{
  "title_en": "Short English title (max 8 words)",
  "title_ja": "Japanese translation",
  "description": "Scene description in Japanese (2-3 sentences, sets the scene vividly)",
  "difficulty_level": <1-5 integer>,
  "key_phrases": [{"en": "phrase", "ja": "translation"}, ...],
  "vocabulary": [{"word": "word", "pronunciation_hint": "katakana + IPA", "ja": "translation"}, ...],
  "dialogue_preview": [{"speaker": "ai", "text": "..."}, {"speaker": "user_example", "text": "..."}, ...],
  "objectives": ["objective in English", ...],
  "ai_role": "AI character description in English",
  "user_role": "User role description in Japanese",
  "system_prompt": "Full English system prompt for the AI character during role-play (3-5 sentences)"
}

DIFFICULTY GUIDE:
  beginner -> 1-2   (very short sentences, basic vocab, slow pace)
  elementary -> 2-3
  intermediate -> 3-4
  upper_intermediate -> 4-5

QUALITY RULES:
- Scenarios must feel real and specific (not generic)
- key_phrases: 4-6, directly useful for the scenario
- vocabulary: 5-8 words the user WILL encounter
- dialogue_preview: 3-4 exchanges showing realistic flow
- objectives: 2-4 concrete tasks the user must complete
- system_prompt: make the AI character behave realistically
"""


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _build_contents(messages: list[dict]) -> list[types.Content]:
    """
    Convert message dicts to Gemini SDK Content objects.
    Skips system messages (passed separately via config).
    Gemini uses "model" instead of "assistant".
    """
    contents = []
    for msg in messages:
        if msg["role"] == "system":
            continue
        role = "model" if msg["role"] == "assistant" else "user"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part(text=msg["content"])],
            )
        )
    return contents


async def _call_gemini(
    messages: list[dict],
    system_prompt: str,
    max_tokens: int = 800,
) -> str:
    """
    Call Gemini using the official google-genai SDK.
    system_prompt is passed separately via GenerateContentConfig.
    """
    client = genai.Client(api_key=settings.gemini_api_key)
    contents = _build_contents(messages)

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        max_output_tokens=max_tokens,
        temperature=0.7,
    )

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=config,
        )
        return response.text
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini APIエラー: {str(e)}",
        )


def _parse_completion(text: str) -> tuple[str, OnboardingData | None]:
    """
    Splits the AI reply into (clean_message, extracted_data | None).
    Looks for __INTERVIEW_COMPLETE__ marker followed by a JSON object.
    """
    marker = "__INTERVIEW_COMPLETE__"
    if marker not in text:
        return text.strip(), None

    parts = text.split(marker, 1)
    clean_message = parts[0].strip()
    json_part = parts[1].strip()

    match = re.search(r"\{.*\}", json_part, re.DOTALL)
    if not match:
        return clean_message, None

    try:
        data = json.loads(match.group())
        return clean_message, OnboardingData(**data)
    except (json.JSONDecodeError, Exception):
        return clean_message, None


# ─── Public API ──────────────────────────────────────────────────────────────

async def run_interview_turn(req: OnboardingChatRequest) -> OnboardingChatResponse:
    """Single turn of the onboarding interview (B2). Client calls repeatedly."""
    messages: list[dict] = []

    for msg in req.messages:
        messages.append({"role": msg.role, "content": msg.content})

    messages.append({"role": "user", "content": req.user_message})

    raw = await _call_gemini(
        messages=messages,
        system_prompt=INTERVIEW_SYSTEM_PROMPT,
        max_tokens=600,
    )
    clean, extracted = _parse_completion(raw)

    return OnboardingChatResponse(
        assistant_message=clean,
        is_complete=extracted is not None,
        extracted_data=extracted,
    )


async def generate_missions_from_openai(
    primary_goal: str,
    goal_detail: str,
    english_level: str,
    speaking_comfort: str,
    count: int,
) -> list[dict]:
    """
    Generate `count` missions via Gemini. Returns raw list of dicts.
    Caller (mission_service) persists them to DB.
    Function name kept as-is to avoid changing mission_service.py.
    """
    user_prompt = (
        f"User profile:\n"
        f"- Primary goal: {primary_goal}\n"
        f"- Goal detail: {goal_detail}\n"
        f"- English level: {english_level}\n"
        f"- Speaking comfort: {speaking_comfort}\n\n"
        f"Generate exactly {count} missions as a JSON array."
    )
    messages = [{"role": "user", "content": user_prompt}]

    raw = await _call_gemini(
        messages=messages,
        system_prompt=MISSION_GENERATION_SYSTEM_PROMPT,
        max_tokens=8192,
    )

    cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
    try:
        missions = json.loads(cleaned)
        if not isinstance(missions, list):
            raise ValueError("Expected a JSON array")
        return missions
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"ミッション生成のJSONパースに失敗しました: {e}",
        )