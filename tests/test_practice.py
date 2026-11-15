"""Module 4 — Mock Interview & Performance Tracking tests (FR-4.x)."""
from datetime import datetime, timedelta, timezone

import pytest

from app.modules.practice import scorer, service
from app.modules.practice.models import PracticeSession

GOOD = ("A process has its own address space while a thread shares memory inside the process. "
        "Thread context switch is cheaper and needs synchronization such as a mutex to avoid races in practice.")


def start(client, h, **kw):
    body = {"num_questions": 3, "duration_minutes": 30, **kw}
    return client.post("/api/practice/sessions", json=body, headers=h)


# ---------- scorer unit tests ----------

def test_extract_keywords_tags_first_and_deduped():
    kws = scorer.extract_keywords("q", "threads threads process memory", "thread,os")
    assert kws[0] == "thread" and "threads" not in kws and "process" in kws
    assert len(scorer.extract_keywords("x", " ".join(f"word{i}" for i in range(30)), None)) == scorer.MAX_KEYWORDS


def test_extract_keywords_falls_back_to_question():
    assert "deadlock" in scorer.extract_keywords("Explain deadlock prevention", None, None)


def test_score_empty_answer():
    r = scorer.score_answer("   ", ["a"])
    assert r.auto_score == 0 and r.feedback == "No answer was given."


def test_score_good_vs_poor():
    kws = ["process", "thread", "memory", "mutex"]
    good = scorer.score_answer(GOOD, kws)
    poor = scorer.score_answer("No idea really.", kws)
    assert good.auto_score >= 80 and "Strong" in good.feedback
    assert poor.auto_score < 50 and "Needs work" in poor.feedback and "elaborate" in poor.feedback
    assert set(poor.missed) == set(kws)


def test_score_middle_band_and_stemming():
    r = scorer.score_answer("processes threads memory " * 5, ["process", "thread", "memory", "mutex"])
    assert 50 <= r.auto_score < 80 and "gaps" in r.feedback
    assert r.covered == ["process", "thread", "memory"] and r.missed == ["mutex"]
    assert scorer._stem("process") == "process" and scorer._stem("classes") == "class"


def test_score_no_keywords():
    assert scorer.score_answer("anything at all", []).auto_score > 0


def test_combine():
    assert scorer.combine(80, None) == 80
    assert scorer.combine(80, 5) == round(0.7 * 80 + 30, 1)


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
    item = next(i for i in s["items"] if "process" in i["question"].lower())
    r = client.post(f"/api/practice/sessions/{s['id']}/items/{item['item_id']}/answer",
                    json={"answer_text": GOOD, "self_rating": 4, "time_taken_sec": 90}, headers=student_h)
    assert r.status_code == 200
    a = r.json()
    assert a["answered"] and a["auto_score"] > 60 and a["final_score"] == scorer.combine(a["auto_score"], 4)
    done = client.post(f"/api/practice/sessions/{s['id']}/finish", headers=student_h).json()
    assert done["state"] == "completed"
    assert done["total_score"] == round(a["final_score"] / 2, 1)  # unanswered counts as 0
    assert all(i["model_answer"] for i in done["items"])  # revealed after finish
    # closed sessions reject further answers / finishes
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
    assert got["state"] == "expired" and got["seconds_remaining"] == 0 and got["total_score"] == 0.0


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


# ---------- analytics ----------

def test_analytics_empty(client, student_h):
    a = client.get("/api/practice/analytics", headers=student_h).json()
    assert a["sessions_completed"] == 0 and a["average_score"] == 0 and a["trend"] == []


def _complete(client, h, topic, answer, **kw):
    s = start(client, h, topic=topic, num_questions=1, focus_weak_topics=False, **kw).json()
    i = s["items"][0]
    client.post(f"/api/practice/sessions/{s['id']}/items/{i['item_id']}/answer",
                json={"answer_text": answer, "time_taken_sec": 120}, headers=h)
    return client.post(f"/api/practice/sessions/{s['id']}/finish", headers=h).json()


def test_analytics_weak_strong_trend(client, seeded, student_h):
    _complete(client, student_h, "dbms", "no idea")
    _complete(client, student_h, "os", GOOD, company="Infosys")
    a = client.get("/api/practice/analytics", headers=student_h).json()
    assert a["sessions_completed"] == 2 and a["questions_answered"] == 2
    assert a["weak_topics"] == ["dbms"] and "os" in a["strong_topics"]
    assert a["topics"][0]["topic"] == "dbms"  # sorted weakest first
    assert len(a["trend"]) == 2 and a["improvement"] > 0
    assert a["total_practice_minutes"] == 4.0 and a["current_streak_days"] == 1
    assert a["best_score"] >= a["average_score"]


def test_weak_topic_focus_biases_next_session(client, seeded, student_h):
    _complete(client, student_h, "dbms", "no idea")
    s = start(client, student_h, num_questions=1).json()  # focus_weak_topics defaults True; dbms already seen
    assert s["items"]


@pytest.mark.parametrize("offsets,expected", [([], 0), ([0], 1), ([0, 1, 2], 3), ([1, 2], 2), ([0, 2], 1), ([3], 0)])
def test_streak_days(offsets, expected):
    today = datetime(2026, 11, 15, 12, tzinfo=timezone.utc)
    dates = [(today - timedelta(days=o)).replace(tzinfo=None) for o in offsets]
    assert service.streak_days(dates, today) == expected


def test_seconds_remaining_closed_session():
    s = PracticeSession(state="completed", duration_minutes=10, started_at=datetime.now(timezone.utc))
    assert service.seconds_remaining(s) == 0
