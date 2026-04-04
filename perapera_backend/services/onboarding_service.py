"""
onboarding_service.py
Handles two OpenAI calls:
  1. onboarding interview chat (B2) — multi-turn, stateless
  2. mission generation (B3)        — single call, returns JSON array

Both always use the developer's OPENAI_DEV_API_KEY (free sessions).
"""

import json
import re
import httpx
from fastapi import HTTPException, status

from config import get_settings
from schemas.mission import (
    OnboardingChatRequest,
    OnboardingChatResponse,
    OnboardingData,
)

settings = get_settings()

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-4o-mini"

# ─── Prompts ─────────────────────────────────────────────────────────────────

INTERVIEW_SYSTEM_PROMPT = """\
You are a friendly interview assistant for PeraperaAI, a Japanese English learning app.
Interview the user in Japanese to learn their goal and English level. Follow these steps IN ORDER:

STEP 1 — Goal
Ask: 「英語を使いたい場面はどんなところですか？」
(Offer examples: 海外旅行 / 仕事・ビジネス / 留学準備 / 日常会話 / 試験対策)

STEP 2 — Goal detail
Based on their answer, ask one follow-up to narrow down the specific situation.
Example if travel: 「レストランで注文？ホテルのチェックイン？道を聞く？」

STEP 3 — Level check (switch to English for THIS message only)
Say in English: "By the way, can you tell me a little about yourself in English? \
Just 1–2 sentences is fine! 😊"
Add Japanese hint below: 「簡単な英語で自己紹介してみてください！」
Internally assess their reply → map to: beginner / elementary / intermediate / upper_intermediate
  beginner:           very simple phrases, many errors, tiny vocabulary
  elementary:         basic sentences, clear errors, limited vocabulary
  intermediate:       decent sentences, some errors, reasonable vocabulary
  upper_intermediate: complex sentences, few errors, good vocabulary

STEP 4 — Comfort check (back to Japanese)
Ask: 「英語を声に出して練習するのは得意ですか？苦手ですか？」
(Hints: 「得意！」「まあまあ」「苦手…」)

STEP 5 — Summary
Summarise in Japanese: goal + level impression + say missions are being prepared.
Example: 「わかりました！海外旅行での英語を練習しましょう。初中級レベルに合わせたミッションを作りますね！」

RULES:
- Stay in Japanese except Step 3
- Be warm and encouraging; keep replies to 2–4 sentences
- Do NOT skip or reorder steps
- Do NOT add the completion signal until AFTER step 5 summary

COMPLETION SIGNAL — output exactly this after your Step 5 message, on its own line:
__INTERVIEW_COMPLETE__
{"primary_goal":"<goal>","goal_detail":"<detail>","english_level":"<level>","speaking_comfort":"<comfortable|neutral|uncomfortable>"}
"""

MISSION_GENERATION_SYSTEM_PROMPT = """\
You are a mission designer for PeraperaAI, a Japanese English learning app.
Generate English practice missions tailored to the user profile below.

OUTPUT: Return ONLY a valid JSON array — no markdown, no preamble, no explanation.

Each mission object:
{
  "title_en": "Short English title (max 8 words)",
  "title_ja": "Japanese translation",
  "description": "Scene description in Japanese (2–3 sentences, sets the scene vividly)",
  "difficulty_level": <1–5 integer>,
  "key_phrases": [{"en": "phrase", "ja": "translation"}, ...],
  "vocabulary": [{"word": "word", "pronunciation_hint": "katakana + IPA", "ja": "translation"}, ...],
  "dialogue_preview": [{"speaker": "ai", "text": "..."}, {"speaker": "user_example", "text": "..."}, ...],
  "objectives": ["objective in English", ...],
  "ai_role": "AI character description in English",
  "user_role": "User role description in Japanese",
  "system_prompt": "Full English system prompt for the AI character during role-play (3–5 sentences, \
sets personality + constraints)"
}

DIFFICULTY GUIDE:
  beginner → 1–2   (very short sentences, basic vocab, slow pace)
  elementary → 2–3
  intermediate → 3–4
  upper_intermediate → 4–5

QUALITY RULES:
- Scenarios must feel real and specific (not generic)
- key_phrases: 4–6, directly useful for the scenario
- vocabulary: 5–8 words the user WILL encounter
- dialogue_preview: 3–4 exchanges showing realistic flow
- objectives: 2–4 concrete tasks the user must complete
- system_prompt: make the AI character behave realistically (correct pace, helpful hints if stuck)
"""


# ─── Helpers ─────────────────────────────────────────────────────────────────

async def _call_openai(messages: list[dict], max_tokens: int = 800) -> str:
    """Raw OpenAI call using developer key. Returns the assistant text."""
    headers = {
        "Authorization": f"Bearer {settings.openai_dev_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(OPENAI_CHAT_URL, headers=headers, json=payload)

    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenAI APIエラー: {resp.status_code}",
        )
    return resp.json()["choices"][0]["message"]["content"]


def _parse_completion(text: str) -> tuple[str, OnboardingData | None]:
    """
    Splits the AI reply into (clean_message, extracted_data | None).
    Looks for __INTERVIEW_COMPLETE__ marker followed by a JSON line.
    """
    marker = "__INTERVIEW_COMPLETE__"
    if marker not in text:
        return text.strip(), None

    parts = text.split(marker, 1)
    clean_message = parts[0].strip()
    json_part = parts[1].strip()

    # Extract first JSON object from whatever follows the marker
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
    messages: list[dict] = [{"role": "system", "content": INTERVIEW_SYSTEM_PROMPT}]

    # Replay history
    for msg in req.messages:
        messages.append({"role": msg.role, "content": msg.content})

    # Append new user message
    messages.append({"role": "user", "content": req.user_message})

    raw = await _call_openai(messages, max_tokens=600)
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
    Call GPT to generate `count` missions. Returns raw list of dicts.
    Caller (mission_service) persists them to DB.
    """
    user_prompt = (
        f"User profile:\n"
        f"- Primary goal: {primary_goal}\n"
        f"- Goal detail: {goal_detail}\n"
        f"- English level: {english_level}\n"
        f"- Speaking comfort: {speaking_comfort}\n\n"
        f"Generate exactly {count} missions as a JSON array."
    )
    messages = [
        {"role": "system", "content": MISSION_GENERATION_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    raw = await _call_openai(messages, max_tokens=2000)

    # Strip any accidental markdown fences
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