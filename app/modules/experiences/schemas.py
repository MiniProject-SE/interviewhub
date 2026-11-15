from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.modules.experiences.models import MODES, OUTCOMES


class RoundIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    description: str = Field(min_length=5, max_length=5000)


class AskedQuestionIn(BaseModel):
    text: str = Field(min_length=10, max_length=4000)
    topic: str = "other"
    difficulty: str = "medium"
    tags: list[str] = Field(default_factory=list)


class ExperienceCreate(BaseModel):
    company: str = Field(min_length=1, max_length=120)
    role_title: str = Field(min_length=2, max_length=100)
    year: int = Field(ge=2000, le=2100)
    mode: str = "on-campus"
    outcome: str
    difficulty: int = Field(ge=1, le=5)
    summary: str = Field(min_length=30, max_length=10000)
    tips: str | None = Field(default=None, max_length=5000)
    anonymous: bool = False
    rounds: list[RoundIn] = Field(default_factory=list, max_length=12)
    questions: list[AskedQuestionIn] = Field(default_factory=list, max_length=30)

    @field_validator("outcome")
    @classmethod
    def valid_outcome(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in OUTCOMES:
            raise ValueError(f"outcome must be one of {OUTCOMES}")
        return v

    @field_validator("mode")
    @classmethod
    def valid_mode(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in MODES:
            raise ValueError(f"mode must be one of {MODES}")
        return v


class ExperienceUpdate(BaseModel):
    summary: str | None = Field(default=None, min_length=30, max_length=10000)
    tips: str | None = Field(default=None, max_length=5000)
    outcome: str | None = None
    difficulty: int | None = Field(default=None, ge=1, le=5)

    @field_validator("outcome")
    @classmethod
    def valid_outcome(cls, v):
        return None if v is None else ExperienceCreate.valid_outcome(v)


class ModerationDecision(BaseModel):
    approve: bool
    note: str | None = Field(default=None, max_length=300)


class RoundOut(BaseModel):
    position: int
    name: str
    description: str


class ExperienceOut(BaseModel):
    id: int
    company: str
    role_title: str
    year: int
    mode: str
    outcome: str
    difficulty: int
    summary: str
    tips: str | None
    author: str
    status: str
    upvotes: int
    rounds: list[RoundOut]
    question_ids: list[int] = Field(default_factory=list)
    created_at: datetime


class ExperiencePage(BaseModel):
    items: list[ExperienceOut]
    total: int
    page: int
    size: int


class CompanyStats(BaseModel):
    company: str
    experiences: int
    selection_rate: float
    avg_difficulty: float
    top_roles: list[str]
    question_count: int
