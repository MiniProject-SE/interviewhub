"""HTTP endpoints for /api/questions."""
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.deps import get_current_user
from app.modules.auth.models import User
from app.modules.questions import recommender, schemas, service
from app.modules.questions.models import DIFFICULTIES, TOPICS

router = APIRouter(prefix="/api/questions", tags=["questions"])


@router.get("/meta")
def meta(db: Session = Depends(get_db)):
    return {"topics": TOPICS, "difficulties": DIFFICULTIES, "counts": service.topic_stats(db)}


@router.get("", response_model=schemas.QuestionPage)
def search(q: str | None = None, topic: str | None = None, difficulty: str | None = None,
           company: str | None = None, role: str | None = None,
           page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
           db: Session = Depends(get_db)):
    rows, total = service.search(db, q=q, topic=topic, difficulty=difficulty,
                                 company=company, role=role, page=page, size=size)
    return schemas.QuestionPage(items=[service.to_out(r) for r in rows], total=total, page=page, size=size)


@router.post("", response_model=schemas.QuestionOut)
def create(data: schemas.QuestionCreate, response: Response,
           user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q, created = service.create(db, data, user)
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    response.headers["X-Duplicate-Merged"] = "false" if created else "true"
    return service.to_out(q)


@router.get("/suggest", response_model=list[schemas.Suggestion])
def suggest(q: str = "", company: str | None = None, role: str | None = None, topic: str | None = None,
            limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    query = recommender.Query(text=q, company=company, role_title=role, topic=topic, limit=limit)
    return [schemas.Suggestion(question=service.to_out(qn), score=s, reason=r)
            for qn, s, r in service.suggest(db, query)]


@router.get("/{question_id}", response_model=schemas.QuestionDetail)
def detail(question_id: int, db: Session = Depends(get_db)):
    return service.to_out(service.get(db, question_id), detail=True)


@router.patch("/{question_id}", response_model=schemas.QuestionDetail)
def update(question_id: int, data: schemas.QuestionUpdate,
           user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.to_out(service.update(db, user, question_id, data), detail=True)


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(question_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service.delete(db, user, question_id)
