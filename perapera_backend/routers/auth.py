from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db
from schemas.auth import TokenResponse, LoginRequest, RefreshRequest
from schemas.user import UserRegisterRequest, UserResponse
from services.auth_service import register_user, login_user, refresh_tokens
from models.user import User

router = APIRouter()


# ── POST /register ────────────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="新規ユーザー登録",
    description=(
        "メールアドレス・携帯電話番号・パスワード・年齢グループでアカウントを作成します。"
        "年齢グループに応じて無料練習回数が決まります（学生: 10回 / 社会人: 5回）。"
    ),
)
async def register(
    body: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    user: User = await register_user(db, body)
    return _to_response(user)


# ── POST /login ───────────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="ログイン",
    description=(
        "メールアドレスまたは携帯電話番号とパスワードでログインします。"
        "アクセストークン（60分）とリフレッシュトークン（30日）を返します。"
    ),
)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    tokens = await login_user(db, body.identifier, body.password)
    return TokenResponse(**tokens)


# ── POST /refresh ─────────────────────────────────────────────────────────────

@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="トークン更新",
    description="リフレッシュトークンを使って新しいアクセストークンを取得します。",
)
async def refresh(body: RefreshRequest) -> TokenResponse:
    tokens = await refresh_tokens(body.refresh_token)
    return TokenResponse(**tokens)


# ── Helper ─────────────────────────────────────────────────────────────────────

def _to_response(user: User) -> UserResponse:
    return UserResponse(
        user_id=user.user_id,
        email=user.email,
        display_name=user.display_name,
        age_group=user.age_group,
        max_free_sessions=user.max_free_sessions,
        used_free_sessions=user.used_free_sessions,
        remaining_sessions=user.max_free_sessions - user.used_free_sessions,
        api_key_registered=user.api_key_registered,
        onboarding_completed=user.onboarding_completed,
    )