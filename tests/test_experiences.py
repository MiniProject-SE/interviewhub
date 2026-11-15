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


def test_student_post_goes_to_moderation(client, student_h):
    r = post(client, student_h)
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "pending" and len(body["rounds"]) == 2
    assert len(body["question_ids"]) == 2  # fed into question bank
    assert client.get("/api/experiences").json()["total"] == 0  # hidden until approved


def test_pending_visible_to_author_not_others(client, student_h, student2_h):
    eid = post(client, student_h).json()["id"]
    assert client.get(f"/api/experiences/{eid}", headers=student_h).status_code == 200
    assert client.get(f"/api/experiences/{eid}", headers=student2_h).status_code == 404
    assert client.get(f"/api/experiences/{eid}").status_code == 404


def test_moderator_post_auto_approved(client, mod_h):
    assert post(client, mod_h).json()["status"] == "approved"


def test_moderation_flow(client, student_h, mod_h):
    eid = post(client, student_h).json()["id"]
    assert client.get("/api/experiences/pending", headers=student_h).status_code == 403
    pending = client.get("/api/experiences/pending", headers=mod_h).json()
    assert [e["id"] for e in pending] == [eid]
    r = client.post(f"/api/experiences/{eid}/moderate", json={"approve": True}, headers=mod_h)
    assert r.json()["status"] == "approved"
    assert client.get("/api/experiences").json()["total"] == 1
    assert client.post("/api/experiences/999/moderate", json={"approve": True}, headers=mod_h).status_code == 404


def test_reject(client, student_h, mod_h):
    eid = post(client, student_h).json()["id"]
    r = client.post(f"/api/experiences/{eid}/moderate", json={"approve": False, "note": "spam"}, headers=mod_h)
    assert r.json()["status"] == "rejected"


def test_anonymous_hides_author(client, mod_h):
    assert post(client, mod_h, anonymous=True).json()["author"] == "Anonymous"
    assert post(client, mod_h).json()["author"] == "Mod"


@pytest.mark.parametrize("field,value", [("outcome", "maybe"), ("mode", "telepathy"), ("difficulty", 9),
                                         ("summary", "too short"), ("year", 1990)])
def test_validation(client, student_h, field, value):
    assert post(client, student_h, **{field: value}).status_code == 422


def test_browse_filters_and_sort(client, mod_h, student_h):
    a = post(client, mod_h).json()["id"]
    post(client, mod_h, company="Google", role_title="SDE", outcome="rejected", year=2025,
         summary="Graph heavy onsite rounds with a strong focus on dynamic programming and optimal code.")
    assert client.get("/api/experiences", params={"company": "amazon"}).json()["total"] == 1
    assert client.get("/api/experiences", params={"outcome": "rejected"}).json()["items"][0]["company"] == "Google"
    assert client.get("/api/experiences", params={"year": 2025}).json()["total"] == 1
    assert client.get("/api/experiences", params={"role": "intern"}).json()["total"] == 1
    assert client.get("/api/experiences", params={"q": "dynamic"}).json()["total"] == 1
    client.post(f"/api/experiences/{a}/vote", headers=student_h)
    assert client.get("/api/experiences", params={"sort": "top"}).json()["items"][0]["id"] == a
    assert client.get("/api/experiences", params={"sort": "bogus"}).status_code == 422
    page = client.get("/api/experiences", params={"size": 1, "page": 2}).json()
    assert page["total"] == 2 and len(page["items"]) == 1


def test_vote_toggle_and_self_vote(client, mod_h, student_h):
    eid = post(client, mod_h).json()["id"]
    assert client.post(f"/api/experiences/{eid}/vote", headers=student_h).json() == {"upvotes": 1, "voted": True}
    assert client.post(f"/api/experiences/{eid}/vote", headers=student_h).json() == {"upvotes": 0, "voted": False}
    assert client.post(f"/api/experiences/{eid}/vote", headers=mod_h).status_code == 409


def test_update_and_delete_permissions(client, student_h, student2_h, mod_h):
    eid = post(client, student_h).json()["id"]
    client.post(f"/api/experiences/{eid}/moderate", json={"approve": True}, headers=mod_h)
    assert client.patch(f"/api/experiences/{eid}", json={"outcome": "rejected"}, headers=student2_h).status_code == 403
    r = client.patch(f"/api/experiences/{eid}", json={"outcome": "rejected", "difficulty": 2}, headers=student_h)
    assert r.json()["outcome"] == "rejected" and r.json()["difficulty"] == 2
    assert client.delete(f"/api/experiences/{eid}", headers=student2_h).status_code == 403
    assert client.delete(f"/api/experiences/{eid}", headers=mod_h).status_code == 204
    assert client.get(f"/api/experiences/{eid}").status_code == 404


def test_mine(client, student_h):
    post(client, student_h)
    mine = client.get("/api/experiences/mine", headers=student_h).json()
    assert len(mine) == 1 and mine[0]["status"] == "pending"


def test_company_stats(client, mod_h):
    post(client, mod_h)
    post(client, mod_h, outcome="rejected", difficulty=2, role_title="SDE")
    post(client, mod_h, outcome="pending")
    s = client.get("/api/companies/Amazon/stats").json()
    assert s["experiences"] == 3 and s["selection_rate"] == 0.5
    assert s["avg_difficulty"] == round((4 + 2 + 4) / 3, 2)
    assert s["top_roles"][0] == "SDE Intern"
    assert s["question_count"] >= 1
    assert client.get("/api/companies/Nowhere/stats").status_code == 404
    assert any(c["slug"] == "amazon" for c in client.get("/api/companies").json())


def test_company_stats_empty_company(client, admin_h):
    client.post("/api/questions", json={"text": "Explain polymorphism with an example.", "topic": "oop",
                                        "company": "Zoho"}, headers=admin_h)
    s = client.get("/api/companies/zoho/stats").json()
    assert s["experiences"] == 0 and s["selection_rate"] == 0.0 and s["avg_difficulty"] == 0.0


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
