"""Question bank business logic. Public functions here form the module API
used by Experiences (create from an experience) and Practice (pick
questions for a mock interview)."""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, PermissionDeniedError
from app.modules.auth.models import User
from app.modules.companies import service as companies
from app.modules.companies.models import Company
from app.modules.questions import recommender, schemas
from app.modules.questions.models import Question


def to_doc(q: Question) -> recommender.Doc:
    return recommender.Doc(
        id=q.id, text=q.text, topic=q.topic, tags=q.tags,
        company=q.company.name if q.company else None,
        role_title=q.role_title, times_asked=q.times_asked,
    )


def to_out(q: Question, detail: bool = False):
    data = dict(
        id=q.id, text=q.text, topic=q.topic, difficulty=q.difficulty,
        role_title=q.role_title, tags=[t for t in q.tags.split(",") if t],
        company=q.company.name if q.company else None,
        has_model_answer=bool(q.model_answer), times_asked=q.times_asked,
        source_experience_id=q.source_experience_id, created_at=q.created_at,
    )
    if detail:
        return schemas.QuestionDetail(**data, model_answer=q.model_answer)
    return schemas.QuestionOut(**data)


def get(db: Session, question_id: int) -> Question:
    q = db.get(Question, question_id)
    if q is None:
        raise NotFoundError("question not found")
    return q


def all_questions(db: Session) -> list[Question]:
    return list(db.scalars(select(Question)))


def create(db: Session, data: schemas.QuestionCreate, author: User | None,
           source_experience_id: int | None = None, commit: bool = True) -> tuple[Question, bool]:
    """Create a question, or merge into a near-duplicate.

    Returns (question, created). ``created`` is False when merged.
    """
    company = companies.get_or_create(db, data.company) if data.company else None
    existing = [q for q in all_questions(db) if company is None or q.company_id in (None, company.id)]
    match, sim = recommender.TfidfIndex((to_doc(q) for q in existing), text_only=True).most_similar(data.text)
    if match is not None and sim >= recommender.DUPLICATE_THRESHOLD:
        dup = get(db, match.id)
        dup.times_asked += 1
        if commit:
            db.commit()
        return dup, False

    q = Question(
        text=data.text.strip(), topic=data.topic, difficulty=data.difficulty,
        role_title=data.role_title, tags=",".join(data.tags), model_answer=data.model_answer,
        company_id=company.id if company else None,
        source_experience_id=source_experience_id,
        created_by=author.id if author else None,
    )
    db.add(q)
    if commit:
        db.commit()
        db.refresh(q)
    else:
        db.flush()
    return q, True


def update(db: Session, user: User, question_id: int, data: schemas.QuestionUpdate) -> Question:
    q = get(db, question_id)
    if user.role not in ("moderator", "admin") and q.created_by != user.id:
        raise PermissionDeniedError("only the author or a moderator can edit")
    changes = data.model_dump(exclude_unset=True)
    # Required columns cannot be cleared; an explicit null means "leave unchanged".
    for required in ("text", "difficulty", "tags"):
        if changes.get(required, "") is None:
            changes.pop(required)
    if "tags" in changes:
        changes["tags"] = ",".join(changes["tags"])
    for k, v in changes.items():
        setattr(q, k, v)
    db.commit()
    db.refresh(q)
    return q


def delete(db: Session, user: User, question_id: int) -> None:
    q = get(db, question_id)
    if user.role not in ("moderator", "admin"):
        raise PermissionDeniedError("only moderators can delete questions")
    db.delete(q)
    db.commit()


def search(db: Session, *, q: str | None = None, topic: str | None = None, difficulty: str | None = None,
           company: str | None = None, role: str | None = None, page: int = 1, size: int = 20):
    stmt = select(Question)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Question.text.ilike(like), Question.tags.ilike(like)))
    if topic:
        stmt = stmt.where(Question.topic == topic.lower())
    if difficulty:
        stmt = stmt.where(Question.difficulty == difficulty.lower())
    if company:
        stmt = stmt.join(Company, Question.company_id == Company.id).where(
            Company.slug == companies.slugify(company))
    if role:
        stmt = stmt.where(Question.role_title.ilike(f"%{role.strip()}%"))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(
        stmt.order_by(Question.times_asked.desc(), Question.id.desc())
        .offset((page - 1) * size).limit(size)
    ).unique()
    return list(rows), total


def topic_stats(db: Session) -> dict[str, int]:
    rows = db.execute(select(Question.topic, func.count(Question.id)).group_by(Question.topic))
    return {t: c for t, c in rows}
