"""Module 1 — Auth & User Management tests (FR-1.x, SR-x)."""
import pytest

from app.core.config import settings
from app.modules.auth.security import create_access_token, decode_access_token, hash_password, verify_password
from tests.conftest import PASSWORD


def test_register_first_user_is_admin(client):
    r = client.post("/api/auth/register", json={"name": "First", "email": "first@x.dev", "password": PASSWORD})
    assert r.status_code == 201
    assert r.json()["role"] == "admin"
    assert "password" not in r.text and "password_hash" not in r.text


def test_second_user_is_student(client, admin_h):
    r = client.post("/api/auth/register", json={"name": "Second", "email": "Second@X.dev", "password": PASSWORD})
    assert r.json()["role"] == "student"
    assert r.json()["email"] == "second@x.dev"  # normalised


def test_duplicate_email_rejected(client, admin_h):
    r = client.post("/api/auth/register", json={"name": "Dup", "email": "ADMIN@test.dev", "password": PASSWORD})
    assert r.status_code == 409


@pytest.mark.parametrize("pw", ["short1", "allletters", "12345678"])
def test_weak_passwords_rejected(client, pw):
    r = client.post("/api/auth/register", json={"name": "Weak", "email": "w@x.dev", "password": pw})
    assert r.status_code == 422


def test_invalid_email_and_short_name_rejected(client):
    assert client.post("/api/auth/register", json={"name": "Ok", "email": "bad", "password": PASSWORD}).status_code == 422
    assert client.post("/api/auth/register", json={"name": "  a ", "email": "a@x.dev", "password": PASSWORD}).status_code == 422


def test_login_success_and_me(client, student_h):
    r = client.get("/api/users/me", headers=student_h)
    assert r.status_code == 200 and r.json()["email"] == "student@test.dev"


def test_protected_route_requires_token(client):
    assert client.get("/api/users/me").status_code == 401
    assert client.get("/api/users/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_password_hashing():
    h = hash_password("Secret123")
    assert h != "Secret123" and verify_password("Secret123", h)
    assert not verify_password("Secret124", h)
    assert not verify_password("x", "not-a-bcrypt-hash")


def test_token_round_trip():
    payload = decode_access_token(create_access_token(7, "moderator"))
    assert payload["sub"] == "7" and payload["role"] == "moderator"
    assert settings.jwt_algorithm == "HS256"


def test_update_profile(client, student_h):
    r = client.patch("/api/users/me", json={"college": "PES University", "target_role": "SDE"}, headers=student_h)
    assert r.status_code == 200 and r.json()["college"] == "PES University"


def test_change_password(client, student_h):
    bad = client.post("/api/users/me/password", json={"old_password": "nope1234", "new_password": "NewPass99"},
                      headers=student_h)
    assert bad.status_code == 401
    ok = client.post("/api/users/me/password", json={"old_password": PASSWORD, "new_password": "NewPass99"},
                     headers=student_h)
    assert ok.status_code == 204
    assert client.post("/api/auth/login", json={"email": "student@test.dev", "password": "NewPass99"}).status_code == 200


def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_frontend_served(client):
    r = client.get("/")
    assert r.status_code == 200 and "InterviewHub" in r.text
