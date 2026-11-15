"""Interview experience models. Owner: Member 2 (Experiences & Companies)."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.auth.models import User, utcnow
from app.modules.companies.models import Company

OUTCOMES = ("selected", "rejected", "pending", "withdrew")
STATUSES = ("pending", "approved", "rejected")
MODES = ("on-campus", "off-campus", "referral", "internship")


class Experience(Base):
    __tablename__ = "experiences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    role_title: Mapped[str] = mapped_column(String(100), index=True)
    year: Mapped[int] = mapped_column(Integer)
    mode: Mapped[str] = mapped_column(String(20), default="on-campus")
    outcome: Mapped[str] = mapped_column(String(20))
    difficulty: Mapped[int] = mapped_column(Integer)  # 1 (easy) .. 5 (very hard)
    summary: Mapped[str] = mapped_column(Text)
    tips: Mapped[str | None] = mapped_column(Text, nullable=True)
    anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    moderation_note: Mapped[str | None] = mapped_column(String(300), nullable=True)
    upvotes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    company: Mapped[Company] = relationship(lazy="joined")
    author: Mapped[User] = relationship(lazy="joined")
    rounds: Mapped[list["ExperienceRound"]] = relationship(
        back_populates="experience", cascade="all, delete-orphan",
        order_by="ExperienceRound.position", lazy="selectin")


class ExperienceRound(Base):
    __tablename__ = "experience_rounds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    experience_id: Mapped[int] = mapped_column(ForeignKey("experiences.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(Text)

    experience: Mapped[Experience] = relationship(back_populates="rounds")


class ExperienceVote(Base):
    __tablename__ = "experience_votes"
    __table_args__ = (UniqueConstraint("user_id", "experience_id", name="uq_vote"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    experience_id: Mapped[int] = mapped_column(ForeignKey("experiences.id", ondelete="CASCADE"))
