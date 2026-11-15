"""Mock interview lifecycle.

Session state machine:
    in_progress --finish()--> completed
    in_progress --deadline passed--> expired   (checked lazily on access)
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, ValidationFailed
from app.modules.auth.models import User
from app.modules.practice import schemas
from app.modules.practice.models import PracticeSession, SessionItem
from app.modules.questions import service as question_service


def now() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(dt: datetime) -> datetime:
    # SQLite drops tzinfo; values are always stored as UTC.
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def deadline(s: PracticeSession) -> datetime:
    return as_utc(s.started_at) + timedelta(minutes=s.duration_minutes)


def seconds_remaining(s: PracticeSession, at: datetime | None = None) -> int:
    if s.state != "in_progress":
        return 0
    return max(0, int((deadline(s) - (at or now())).total_seconds()))


def _finalise(db: Session, s: PracticeSession, state: str, at: datetime | None = None) -> None:
    s.state = state
    s.ended_at = at or now()
    db.commit()


def _expire_if_due(db: Session, s: PracticeSession, at: datetime | None = None) -> None:
    if s.state == "in_progress" and (at or now()) >= deadline(s):
        _finalise(db, s, "expired", at)


def answered_question_ids(db: Session, user_id: int) -> set[int]:
    rows = db.scalars(
        select(SessionItem.question_id).join(PracticeSession)
        .where(PracticeSession.user_id == user_id, SessionItem.answer_text.is_not(None)))
    return set(rows)


def pick_questions(db: Session, data: schemas.StartSession, exclude: set[int]):
    """Filter the question bank by topic/company; most-asked first."""
    rows, _ = question_service.search(db, topic=data.topic, company=data.company, size=100)
    return [q for q in rows if q.id not in exclude][: data.num_questions]


def start(db: Session, user: User, data: schemas.StartSession) -> PracticeSession:
    seen = answered_question_ids(db, user.id)
    picks = pick_questions(db, data, seen)
    if len(picks) < data.num_questions:
        # Not enough unseen questions: allow repeats rather than failing.
        picks = pick_questions(db, data, set())
    if not picks:
        raise ValidationFailed("no questions match these filters yet")
    s = PracticeSession(user_id=user.id, role_title=data.role_title, company=data.company,
                        topic=data.topic, duration_minutes=data.duration_minutes)
    s.items = [SessionItem(question_id=q.id, position=i + 1) for i, q in enumerate(picks)]
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def get(db: Session, user: User, session_id: int) -> PracticeSession:
    s = db.get(PracticeSession, session_id)
    if s is None or s.user_id != user.id:
        raise NotFoundError("session not found")
    _expire_if_due(db, s)
    return s


def answer(db: Session, user: User, session_id: int, item_id: int, data: schemas.AnswerIn) -> SessionItem:
    s = get(db, user, session_id)
    if s.state != "in_progress":
        raise ConflictError(f"session is {s.state}; answers are closed")
    item = next((i for i in s.items if i.id == item_id), None)
    if item is None:
        raise NotFoundError("question not part of this session")
    item.answer_text = data.answer_text
    item.self_rating = data.self_rating
    item.time_taken_sec = data.time_taken_sec
    item.answered_at = now()
    db.commit()
    db.refresh(item)
    return item


def finish(db: Session, user: User, session_id: int) -> PracticeSession:
    s = get(db, user, session_id)
    if s.state != "in_progress":
        raise ConflictError(f"session already {s.state}")
    _finalise(db, s, "completed")
    db.refresh(s)
    return s


def history(db: Session, user: User) -> list[PracticeSession]:
    rows = list(db.scalars(select(PracticeSession).where(PracticeSession.user_id == user.id)
                           .order_by(PracticeSession.started_at.desc())))
    for s in rows:
        _expire_if_due(db, s)
    return rows


def to_out(s: PracticeSession) -> schemas.SessionOut:
    closed = s.state != "in_progress"
    items = [
        schemas.ItemOut(
            item_id=i.id, position=i.position, question_id=i.question_id, question=i.question.text,
            topic=i.question.topic, difficulty=i.question.difficulty, answered=i.answer_text is not None,
            answer_text=i.answer_text, self_rating=i.self_rating, auto_score=i.auto_score,
            final_score=i.final_score, feedback=i.feedback,
            model_answer=i.question.model_answer if closed else None,
        ) for i in s.items
    ]
    return schemas.SessionOut(
        id=s.id, state=s.state, role_title=s.role_title, company=s.company, topic=s.topic,
        duration_minutes=s.duration_minutes, started_at=s.started_at, ended_at=s.ended_at,
        seconds_remaining=seconds_remaining(s), total_score=s.total_score, items=items,
    )
