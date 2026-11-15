"""Shared fixtures: an isolated in-memory database per test."""
import os

os.environ.setdefault("JWT_SECRET", "test-secret-key-that-is-long-enough-1234")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.database import get_db, init_db  # noqa: E402
from app.main import create_app  # noqa: E402

PASSWORD = "Passw0rd!"


@pytest.fixture()
def engine():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    init_db(bind=eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def db(engine):
    session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()
    yield session
    session.close()


@pytest.fixture()
def client(engine):
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def _get_db():
        s = Session()
        try:
            yield s
        finally:
            s.close()

    app = create_app()
    app.dependency_overrides[get_db] = _get_db
    with TestClient(app) as c:
        yield c


def register_and_login(client, email, name="Test User", role=None, db=None):
    client.post("/api/auth/register", json={"name": name, "email": email, "password": PASSWORD})
    if role and db is not None:
        from app.modules.auth.models import User
        u = db.query(User).filter_by(email=email).one()
        u.role = role
        db.commit()
    r = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def admin_h(client):
    # First registered user becomes admin.
    return register_and_login(client, "admin@test.dev", "Admin")


@pytest.fixture()
def student_h(client, admin_h):
    return register_and_login(client, "student@test.dev", "Student")


@pytest.fixture()
def student2_h(client, admin_h):
    return register_and_login(client, "student2@test.dev", "Student Two")


@pytest.fixture()
def mod_h(client, admin_h, db):
    return register_and_login(client, "mod@test.dev", "Mod", role="moderator", db=db)


SAMPLE_QUESTIONS = [
    dict(text="Explain the difference between process and thread.", topic="os", difficulty="easy",
         company="Infosys", role_title="Software Engineer", tags=["process", "thread"],
         model_answer="A process has its own address space; a thread shares memory within a process. "
                      "Thread context switch is cheaper; synchronization uses mutex."),
    dict(text="What is a deadlock and how can it be prevented?", topic="os", difficulty="medium",
         company="Wipro", tags=["deadlock"],
         model_answer="Deadlock needs mutual exclusion, hold and wait, no preemption, circular wait."),
    dict(text="Reverse a singly linked list in place.", topic="dsa", difficulty="easy", company="Amazon",
         role_title="SDE Intern", tags=["linked-list"],
         model_answer="Use prev, current and next pointers; iterate and reverse links. O(n) time."),
    dict(text="Detect a cycle in a directed graph using DFS.", topic="dsa", difficulty="medium",
         company="Google", role_title="SDE", tags=["graph", "dfs"],
         model_answer="DFS with recursion stack; back edge means cycle. Or Kahn topological sort."),
    dict(text="What are the ACID properties of transactions?", topic="dbms", difficulty="easy",
         company="Oracle", tags=["transactions"],
         model_answer="Atomicity, consistency, isolation, durability."),
    dict(text="Describe a time you handled conflict in a team project.", topic="behavioral",
         difficulty="medium", tags=["star"], model_answer=None),
]


@pytest.fixture()
def seeded(client, admin_h):
    ids = []
    for q in SAMPLE_QUESTIONS:
        r = client.post("/api/questions", json=q, headers=admin_h)
        assert r.status_code == 201, r.text
        ids.append(r.json()["id"])
    return ids
