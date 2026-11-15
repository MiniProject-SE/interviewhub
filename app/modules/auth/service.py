"""Business logic for registration, login, profiles and role management."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AuthError, ConflictError, NotFoundError
from app.modules.auth import schemas
from app.modules.auth.models import User
from app.modules.auth.security import create_access_token, hash_password, verify_password


def _normalise_email(email: str) -> str:
    return email.strip().lower()


def get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("user not found")
    return user


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == _normalise_email(email)))


def register(db: Session, data: schemas.RegisterRequest, role: str = "student") -> User:
    if get_by_email(db, data.email) is not None:
        raise ConflictError("email already registered")
    # The very first account becomes admin so a fresh install is manageable.
    if db.scalar(select(func.count(User.id))) == 0:
        role = "admin"
    user = User(
        name=data.name,
        email=_normalise_email(data.email),
        password_hash=hash_password(data.password),
        role=role,
        college=data.college,
        graduation_year=data.graduation_year,
        target_role=data.target_role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> tuple[User, str]:
    user = get_by_email(db, email)
    # Same message for unknown email and bad password (no user enumeration, SR-4).
    if user is None or not verify_password(password, user.password_hash):
        raise AuthError("invalid email or password")
    return user, create_access_token(user.id, user.role)


def update_profile(db: Session, user: User, data: schemas.ProfileUpdate) -> User:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user: User, data: schemas.PasswordChange) -> None:
    if not verify_password(data.old_password, user.password_hash):
        raise AuthError("old password is incorrect")
    user.password_hash = hash_password(data.new_password)
    db.commit()
