"""Company lookup helpers used by other modules."""
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, ValidationFailed
from app.modules.companies.models import Company


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    if not slug:
        raise ValidationFailed("company name must contain letters or digits")
    return slug


def get_or_create(db: Session, name: str, sector: str | None = None) -> Company:
    slug = slugify(name)
    company = db.scalar(select(Company).where(Company.slug == slug))
    if company is None:
        company = Company(name=name.strip(), slug=slug, sector=sector)
        db.add(company)
        db.flush()
    return company


def find_by_name(db: Session, name: str) -> Company | None:
    try:
        slug = slugify(name)
    except ValidationFailed:
        return None
    return db.scalar(select(Company).where(Company.slug == slug))


def get(db: Session, company_id: int) -> Company:
    company = db.get(Company, company_id)
    if company is None:
        raise NotFoundError("company not found")
    return company


def list_all(db: Session) -> list[Company]:
    return list(db.scalars(select(Company).order_by(Company.name)))
