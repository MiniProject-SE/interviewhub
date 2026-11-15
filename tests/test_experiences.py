"""Module 2 — Interview Experiences & Companies tests (FR-2.x)."""
import pytest

from app.core.errors import ValidationFailed
from app.modules.companies import service as companies

EXP = dict(
    company="Amazon", role_title="SDE Intern", year=2026, mode="on-campus", outcome="selected", difficulty=4,
    summary="Online assessment followed by two technical rounds focusing on DSA and leadership principles.",
    tips="Practice LeetCode mediums.",
    rounds=[{"name": "OA", "description": "Two coding problems"}, {"name": "Tech 1", "description": "Trees"}],
    questions=[{"text": "Return the level order traversal of a binary tree.", "topic": "dsa", "tags": ["tree"]},
               {"text": "Tell me about a time you failed and what you learned.", "topic": "behavioral"}],
)


def post(client, h, **over):
    return client.post("/api/experiences", json={**EXP, **over}, headers=h)


def test_create_requires_login(client):
    assert client.post("/api/experiences", json=EXP).status_code == 401


def test_create_experience_feeds_question_bank(client, student_h):
    r = post(client, student_h)
    assert r.status_code == 201
    body = r.json()
    assert len(body["rounds"]) == 2 and body["rounds"][0]["name"] == "OA"
    assert len(body["question_ids"]) == 2
    assert client.get("/api/experiences").json()["total"] == 1
    assert client.get(f"/api/experiences/{body['id']}").status_code == 200
    assert client.get("/api/experiences/999").status_code == 404


def test_anonymous_hides_author(client, student_h):
    assert post(client, student_h, anonymous=True).json()["author"] == "Anonymous"
    assert post(client, student_h).json()["author"] == "Student"


@pytest.mark.parametrize("field,value", [("outcome", "maybe"), ("mode", "telepathy"), ("difficulty", 9),
                                         ("summary", "too short"), ("year", 1990)])
def test_validation(client, student_h, field, value):
    assert post(client, student_h, **{field: value}).status_code == 422


def test_browse_filters(client, student_h):
    post(client, student_h)
    post(client, student_h, company="Google", role_title="SDE", outcome="rejected", year=2025,
         summary="Graph heavy onsite rounds with a strong focus on dynamic programming and optimal code.")
    assert client.get("/api/experiences", params={"company": "amazon"}).json()["total"] == 1
    assert client.get("/api/experiences", params={"outcome": "rejected"}).json()["items"][0]["company"] == "Google"
    assert client.get("/api/experiences", params={"year": 2025}).json()["total"] == 1
    assert client.get("/api/experiences", params={"role": "intern"}).json()["total"] == 1
    assert client.get("/api/experiences", params={"q": "dynamic"}).json()["total"] == 1
    page = client.get("/api/experiences", params={"size": 1, "page": 2}).json()
    assert page["total"] == 2 and len(page["items"]) == 1
    assert client.get("/api/experiences").json()["items"][0]["company"] == "Google"  # newest first


def test_update_and_delete_permissions(client, student_h, student2_h, mod_h):
    eid = post(client, student_h).json()["id"]
    assert client.patch(f"/api/experiences/{eid}", json={"outcome": "rejected"}, headers=student2_h).status_code == 403
    r = client.patch(f"/api/experiences/{eid}", json={"outcome": "rejected", "difficulty": 2}, headers=student_h)
    assert r.json()["outcome"] == "rejected" and r.json()["difficulty"] == 2
    assert client.delete(f"/api/experiences/{eid}", headers=student2_h).status_code == 403
    assert client.delete(f"/api/experiences/{eid}", headers=mod_h).status_code == 204
    assert client.get(f"/api/experiences/{eid}").status_code == 404


def test_mine(client, student_h, student2_h):
    post(client, student_h)
    assert len(client.get("/api/experiences/mine", headers=student_h).json()) == 1
    assert client.get("/api/experiences/mine", headers=student2_h).json() == []
    assert any(c["slug"] == "amazon" for c in client.get("/api/companies").json())


def test_company_slug_and_dedupe(db):
    a = companies.get_or_create(db, "Goldman Sachs")
    b = companies.get_or_create(db, "  goldman   SACHS ")
    assert a.id == b.id and a.slug == "goldman-sachs"
    with pytest.raises(ValidationFailed):
        companies.slugify("!!!")
    assert companies.find_by_name(db, "???") is None
    with pytest.raises(Exception):
        companies.get(db, 999)
    assert companies.get(db, a.id).name == "Goldman Sachs"
