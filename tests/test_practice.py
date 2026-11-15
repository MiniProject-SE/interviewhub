"""Module 4 — Mock Interview session tests (FR-4.1, 4.2, 4.5, 4.7)."""
from datetime import datetime, timedelta, timezone

from app.modules.practice import service
from app.modules.practice.models import PracticeSession

GOOD = ("A process has its own address space while a thread shares memory inside the process. "
        "Thread context switch is cheaper and needs synchronization such as a mutex to avoid races in practice.")


def start(client, h, **kw):
    body = {"num_questions": 3, "duration_minutes": 30, **kw}
    return client.post("/api/practice/sessions", json=body, headers=h)


# ---------- session lifecycle ----------

def test_start_requires_login(client, seeded):
    assert client.post("/api/practice/sessions", json={}).status_code == 401


def test_start_session(client, seeded, student_h):
    r = start(client, student_h, topic="os", num_questions=2)
    assert r.status_code == 201
    s = r.json()
    assert s["state"] == "in_progress" and len(s["items"]) == 2
    assert all(i["topic"] == "os" for i in s["items"])
    assert all(i["model_answer"] is None for i in s["items"])  # hidden while live
    assert 0 < s["seconds_remaining"] <= 1800


def test_start_no_matching_questions(client, seeded, student_h):
    r = start(client, student_h, topic="ml")
    assert r.status_code == 422


def test_start_validation(client, seeded, student_h):
    assert start(client, student_h, num_questions=0).status_code == 422
    assert start(client, student_h, duration_minutes=1).status_code == 422


def test_answer_and_finish(client, seeded, student_h):
    s = start(client, student_h, topic="os", num_questions=2).json()
    item = s["items"][0]
    r = client.post(f"/api/practice/sessions/{s['id']}/items/{item['item_id']}/answer",
                    json={"answer_text": GOOD, "self_rating": 4, "time_taken_sec": 90}, headers=student_h)
    assert r.status_code == 200
    a = r.json()
    assert a["answered"] and a["answer_text"] == GOOD and a["self_rating"] == 4
    done = client.post(f"/api/practice/sessions/{s['id']}/finish", headers=student_h).json()
    assert done["state"] == "completed" and done["ended_at"]
    assert all(i["model_answer"] for i in done["items"])  # revealed after finish
    assert client.post(f"/api/practice/sessions/{s['id']}/items/{item['item_id']}/answer",
                       json={"answer_text": "late"}, headers=student_h).status_code == 409
    assert client.post(f"/api/practice/sessions/{s['id']}/finish", headers=student_h).status_code == 409


def test_answer_wrong_item_or_other_user(client, seeded, student_h, student2_h):
    s = start(client, student_h).json()
    assert client.post(f"/api/practice/sessions/{s['id']}/items/9999/answer",
                       json={"answer_text": "x"}, headers=student_h).status_code == 404
    assert client.get(f"/api/practice/sessions/{s['id']}", headers=student2_h).status_code == 404
    assert client.post(f"/api/practice/sessions/{s['id']}/items/{s['items'][0]['item_id']}/answer",
                       json={"answer_text": "x", "self_rating": 9}, headers=student_h).status_code == 422


def test_session_expires(client, seeded, student_h, db):
    s = start(client, student_h, duration_minutes=5).json()
    row = db.get(PracticeSession, s["id"])
    row.started_at = datetime.now(timezone.utc) - timedelta(minutes=10)
    db.commit()
    got = client.get(f"/api/practice/sessions/{s['id']}", headers=student_h).json()
    assert got["state"] == "expired" and got["seconds_remaining"] == 0


def test_prefers_unseen_questions_then_allows_repeats(client, seeded, student_h):
    first = start(client, student_h, topic="os", num_questions=1).json()
    item = first["items"][0]
    client.post(f"/api/practice/sessions/{first['id']}/items/{item['item_id']}/answer",
                json={"answer_text": GOOD}, headers=student_h)
    second = start(client, student_h, topic="os", num_questions=1).json()
    assert second["items"][0]["question_id"] != item["question_id"]
    third = start(client, student_h, topic="os", num_questions=2).json()  # only 2 os questions exist
    assert len(third["items"]) == 2


def test_history(client, seeded, student_h):
    start(client, student_h)
    start(client, student_h, topic="dsa", num_questions=1)
    h = client.get("/api/practice/sessions", headers=student_h).json()
    assert len(h) == 2 and h[0]["topic"] == "dsa"


def test_seconds_remaining_closed_session():
    s = PracticeSession(state="completed", duration_minutes=10, started_at=datetime.now(timezone.utc))
    assert service.seconds_remaining(s) == 0
