from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal
from core.security import verify_access_token

security_scheme = HTTPBearer()


# ── Database session ──────────────────────────────────────────────────────────

async def get_db():
    """
    Yields an async SQLAlchemy session, then closes it.
    Use as: db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# ── Authenticated user ────────────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    Validates the Bearer JWT from the Authorization header.
    Returns the User ORM object, or raises 401.

    Usage:
        @router.get("/me")
        async def me(user = Depends(get_current_user)):
            ...
    """
    token_data = verify_access_token(credentials.credentials)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効なトークンです",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Import here to avoid circular imports at module load time
    from services.auth_service import get_user_by_id

    user = await get_user_by_id(db, token_data["sub"])
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザーが見つかりません",
        )
    return user