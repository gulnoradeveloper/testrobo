import uuid

from app.core.database import SessionLocal
from app.models import User, UserRole
from conftest import create_project, register


def _make_admin(tok):
    with SessionLocal() as db:
        u = db.get(User, uuid.UUID(tok["user"]["id"]))
        u.role = UserRole.ADMIN
        db.commit()


def test_health(client):
    assert client.get("/health/live").json() == {"status": "ok"}
    r = client.get("/health/ready")
    assert r.status_code == 200 and r.json()["checks"]["database"] == "ok"


def test_openapi_lists_endpoints(client):
    paths = client.get("/openapi.json").json()["paths"]
    for p in ("/api/v1/auth/register", "/api/v1/projects/{project_id}/analyze", "/api/v1/defenses/{session_id}/answers",
              "/api/v1/practice-plans/{plan_id}/progress", "/api/v1/me/competencies", "/health/ready"):
        assert p in paths


def test_error_format_and_request_id(client):
    r = client.get("/api/v1/projects/not-a-uuid", headers=register(client)[0])
    assert r.status_code == 422
    assert set(r.json()["error"]) >= {"code", "message"}
    assert r.headers.get("X-Request-ID")


def test_pagination(client):
    h, _ = register(client)
    for i in range(3):
        create_project(client, h, title=f"Loyiha {i}")
    r = client.get("/api/v1/projects?page=2&page_size=2", headers=h).json()
    assert r["total"] == 3 and len(r["items"]) == 1 and r["page"] == 2
    assert client.get("/api/v1/projects?page_size=500", headers=h).status_code == 422


def test_rate_limit(client, monkeypatch):
    from app.core.config import get_settings
    monkeypatch.setattr(get_settings(), "AUTH_RATE_LIMIT_PER_MINUTE", 3)
    codes = [client.post("/api/v1/auth/login", json={"email": "x@example.uz", "password": "p"}).status_code
             for _ in range(5)]
    assert codes[:3] == [401, 401, 401] and codes[3] == 429


def test_admin_requires_role_and_hides_content(client):
    h, tok = register(client, "admin@example.uz")
    assert client.get("/api/v1/admin/users", headers=h).status_code == 403
    _make_admin(tok)
    hs, _ = register(client, "s@example.uz")
    p = create_project(client, hs)
    users = client.get("/api/v1/admin/users", headers=h).json()
    assert users["total"] == 2
    assert "description" not in str(users)  # no project content in user list
    assert client.get("/api/v1/admin/system", headers=h).json()["database"] == "ok"
    # content access needs the student's permission and is audited
    r = client.post(f"/api/v1/admin/projects/{p['id']}/access", json={"reason": "Fayl yuklash xatosini tekshirish"},
                    headers=h)
    assert r.status_code == 403
    client.patch("/api/v1/me", json={"support_access_days": 1}, headers=hs)
    r = client.post(f"/api/v1/admin/projects/{p['id']}/access", json={"reason": "Fayl yuklash xatosini tekshirish"},
                    headers=h)
    assert r.status_code == 200
    logs = client.get("/api/v1/admin/audit-logs", headers=h).json()["items"]
    assert {"admin.project_access", "admin.project_access_denied"} <= {l["action"] for l in logs}


def test_meta_does_not_expose_secrets(client):
    m = client.get("/api/v1/meta").json()
    assert "AI_API_KEY" not in str(m) and "secret" not in str(m).lower()
