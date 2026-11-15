"""Database engine, session factory and declarative base (SQLAlchemy 2.x)."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for every ORM model in every module."""


def _make_engine(url: str):
    kwargs = {}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


engine = _make_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    """FastAPI dependency yielding a request-scoped session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(bind=None) -> None:
    """Create all tables. Importing the model modules registers them on Base."""
    from app.modules.auth import models as _a  # noqa: F401
    from app.modules.companies import models as _c  # noqa: F401
    from app.modules.questions import models as _q  # noqa: F401

    Base.metadata.create_all(bind=bind or engine)
