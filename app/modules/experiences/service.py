"""Experience sharing and browsing."""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, PermissionDeniedError
from app.modules.auth.models import User
from app.modules.companies import service as companies
from app.modules.companies.models import Company
from app.modules.experiences import schemas
from app.modules.experiences.models import Experience, ExperienceRound
from app.modules.questions import service as question_service
from app.modules.questions.models import Question
from app.modules.questions.schemas import QuestionCreate

MODERATOR_ROLES = ("moderator", "admin")


def _is_mod(user: User | None) -> bool:
    return user is not None and user.role in MODERATOR_ROLES


def to_out(db: Session, e: Experience) -> schemas.ExperienceOut:
    qids = list(db.scalars(select(Question.id).where(Question.source_experience_id == e.id)))
    return schemas.ExperienceOut(
        id=e.id, company=e.company.name, role_title=e.role_title, year=e.year, mode=e.mode,
        outcome=e.outcome, difficulty=e.difficulty, summary=e.summary, tips=e.tips,
        author="Anonymous" if e.anonymous else e.author.name,
        rounds=[schemas.RoundOut(position=r.position, name=r.name, description=r.description) for r in e.rounds],
        question_ids=qids, created_at=e.created_at,
    )


def get(db: Session, exp_id: int, viewer: User | None = None) -> Experience:
    e = db.get(Experience, exp_id)
    if e is None:
        raise NotFoundError("experience not found")
    return e


def create(db: Session, author: User, data: schemas.ExperienceCreate) -> Experience:
    company = companies.get_or_create(db, data.company)
    e = Experience(
        author_id=author.id, company_id=company.id, role_title=data.role_title.strip(),
        year=data.year, mode=data.mode, outcome=data.outcome, difficulty=data.difficulty,
        summary=data.summary.strip(), tips=data.tips, anonymous=data.anonymous,
    )
    e.rounds = [ExperienceRound(position=i + 1, name=r.name, description=r.description)
                for i, r in enumerate(data.rounds)]
    db.add(e)
    db.flush()
    # Feed every asked question into the shared question bank (Member 3's API).
    for aq in data.questions:
        question_service.create(
            db,
            QuestionCreate(text=aq.text, topic=aq.topic, difficulty=aq.difficulty, tags=aq.tags,
                           company=company.name, role_title=e.role_title),
            author, source_experience_id=e.id, commit=False,
        )
    db.commit()
    db.refresh(e)
    return e


def update(db: Session, user: User, exp_id: int, data: schemas.ExperienceUpdate) -> Experience:
    e = get(db, exp_id, user)
    if e.author_id != user.id and not _is_mod(user):
        raise PermissionDeniedError("only the author can edit this experience")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(e, k, v)
    db.commit()
    db.refresh(e)
    return e


def delete(db: Session, user: User, exp_id: int) -> None:
    e = get(db, exp_id, user)
    if e.author_id != user.id and not _is_mod(user):
        raise PermissionDeniedError("only the author or a moderator can delete")
    db.delete(e)
    db.commit()


def browse(db: Session, *, company: str | None = None, role: str | None = None, outcome: str | None = None,
           year: int | None = None, q: str | None = None, page: int = 1, size: int = 10):
    stmt = select(Experience).join(Company, Experience.company_id == Company.id)
    if company:
        stmt = stmt.where(Company.slug == companies.slugify(company))
    if role:
        stmt = stmt.where(Experience.role_title.ilike(f"%{role.strip()}%"))
    if outcome:
        stmt = stmt.where(Experience.outcome == outcome.lower())
    if year:
        stmt = stmt.where(Experience.year == year)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Experience.summary.ilike(like), Experience.tips.ilike(like),
                              Company.name.ilike(like)))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.order_by(Experience.created_at.desc(), Experience.id.desc())
                      .offset((page - 1) * size).limit(size)).unique()
    return list(rows), total


def mine(db: Session, user: User) -> list[Experience]:
    return list(db.scalars(select(Experience).where(Experience.author_id == user.id)
                           .order_by(Experience.created_at.desc())).unique())
