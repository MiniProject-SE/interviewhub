"""HTTP endpoints for /api/practice."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.deps import get_current_user
from app.modules.auth.models import User
from app.modules.practice import schemas, service

router = APIRouter(prefix="/api/practice", tags=["practice"])


@router.post("/sessions", response_model=schemas.SessionOut, status_code=status.HTTP_201_CREATED)
def start(data: schemas.StartSession, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.to_out(service.start(db, user, data))


@router.get("/sessions", response_model=list[schemas.SessionSummary])
def history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [schemas.SessionSummary(id=s.id, state=s.state, started_at=s.started_at, total_score=s.total_score,
                                   questions=len(s.items), topic=s.topic, company=s.company)
            for s in service.history(db, user)]


@router.get("/sessions/{session_id}", response_model=schemas.SessionOut)
def detail(session_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.to_out(service.get(db, user, session_id))


@router.post("/sessions/{session_id}/items/{item_id}/answer", response_model=schemas.ItemOut)
def answer(session_id: int, item_id: int, data: schemas.AnswerIn,
           user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service.answer(db, user, session_id, item_id, data)
    out = service.to_out(service.get(db, user, session_id))
    return next(i for i in out.items if i.item_id == item_id)


@router.post("/sessions/{session_id}/finish", response_model=schemas.SessionOut)
def finish(session_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.to_out(service.finish(db, user, session_id))


@router.get("/analytics", response_model=schemas.Analytics)
def analytics(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.analytics(db, user)
