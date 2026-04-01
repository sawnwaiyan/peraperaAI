from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from core.exceptions import (
    DuplicateEmailError,
    DuplicatePhoneError,
    InvalidCredentialsError,
)
from models.user import User, AgeGroup
from schemas.user import UserRegisterRequest
from utils.validators import detect_identifier_type
from utils.phone_formatter import normalize_phone

settings = get_settings()

# Age groups that receive the student free-session quota
STUDENT_GROUPS = {AgeGroup.under16, AgeGroup.high_school, AgeGroup.college}


# ── Register ─────────────────────────────────────────────────────────────────

async def register_user(db: AsyncSession, data: UserRegisterRequest) -> User:
    """
    Create a new user account.

    Checks:
      1. Email must be globally unique.
      2. Phone must be globally unique.
      3. Age group determines free session quota (5 adult / 10 student).

    Raises:
      DuplicateEmailError  — 409
      DuplicatePhoneError  — 409
    """
    # 1. Email uniqueness
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise DuplicateEmailError()

    # 2. Phone uniqueness (phone is already normalised by Pydantic validator)
    existing = await db.execute(select(User).where(User.phone == data.phone))
    if existing.scalar_one_or_none():
        raise DuplicatePhoneError()

    # 3. Session quota
    max_sessions = (
        settings.free_sessions_student
        if data.age_group in STUDENT_GROUPS
        else settings.free_sessions_adult
    )

    user = User(
        email=data.email,
        phone=data.phone,
        password_hash=hash_password(data.password),
        display_name=data.display_name,
        age_group=data.age_group,
        max_free_sessions=max_sessions,
        device_fingerprint=data.device_fingerprint,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# ── Login ────────────────────────────────────────────────────────────────────

async def login_user(db: AsyncSession, identifier: str, password: str) -> dict:
    """
    Accepts email OR Japanese mobile number as identifier.
    Returns access + refresh token pair.

    Raises:
      InvalidCredentialsError — 401 (same message for wrong id or wrong password
                                     — prevents user enumeration)
    """
    id_type = detect_identifier_type(identifier)

    if id_type == "email":
        stmt = select(User).where(User.email == identifier)
    else:
        normalised = normalize_phone(identifier)
        stmt = select(User).where(User.phone == normalised)

    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError()

    return {
        "access_token": create_access_token(user.user_id),
        "refresh_token": create_refresh_token(user.user_id),
        "token_type": "bearer",
    }


# ── Token Refresh ─────────────────────────────────────────────────────────────

async def refresh_tokens(refresh_token: str) -> dict:
    """
    Issue a fresh access + refresh token pair from a valid refresh token.

    Raises:
      InvalidCredentialsError — 401
    """
    payload = verify_refresh_token(refresh_token)
    if payload is None:
        raise InvalidCredentialsError()

    return {
        "access_token": create_access_token(payload["sub"]),
        "refresh_token": create_refresh_token(payload["sub"]),
        "token_type": "bearer",
    }


# ── Helpers (used by dependencies.py) ─────────────────────────────────────────

async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(select(User).where(User.user_id == user_id))
    return result.scalar_one_or_none()