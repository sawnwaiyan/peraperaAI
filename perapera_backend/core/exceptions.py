from fastapi import HTTPException, status


class DuplicateEmailError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="このメールアドレスは既に登録されています",
        )


class DuplicatePhoneError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="この電話番号は既に登録されています",
        )


class InvalidCredentialsError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="メールアドレス（電話番号）またはパスワードが正しくありません",
        )


class NoFreeSessionsError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="無料セッションを使い切りました。APIキーを登録してください。",
        )


class AccountDeletedError(HTTPException):
    """Raised when a previously deleted email/phone tries to re-register."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="このアカウントは削除されています。再登録はできません。",
        )