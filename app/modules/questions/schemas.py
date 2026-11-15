from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.questions.models import DIFFICULTIES, TOPICS


class QuestionCreate(BaseModel):
    text: str = Field(min_length=10, max_length=4000)
    topic: str
    difficulty: str = "medium"
    role_title: str | None = Field(default=None, max_length=100)
    company: str | None = Field(default=None, max_length=120)
    tags: list[str] = Field(default_factory=list, max_length=15)
    model_answer: str | None = Field(default=None, max_length=8000)

    @field_validator("topic")
    @classmethod
    def valid_topic(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in TOPICS:
            raise ValueError(f"topic must be one of {TOPICS}")
        return v

    @field_validator("difficulty")
    @classmethod
    def valid_difficulty(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in DIFFICULTIES:
            raise ValueError(f"difficulty must be one of {DIFFICULTIES}")
        return v

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, v: list[str]) -> list[str]:
        return sorted({t.strip().lower() for t in v if t and t.strip() and "," not in t})


class QuestionUpdate(BaseModel):
    text: str | None = Field(default=None, min_length=10, max_length=4000)
    difficulty: str | None = None
    model_answer: str | None = Field(default=None, max_length=8000)
    tags: list[str] | None = None

    @field_validator("difficulty")
    @classmethod
    def valid_difficulty(cls, v):
        return None if v is None else QuestionCreate.valid_difficulty(v)

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, v):
        return None if v is None else QuestionCreate.clean_tags(v)


class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    topic: str
    difficulty: str
    role_title: str | None
    tags: list[str]
    company: str | None
    has_model_answer: bool
    times_asked: int
    source_experience_id: int | None
    created_at: datetime


class QuestionDetail(QuestionOut):
    model_answer: str | None


class Suggestion(BaseModel):
    question: QuestionOut
    score: float
    reason: str


class QuestionPage(BaseModel):
    items: list[QuestionOut]
    total: int
    page: int
    size: int
