"""HTTP endpoints for /api/auth and /api/users."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth import schemas, service
from app.modules.auth.deps import get_current_user, require_roles
from app.modules.auth.models import User

router = APIRouter(tags=["auth"])


@router.post("/api/auth/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register(data: schemas.RegisterRequest, db: Session = Depends(get_db)):
    return service.register(db, data)


@router.post("/api/auth/login", response_model=schemas.TokenResponse)
def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    user, token = service.authenticate(db, data.email, data.password)
    return schemas.TokenResponse(access_token=token, user=schemas.UserOut.model_validate(user))


@router.get("/api/users/me", response_model=schemas.UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.patch("/api/users/me", response_model=schemas.UserOut)
def update_me(data: schemas.ProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.update_profile(db, user, data)


@router.post("/api/users/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(data: schemas.PasswordChange, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service.change_password(db, user, data)


@router.get("/api/users", response_model=list[schemas.UserOut])
def list_users(_: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return service.list_users(db)


@router.patch("/api/users/{user_id}/role", response_model=schemas.UserOut)
def set_role(user_id: int, data: schemas.RoleUpdate, admin: User = Depends(require_roles("admin")),
             db: Session = Depends(get_db)):
    return service.set_role(db, admin, user_id, data.role)


@router.patch("/api/users/{user_id}/active", response_model=schemas.UserOut)
def set_active(user_id: int, active: bool, admin: User = Depends(require_roles("admin")),
               db: Session = Depends(get_db)):
    return service.set_active(db, admin, user_id, active)
