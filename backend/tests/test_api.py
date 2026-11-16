def post(client, message, **kwargs):
    return client.post("/chat", json={"session_id": "s1", "message": message}, **kwargs)


def test_health(client):
    assert client.get("/health").json() == {"status": "ok", "provider": "offline"}


def test_schedule_in_english(client):
    body = post(client, "What is my schedule?").json()
    assert body["tools_used"] == ["get_schedule"]
    assert "B-204" in body["reply"]


def test_grade_history_in_spanish(client):
    body = post(client, "Quiero mi historial de calificaciones").json()
    assert body["tools_used"] == ["get_grade_history"]
    assert "Tu historial" in body["reply"]


def test_specific_semester(client):
    body = post(client, "grades from semester 4").json()
    assert "Operating Systems" in body["reply"] and "Algorithms" not in body["reply"]


def test_social_service(client):
    assert "240 remaining" in post(client, "social service status").json()["reply"]


def test_request_flow(client):
    body = post(client, "Please request an enrollment certificate").json()
    assert body["tools_used"] == ["submit_service_request"]
    assert "REQ-0001" in body["reply"]


def test_small_talk_uses_no_tools(client):
    body = post(client, "tell me a joke").json()
    assert body["tools_used"] == []


def test_unknown_student_is_rejected(client):
    assert post(client, "hi", headers={"X-Student-Id": "nobody"}).status_code == 401


def test_validation(client):
    assert client.post("/chat", json={"session_id": "s1", "message": ""}).status_code == 422


def test_history_is_trimmed_to_whole_pairs(client):
    from app import main

    for _ in range(15):
        post(client, "schedule")
    history = main._sessions["A0001:s1"]
    assert len(history) <= main.MAX_HISTORY_TURNS and history[0]["role"] == "user"
