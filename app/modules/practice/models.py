"""Mock interview sessions. Owner: Member 4 (Mock Interview & Performance)."""
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.auth.models import utcnow
from app.modules.questions.models import Question

SESSION_STATES = ("in_progress", "completed", "expired")


class PracticeSession(Base):
    __tablename__ = "practice_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role_title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    company: Mapped[str | None] = mapped_column(String(120), nullable=True)
    topic: Mapped[str | None] = mapped_column(String(40), nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    state: Mapped[str] = mapped_column(String(20), default="in_progress")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    items: Mapped[list["SessionItem"]] = relationship(
        back_populates="session", cascade="all, delete-orphan",
        order_by="SessionItem.position", lazy="selectin")


class SessionItem(Base):
    __tablename__ = "session_items"
    __table_args__ = (UniqueConstraint("session_id", "question_id", name="uq_session_question"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("practice_sessions.id", ondelete="CASCADE"))
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    position: Mapped[int] = mapped_column(Integer)
    answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    self_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time_taken_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    auto_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    final_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    session: Mapped[PracticeSession] = relationship(back_populates="items")
    question: Mapped[Question] = relationship(lazy="joined")
