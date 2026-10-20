from app.services.ai.provider import AITimeoutError
from conftest import create_project, register


def _new_defense(client, h, pid, mode="hackathon", limit=5, key=None):
    headers = dict(h)
    if key:
        headers["Idempotency-Key"] = key
    r = client.post("/api/v1/defenses", json={"project_id": pid, "mode": mode, "question_limit": limit},
                    headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def _answer_all(client, h, sid, n):
    for i in range(n):
        q = client.get(f"/api/v1/defenses/{sid}/current-question", headers=h).json()["question"]
        assert q is not None, i
        r = client.post(f"/api/v1/defenses/{sid}/answers",
                        json={"question_id": q["id"],
                              "answer_text": f"Javob {i + 1}: navbat raqami PostgreSQL ketma-ketligi va unique "
                                             f"cheklov bilan beriladi, shuning uchun takrorlanmaydi."}, headers=h)
        assert r.status_code == 202, r.text


def test_full_defense_flow(client, ai):
    h, _ = register(client)
    p = create_project(client, h)
    d = _new_defense(client, h, p["id"])
    assert d["status"] == "CREATED"
    s = client.post(f"/api/v1/defenses/{d['id']}/start", headers=h).json()
    assert s["status"] == "IN_PROGRESS" and s["current_question"] is not None
    assert "SmartQueue" in s["current_question"]["question_text"]
    _answer_all(client, h, d["id"], 5)
    cur = client.get(f"/api/v1/defenses/{d['id']}/current-question", headers=h).json()
    assert cur["question"] is None and cur["progress"]["answered"] == 5
    assert cur["last_feedback"]["feedback"]["model_answer"]
    # dynamic: later questions are built from previous answers
    q_calls = [c for c in ai.calls if c["schema"] == "QuestionOut"]
    assert len(q_calls) == 5 and "Javob 1:" in q_calls[1]["user"]
    done = client.post(f"/api/v1/defenses/{d['id']}/complete", headers=h).json()
    assert done["status"] == "EVALUATED"
    res = client.get(f"/api/v1/defenses/{d['id']}/results", headers=h).json()["result"]
    assert res["rubric_version"] == "1.0"
    crit = {c["code"]: c for c in res["criteria"]}
    assert crit["K6"]["assessed"] is False and crit["K6"]["score"] is None
    assert res["max_applicable_score"] == 90  # K6 not applicable yet
    assert res["total_score"] == 14 * 3 + 10 * 2
    assert res["coverage"] == 0.9
    assert res["level"] == "Shakllanayotgan"  # 62/90 = 68.9%
    assert res["readiness"]["assessed"] is True and res["readiness"]["percent"] == 60.0


def test_answers_are_immutable_and_order_enforced(client, ai):
    h, _ = register(client)
    p = create_project(client, h)
    d = _new_defense(client, h, p["id"])
    client.post(f"/api/v1/defenses/{d['id']}/start", headers=h)
    q1 = client.get(f"/api/v1/defenses/{d['id']}/current-question", headers=h).json()["question"]
    body = {"question_id": q1["id"], "answer_text": "Birinchi javob matni."}
    assert client.post(f"/api/v1/defenses/{d['id']}/answers", json=body, headers=h).status_code == 202
    dup = client.post(f"/api/v1/defenses/{d['id']}/answers", json=body, headers=h)
    assert dup.status_code == 202 and dup.json()["duplicate"] is True
    changed = client.post(f"/api/v1/defenses/{d['id']}/answers",
                          json={"question_id": q1["id"], "answer_text": "O'zgartirilgan"}, headers=h)
    assert changed.status_code == 409 and changed.json()["error"]["code"] == "ANSWER_LOCKED"
    assert client.post(f"/api/v1/defenses/{d['id']}/complete", headers=h).status_code == 409


def test_idempotent_session_creation(client, ai):
    h, _ = register(client)
    p = create_project(client, h)
    a = _new_defense(client, h, p["id"], key="abc-123")
    b = _new_defense(client, h, p["id"], key="abc-123")
    assert a["id"] == b["id"]
    assert client.get("/api/v1/defenses", headers=h).json()["total"] == 1


def test_resume_after_ai_outage(client, ai):
    h, _ = register(client)
    p = create_project(client, h)
    d = _new_defense(client, h, p["id"])
    ai.push("QuestionOut", AITimeoutError("t"))  # timeouts are retried inside the SDK, not again by us
    s = client.post(f"/api/v1/defenses/{d['id']}/start", headers=h).json()
    assert s["status"] == "IN_PROGRESS" and s["current_question"] is None
    assert s["last_failed_job"]["error_code"] == "AI_TIMEOUT"
    assert s["pending_work"] == "defense_question"
    s = client.post(f"/api/v1/defenses/{d['id']}/resume", headers=h).json()
    assert s["current_question"] is not None

    # evaluation failure keeps the answer; resume evaluates it later
    q = s["current_question"]
    ai.push("AnswerEvaluationOut", AITimeoutError("t"))
    client.post(f"/api/v1/defenses/{d['id']}/answers", json={"question_id": q["id"], "answer_text": "Saqlangan javob"},
                headers=h)
    s = client.get(f"/api/v1/defenses/{d['id']}", headers=h).json()
    assert s["questions"][0]["answer"]["answer_text"] == "Saqlangan javob"
    assert s["questions"][0]["answer"]["evaluation"] is None
    assert s["pending_work"] == "defense_answer"
    s = client.post(f"/api/v1/defenses/{d['id']}/resume", headers=h).json()
    assert s["questions"][0]["answer"]["evaluation"] is not None
    assert len(s["questions"]) == 2


def test_final_evaluation_failure_is_retryable(client, ai):
    h, _ = register(client)
    p = create_project(client, h)
    d = _new_defense(client, h, p["id"])
    client.post(f"/api/v1/defenses/{d['id']}/start", headers=h)
    _answer_all(client, h, d["id"], 5)
    ai.push("FinalCoachOut", AITimeoutError("t"))
    s = client.post(f"/api/v1/defenses/{d['id']}/complete", headers=h).json()
    assert s["status"] == "FAILED" and s["failure_reason"]
    s = client.post(f"/api/v1/defenses/{d['id']}/complete", headers=h).json()
    assert s["status"] == "EVALUATED"


def test_sessions_are_isolated(client, ai):
    h1, _ = register(client, "a@example.uz")
    h2, _ = register(client, "b@example.uz")
    p = create_project(client, h1)
    d = _new_defense(client, h1, p["id"])
    client.post(f"/api/v1/defenses/{d['id']}/start", headers=h1)
    q = client.get(f"/api/v1/defenses/{d['id']}/current-question", headers=h1).json()["question"]
    for path in ("", "/current-question", "/results"):
        assert client.get(f"/api/v1/defenses/{d['id']}{path}", headers=h2).status_code == 404
    r = client.post(f"/api/v1/defenses/{d['id']}/answers", json={"question_id": q["id"], "answer_text": "x"}, headers=h2)
    assert r.status_code == 404
    assert client.post("/api/v1/defenses", json={"project_id": p["id"], "mode": "client"}, headers=h2).status_code == 404
    assert client.get("/api/v1/defenses", headers=h2).json()["total"] == 0


def test_cancel_and_invalid_transitions(client, ai):
    h, _ = register(client)
    p = create_project(client, h)
    d = _new_defense(client, h, p["id"])
    assert client.post(f"/api/v1/defenses/{d['id']}/cancel", headers=h).json()["status"] == "CANCELLED"
    r = client.post(f"/api/v1/defenses/{d['id']}/start", headers=h)
    assert r.status_code == 409 and r.json()["error"]["code"] == "INVALID_STATE"


def test_practice_before_after(client, ai):
    h, _ = register(client)
    p = create_project(client, h)
    d = _new_defense(client, h, p["id"])
    client.post(f"/api/v1/defenses/{d['id']}/start", headers=h)
    _answer_all(client, h, d["id"], 5)
    client.post(f"/api/v1/defenses/{d['id']}/complete", headers=h)
    plan = client.post("/api/v1/practice-plans", json={"session_id": d["id"]}, headers=h).json()
    assert sorted(plan["target_competencies"]) == ["K4", "K5"]  # weakest two (10/15 = 66.7%)
    assert len(plan["exercises"]) == 2
    a = client.post(f"/api/v1/practice-plans/{plan['id']}/attempts",
                    json={"exercise_index": 0, "revised_answer": "Yaxshilangan javob: avval savolni qayta ifodalayman, "
                                                                   "so'ng uch dalil bilan javob beraman."},
                    headers=h).json()
    assert a["status"] == "evaluated"
    prog = client.get(f"/api/v1/practice-plans/{plan['id']}/progress", headers=h).json()
    row = prog["rows"][0]
    assert row["before"] == 10 and row["after"] == 13 and row["delta"] == 3
    assert row["reflection"]["assessed"] is True and row["reflection"]["code"] == "K6"
    comp = client.get("/api/v1/me/competencies", headers=h).json()
    assert comp["by_criterion"]["K6"][0]["percent"] == 80.0
    progress = client.get("/api/v1/me/progress", headers=h).json()
    assert len(progress["sessions"]) == 1 and progress["practice"][0]["delta"] == 3


def test_dashboard_history_export_delete(client, ai):
    h, _ = register(client)
    p = create_project(client, h)
    dash = client.get("/api/v1/me/dashboard", headers=h).json()
    assert dash["projects_count"] == 1 and dash["completed_defenses"] == 0
    hist = client.get("/api/v1/me/history", headers=h).json()
    assert any(i["action"] == "project.create" for i in hist["items"])
    exp = client.get("/api/v1/me/export", headers=h).json()
    assert exp["projects"][0]["title"] == p["title"]
    assert client.delete("/api/v1/me", headers=h).status_code == 204
    assert client.get("/api/v1/auth/me", headers=h).status_code == 401
