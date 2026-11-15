"""HTTP endpoints for /api/experiences and /api/companies."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.deps import get_current_user, get_optional_user, require_roles
from app.modules.auth.models import User
from app.modules.companies import service as companies
from app.modules.experiences import schemas, service

router = APIRouter(tags=["experiences"])


@router.get("/api/companies")
def list_companies(db: Session = Depends(get_db)):
    return [{"id": c.id, "name": c.name, "slug": c.slug} for c in companies.list_all(db)]


@router.get("/api/companies/{name}/stats", response_model=schemas.CompanyStats)
def company_stats(name: str, db: Session = Depends(get_db)):
    return service.company_stats(db, name)


@router.get("/api/experiences", response_model=schemas.ExperiencePage)
def browse(company: str | None = None, role: str | None = None, outcome: str | None = None,
           year: int | None = None, q: str | None = None, sort: str = Query("recent", pattern="^(recent|top)$"),
           page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    rows, total = service.browse(db, company=company, role=role, outcome=outcome, year=year, q=q,
                                 sort=sort, page=page, size=size)
    return schemas.ExperiencePage(items=[service.to_out(db, e) for e in rows], total=total, page=page, size=size)


@router.post("/api/experiences", response_model=schemas.ExperienceOut, status_code=status.HTTP_201_CREATED)
def create(data: schemas.ExperienceCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.to_out(db, service.create(db, user, data))


@router.get("/api/experiences/mine", response_model=list[schemas.ExperienceOut])
def mine(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [service.to_out(db, e) for e in service.mine(db, user)]


@router.get("/api/experiences/pending", response_model=list[schemas.ExperienceOut])
def pending(_: User = Depends(require_roles("moderator", "admin")), db: Session = Depends(get_db)):
    return [service.to_out(db, e) for e in service.pending(db)]


@router.get("/api/experiences/{exp_id}", response_model=schemas.ExperienceOut)
def detail(exp_id: int, viewer: User | None = Depends(get_optional_user), db: Session = Depends(get_db)):
    return service.to_out(db, service.get(db, exp_id, viewer))


@router.patch("/api/experiences/{exp_id}", response_model=schemas.ExperienceOut)
def update(exp_id: int, data: schemas.ExperienceUpdate, user: User = Depends(get_current_user),
           db: Session = Depends(get_db)):
    return service.to_out(db, service.update(db, user, exp_id, data))


@router.delete("/api/experiences/{exp_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(exp_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service.delete(db, user, exp_id)


@router.post("/api/experiences/{exp_id}/vote")
def vote(exp_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    upvotes, voted = service.toggle_vote(db, user, exp_id)
    return {"upvotes": upvotes, "voted": voted}


@router.post("/api/experiences/{exp_id}/moderate", response_model=schemas.ExperienceOut)
def moderate(exp_id: int, decision: schemas.ModerationDecision,
             _: User = Depends(require_roles("moderator", "admin")), db: Session = Depends(get_db)):
    return service.to_out(db, service.moderate(db, exp_id, decision))
