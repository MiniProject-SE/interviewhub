"""Question bank model. Owner: Member 3 (Question Bank & AI Suggestions)."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.auth.models import utcnow
from app.modules.companies.models import Company

DIFFICULTIES = ("easy", "medium", "hard")
TOPICS = (
    "dsa", "dbms", "os", "networks", "oop", "system-design", "ml", "web",
    "behavioral", "hr", "aptitude", "language", "other",
)


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    topic: Mapped[str] = mapped_column(String(40), index=True)
    difficulty: Mapped[str] = mapped_column(String(10), default="medium")
    role_title: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    tags: Mapped[str] = mapped_column(String(255), default="")
    # Reference answer / key points; used by the practice module's auto-scorer.
    model_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True, index=True)
    source_experience_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    times_asked: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    company: Mapped[Company | None] = relationship(lazy="joined")
