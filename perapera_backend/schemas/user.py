from pydantic import BaseModel, EmailStr, field_validator
from models.user import AgeGroup, EnglishLevel
import re


# ── Registration ─────────────────────────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    email: EmailStr
    phone: str
    password: str
    age_group: AgeGroup
    display_name: str | None = None
    device_fingerprint: str | None = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Accept 090-1234-5678, 09012345678, +819012345678 — normalise to +81 format."""
        digits = re.sub(r"[\s\-]", "", v)
        if digits.startswith("+81"):
            local = "0" + digits[3:]
        else:
            local = digits

        if not re.match(r"^0[789]0\d{8}$", local):
            raise ValueError("正しい携帯電話番号を入力してください（070/080/090 で始まる11桁）")

        return "+81" + local[1:]   # stored as +819012345678

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("パスワードは8文字以上で入力してください")
        return v

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, v: str | None) -> str | None:
        if v is not None and len(v) > 20:
            raise ValueError("ニックネームは20文字以内で入力してください")
        return v


# ── Response ─────────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    user_id: str
    email: str
    display_name: str | None
    age_group: AgeGroup
    max_free_sessions: int
    used_free_sessions: int
    remaining_sessions: int        # computed: max - used
    api_key_registered: bool
    onboarding_completed: bool

    model_config = {"from_attributes": True}


# ── Profile update (used in /me PATCH — Week 4) ───────────────────────────────

class UserProfileUpdate(BaseModel):
    display_name: str | None = None
    english_level: EnglishLevel | None = None
    primary_goal: str | None = None
    onboarding_completed: bool | None = None
    api_key_registered: bool | None = None