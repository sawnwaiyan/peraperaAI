from pydantic import BaseModel


# ── Tokens ──────────────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# ── Login ────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    """
    Single identifier field — app sends either email or phone number.
    Backend auto-detects which one it is via utils/validators.py.
    """
    identifier: str   # email OR Japanese mobile number
    password: str