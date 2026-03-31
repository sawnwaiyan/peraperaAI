from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.orm import DeclarativeBase

from config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,   # logs SQL in dev when DEBUG=true
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # keeps model attributes accessible after commit
)


class Base(DeclarativeBase):
    """
    All SQLAlchemy models inherit from this Base.
    Alembic reads Base.metadata to auto-generate migrations.
    """
    pass