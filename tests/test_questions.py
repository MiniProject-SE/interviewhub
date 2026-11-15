"""Module 3 — Question Bank API tests (FR-3.x)."""


def test_meta(client, seeded):
    m = client.get("/api/questions/meta").json()
    assert "dsa" in m["topics"] and m["counts"]["os"] == 2


def test_create_requires_login_and_validates(client, admin_h):
    q = {"text": "Explain how a hash map handles collisions.", "topic": "dsa"}
    assert client.post("/api/questions", json=q).status_code == 401
    assert client.post("/api/questions", json={**q, "topic": "cooking"}, headers=admin_h).status_code == 422
    assert client.post("/api/questions", json={**q, "difficulty": "insane"}, headers=admin_h).status_code == 422
    assert client.post("/api/questions", json={**q, "text": "short"}, headers=admin_h).status_code == 422
    r = client.post("/api/questions", json={**q, "tags": [" Hashing ", "hashing", "", "a,b"]}, headers=admin_h)
    assert r.status_code == 201 and r.json()["tags"] == ["hashing"]


def test_duplicate_is_merged(client, seeded, student_h):
    r = client.post("/api/questions", json={"text": "Explain the difference between process and thread",
                                            "topic": "os", "company": "Infosys"}, headers=student_h)
    assert r.status_code == 200
    assert r.headers["X-Duplicate-Merged"] == "true"
    assert r.json()["times_asked"] == 2 and r.json()["id"] == seeded[0]


def test_different_question_not_merged(client, seeded, student_h):
    r = client.post("/api/questions", json={"text": "Explain paging and segmentation in memory management.",
                                            "topic": "os"}, headers=student_h)
    assert r.status_code == 201 and r.headers["X-Duplicate-Merged"] == "false"


def test_search_filters(client, seeded):
    assert client.get("/api/questions").json()["total"] == 6
    assert client.get("/api/questions", params={"topic": "dsa"}).json()["total"] == 2
    assert client.get("/api/questions", params={"difficulty": "easy"}).json()["total"] == 3
    assert client.get("/api/questions", params={"company": "Google"}).json()["total"] == 1
    assert client.get("/api/questions", params={"role": "intern"}).json()["total"] == 1
    assert client.get("/api/questions", params={"q": "deadlock"}).json()["total"] == 1
    assert client.get("/api/questions", params={"q": "graph"}).json()["total"] == 1  # matches tag
    page = client.get("/api/questions", params={"size": 4, "page": 2}).json()
    assert len(page["items"]) == 2


def test_detail_includes_model_answer(client, seeded):
    d = client.get(f"/api/questions/{seeded[0]}").json()
    assert d["has_model_answer"] and "address space" in d["model_answer"]
    assert client.get("/api/questions/9999").status_code == 404


def test_update_permissions(client, seeded, student_h, admin_h):
    assert client.patch(f"/api/questions/{seeded[0]}", json={"difficulty": "hard"}, headers=student_h).status_code == 403
    r = client.patch(f"/api/questions/{seeded[0]}", json={"difficulty": "hard", "tags": ["OS"]}, headers=admin_h)
    assert r.json()["difficulty"] == "hard" and r.json()["tags"] == ["os"]
    own = client.post("/api/questions", json={"text": "What is a semaphore and how is it used?", "topic": "os"},
                      headers=student_h).json()["id"]
    assert client.patch(f"/api/questions/{own}", json={"model_answer": "counter + wait/signal"},
                        headers=student_h).status_code == 200
    assert client.patch(f"/api/questions/{own}", json={"difficulty": None}, headers=student_h).status_code == 200


def test_delete_only_moderators(client, seeded, student_h, mod_h):
    assert client.delete(f"/api/questions/{seeded[1]}", headers=student_h).status_code == 403
    assert client.delete(f"/api/questions/{seeded[1]}", headers=mod_h).status_code == 204
    assert client.get(f"/api/questions/{seeded[1]}").status_code == 404
