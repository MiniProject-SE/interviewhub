"""Company catalogue shared by experiences and the question bank.

Owner: Member 2 (Experiences). Kept in its own package so that both the
experiences and questions modules depend on it without depending on
each other.
"""
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    sector: Mapped[str | None] = mapped_column(String(80), nullable=True)
