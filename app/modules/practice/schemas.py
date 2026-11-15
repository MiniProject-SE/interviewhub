from datetime import datetime

from pydantic import BaseModel, Field


class StartSession(BaseModel):
    role_title: str | None = Field(default=None, max_length=100)
    company: str | None = Field(default=None, max_length=120)
    topic: str | None = Field(default=None, max_length=40)
    num_questions: int = Field(default=5, ge=1, le=15)
    duration_minutes: int = Field(default=30, ge=5, le=180)
    focus_weak_topics: bool = True


class AnswerIn(BaseModel):
    answer_text: str = Field(max_length=10000)
    self_rating: int | None = Field(default=None, ge=1, le=5)
    time_taken_sec: int | None = Field(default=None, ge=0, le=36000)


class ItemOut(BaseModel):
    item_id: int
    position: int
    question_id: int
    question: str
    topic: str
    difficulty: str
    answered: bool
    answer_text: str | None = None
    self_rating: int | None = None
    auto_score: float | None = None
    final_score: float | None = None
    feedback: str | None = None
    model_answer: str | None = None  # revealed only after the session ends


class SessionOut(BaseModel):
    id: int
    state: str
    role_title: str | None
    company: str | None
    topic: str | None
    duration_minutes: int
    started_at: datetime
    ended_at: datetime | None
    seconds_remaining: int
    total_score: float | None
    items: list[ItemOut]


class SessionSummary(BaseModel):
    id: int
    state: str
    started_at: datetime
    total_score: float | None
    questions: int
    topic: str | None
    company: str | None


class TopicStat(BaseModel):
    topic: str
    attempts: int
    avg_score: float


class TrendPoint(BaseModel):
    session_id: int
    date: datetime
    score: float


class Analytics(BaseModel):
    sessions_completed: int
    questions_answered: int
    average_score: float
    best_score: float
    total_practice_minutes: float
    current_streak_days: int
    topics: list[TopicStat]
    weak_topics: list[str]
    strong_topics: list[str]
    trend: list[TrendPoint]
    improvement: float
