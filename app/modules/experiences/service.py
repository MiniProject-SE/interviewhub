"""Experience sharing, browsing, voting and moderation."""
from collections import Counter

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ConflictError, NotFoundError, PermissionDeniedError
from app.modules.auth.models import User
from app.modules.companies import service as companies
from app.modules.companies.models import Company
from app.modules.experiences import schemas
from app.modules.experiences.models import Experience, ExperienceRound, ExperienceVote
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
        status=e.status, upvotes=e.upvotes,
        rounds=[schemas.RoundOut(position=r.position, name=r.name, description=r.description) for r in e.rounds],
        question_ids=qids, created_at=e.created_at,
    )


def get(db: Session, exp_id: int, viewer: User | None = None) -> Experience:
    e = db.get(Experience, exp_id)
    if e is None:
        raise NotFoundError("experience not found")
    # Unapproved posts are visible only to their author and moderators.
    if e.status != "approved" and not _is_mod(viewer) and (viewer is None or viewer.id != e.author_id):
        raise NotFoundError("experience not found")
    return e


def create(db: Session, author: User, data: schemas.ExperienceCreate) -> Experience:
    company = companies.get_or_create(db, data.company)
    auto_approve = not settings.require_moderation or _is_mod(author)
    e = Experience(
        author_id=author.id, company_id=company.id, role_title=data.role_title.strip(),
        year=data.year, mode=data.mode, outcome=data.outcome, difficulty=data.difficulty,
        summary=data.summary.strip(), tips=data.tips, anonymous=data.anonymous,
        status="approved" if auto_approve else "pending",
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
           year: int | None = None, q: str | None = None, sort: str = "recent",
           page: int = 1, size: int = 10):
    stmt = select(Experience).join(Company, Experience.company_id == Company.id).where(
        Experience.status == "approved")
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
    order = Experience.upvotes.desc() if sort == "top" else Experience.created_at.desc()
    rows = db.scalars(stmt.order_by(order, Experience.id.desc()).offset((page - 1) * size).limit(size)).unique()
    return list(rows), total


def toggle_vote(db: Session, user: User, exp_id: int) -> tuple[int, bool]:
    e = get(db, exp_id, user)
    if e.author_id == user.id:
        raise ConflictError("you cannot upvote your own experience")
    vote = db.scalar(select(ExperienceVote).where(
        ExperienceVote.user_id == user.id, ExperienceVote.experience_id == exp_id))
    if vote:
        db.delete(vote)
        e.upvotes = max(0, e.upvotes - 1)
        voted = False
    else:
        db.add(ExperienceVote(user_id=user.id, experience_id=exp_id))
        e.upvotes += 1
        voted = True
    db.commit()
    return e.upvotes, voted


def pending(db: Session) -> list[Experience]:
    return list(db.scalars(select(Experience).where(Experience.status == "pending")
                           .order_by(Experience.created_at)).unique())


def moderate(db: Session, exp_id: int, decision: schemas.ModerationDecision) -> Experience:
    e = db.get(Experience, exp_id)
    if e is None:
        raise NotFoundError("experience not found")
    e.status = "approved" if decision.approve else "rejected"
    e.moderation_note = decision.note
    db.commit()
    db.refresh(e)
    return e


def mine(db: Session, user: User) -> list[Experience]:
    return list(db.scalars(select(Experience).where(Experience.author_id == user.id)
                           .order_by(Experience.created_at.desc())).unique())


def company_stats(db: Session, company_name: str) -> schemas.CompanyStats:
    company = companies.find_by_name(db, company_name)
    if company is None:
        raise NotFoundError("company not found")
    exps = list(db.scalars(select(Experience).where(
        Experience.company_id == company.id, Experience.status == "approved")).unique())
    decided = [e for e in exps if e.outcome in ("selected", "rejected")]
    selected = sum(1 for e in decided if e.outcome == "selected")
    roles = Counter(e.role_title for e in exps).most_common(3)
    qcount = db.scalar(select(func.count(Question.id)).where(Question.company_id == company.id))
    return schemas.CompanyStats(
        company=company.name,
        experiences=len(exps),
        selection_rate=round(selected / len(decided), 3) if decided else 0.0,
        avg_difficulty=round(sum(e.difficulty for e in exps) / len(exps), 2) if exps else 0.0,
        top_roles=[r for r, _ in roles],
        question_count=qcount or 0,
    )
