from conftest import PASSWORD, create_project, register


def test_register_and_me(client):
    headers, tok = register(client, consent=False)
    assert tok["user"]["email"] == "talaba@example.uz"
    r = client.get("/api/v1/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["role"] == "student"


def test_register_duplicate_and_validation(client):
    register(client)
    r = client.post("/api/v1/auth/register", json={
        "first_name": "A", "last_name": "B", "email": "talaba@example.uz", "password": PASSWORD,
        "password_confirm": PASSWORD, "university": "TATU", "study_program": "AT"})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "EMAIL_TAKEN"


def test_weak_password_rejected(client):
    for pw in ("short", "password123", "1234567890"):
        r = client.post("/api/v1/auth/register", json={
            "first_name": "A", "last_name": "B", "email": "x@example.uz", "password": pw,
            "password_confirm": pw, "university": "TATU", "study_program": "AT"})
        assert r.status_code == 422, pw
        assert r.json()["error"]["code"] == "WEAK_PASSWORD"


def test_password_mismatch(client):
    r = client.post("/api/v1/auth/register", json={
        "first_name": "A", "last_name": "B", "email": "x@example.uz", "password": PASSWORD,
        "password_confirm": PASSWORD + "x", "university": "TATU", "study_program": "AT"})
    assert r.status_code == 422


def test_login_and_wrong_password(client):
    register(client)
    ok = client.post("/api/v1/auth/login", json={"email": "TALABA@example.uz", "password": PASSWORD})
    assert ok.status_code == 200
    bad = client.post("/api/v1/auth/login", json={"email": "talaba@example.uz", "password": "noto'g'ri-parol"})
    assert bad.status_code == 401
    assert bad.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_refresh_rotation_and_reuse_detection(client):
    _, tok = register(client)
    r1 = client.post("/api/v1/auth/refresh", json={"refresh_token": tok["refresh_token"]})
    assert r1.status_code == 200
    new = r1.json()
    assert new["refresh_token"] != tok["refresh_token"]
    # Reusing the rotated token revokes the whole family
    reuse = client.post("/api/v1/auth/refresh", json={"refresh_token": tok["refresh_token"]})
    assert reuse.status_code == 401
    after = client.post("/api/v1/auth/refresh", json={"refresh_token": new["refresh_token"]})
    assert after.status_code == 401


def test_logout_revokes_refresh(client):
    headers, tok = register(client)
    assert client.post("/api/v1/auth/logout", json={"refresh_token": tok["refresh_token"]},
                       headers=headers).status_code == 204
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": tok["refresh_token"]}).status_code == 401


def test_unauthenticated_and_bad_token(client):
    assert client.get("/api/v1/projects").status_code == 401
    r = client.get("/api/v1/projects", headers={"Authorization": "Bearer abc.def.ghi"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHORIZED"


def test_other_users_resources_are_hidden(client):
    h1, _ = register(client, "a@example.uz")
    h2, _ = register(client, "b@example.uz")
    p = create_project(client, h1)
    assert client.get(f"/api/v1/projects/{p['id']}", headers=h2).status_code == 404
    assert client.patch(f"/api/v1/projects/{p['id']}", json={"title": "Hack"}, headers=h2).status_code == 404
    assert client.delete(f"/api/v1/projects/{p['id']}", headers=h2).status_code == 404
    assert client.get(f"/api/v1/projects/{p['id']}/files", headers=h2).status_code == 404
    assert client.get("/api/v1/projects", headers=h2).json()["total"] == 0


def test_password_reset_reports_unavailable_without_email(client):
    register(client)
    r = client.post("/api/v1/auth/password-reset/request", json={"email": "talaba@example.uz"})
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "EMAIL_NOT_CONFIGURED"


def test_password_reset_flow_with_email(client, monkeypatch):
    from app.core.config import get_settings
    from app.api.v1 import auth as auth_mod
    s = get_settings()
    monkeypatch.setattr(s, "SMTP_HOST", "smtp.test")
    monkeypatch.setattr(s, "SMTP_FROM", "noreply@test")
    sent = {}
    monkeypatch.setattr(auth_mod, "send_email", lambda to, subj, body: sent.update(to=to, body=body))
    register(client)
    assert client.post("/api/v1/auth/password-reset/request", json={"email": "talaba@example.uz"}).status_code == 202
    token = sent["body"].split("kodi:\n\n")[1].split("\n")[0]
    new_pw = "Yangi-Kuchli-Parol-77"
    r = client.post("/api/v1/auth/password-reset/confirm",
                    json={"token": token, "new_password": new_pw, "new_password_confirm": new_pw})
    assert r.status_code == 200
    assert client.post("/api/v1/auth/login", json={"email": "talaba@example.uz", "password": new_pw}).status_code == 200
    # token is single-use
    assert client.post("/api/v1/auth/password-reset/confirm",
                       json={"token": token, "new_password": new_pw, "new_password_confirm": new_pw}).status_code == 400
