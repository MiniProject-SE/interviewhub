"""Mock interview lifecycle and performance analytics.

Session state machine:
    in_progress --finish()--> completed
    in_progress --deadline passed--> expired   (checked lazily on access)
"""
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, ValidationFailed
from app.modules.auth.models import User
from app.modules.practice import schemas, scorer
from app.modules.practice.models import PracticeSession, SessionItem
from app.modules.questions import recommender
from app.modules.questions import service as question_service

WEAK_THRESHOLD = 60.0
STRONG_THRESHOLD = 75.0


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
    scores = [i.final_score if i.final_score is not None else 0.0 for i in s.items]
    s.total_score = round(sum(scores) / len(scores), 1) if scores else 0.0
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


def start(db: Session, user: User, data: schemas.StartSession) -> PracticeSession:
    weak = analytics(db, user).weak_topics if data.focus_weak_topics else []
    seen = answered_question_ids(db, user.id)
    query = recommender.Query(
        text=" ".join(filter(None, [data.role_title, data.topic])),
        company=data.company, role_title=data.role_title or user.target_role,
        topic=data.topic, weak_topics=weak, exclude_ids=seen, limit=data.num_questions,
    )
    picks = question_service.suggest(db, query)
    if len(picks) < data.num_questions:
        # Not enough unseen questions: allow repeats rather than failing.
        query.exclude_ids = set()
        picks = question_service.suggest(db, query)
    if not picks:
        raise ValidationFailed("no questions match these filters yet")
    s = PracticeSession(user_id=user.id, role_title=data.role_title, company=data.company,
                        topic=data.topic, duration_minutes=data.duration_minutes)
    s.items = [SessionItem(question_id=q.id, position=i + 1) for i, (q, _, _) in enumerate(picks)]
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
    q = item.question
    result = scorer.score_answer(data.answer_text, scorer.extract_keywords(q.text, q.model_answer, q.tags))
    item.answer_text = data.answer_text
    item.self_rating = data.self_rating
    item.time_taken_sec = data.time_taken_sec
    item.auto_score = result.auto_score
    item.final_score = scorer.combine(result.auto_score, data.self_rating)
    item.feedback = result.feedback
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


def streak_days(dates: list[datetime], today: datetime | None = None) -> int:
    """Consecutive days (ending today or yesterday) with at least one session."""
    days = {as_utc(d).date() for d in dates}
    cursor = (today or now()).date()
    if cursor not in days:
        cursor -= timedelta(days=1)
    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def analytics(db: Session, user: User) -> schemas.Analytics:
    sessions = list(db.scalars(
        select(PracticeSession).where(PracticeSession.user_id == user.id,
                                      PracticeSession.state.in_(("completed", "expired")))
        .order_by(PracticeSession.started_at)))
    per_topic: dict[str, list[float]] = defaultdict(list)
    answered, minutes = 0, 0.0
    for s in sessions:
        for i in s.items:
            if i.final_score is not None:
                answered += 1
                per_topic[i.question.topic].append(i.final_score)
            minutes += (i.time_taken_sec or 0) / 60
    topics = sorted(
        (schemas.TopicStat(topic=t, attempts=len(v), avg_score=round(sum(v) / len(v), 1))
         for t, v in per_topic.items()),
        key=lambda ts: ts.avg_score)
    scores = [s.total_score or 0.0 for s in sessions]
    trend = [schemas.TrendPoint(session_id=s.id, date=s.started_at, score=s.total_score or 0.0)
             for s in sessions[-10:]]
    improvement = 0.0
    if len(scores) >= 2:
        half = len(scores) // 2
        improvement = round(sum(scores[half:]) / len(scores[half:]) - sum(scores[:half]) / half, 1)
    return schemas.Analytics(
        sessions_completed=len(sessions),
        questions_answered=answered,
        average_score=round(sum(scores) / len(scores), 1) if scores else 0.0,
        best_score=max(scores) if scores else 0.0,
        total_practice_minutes=round(minutes, 1),
        current_streak_days=streak_days([s.started_at for s in sessions]),
        topics=topics,
        weak_topics=[t.topic for t in topics if t.avg_score < WEAK_THRESHOLD],
        strong_topics=[t.topic for t in reversed(topics) if t.avg_score >= STRONG_THRESHOLD],
        trend=trend,
        improvement=improvement,
    )
