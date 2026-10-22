"""Quick local start (no Docker, no PostgreSQL needed).

    python run_local.py

- Uses DATABASE_URL from .env if present, otherwise a local SQLite file (communiai_local.db).
- Creates/updates the database schema (Alembic), then starts the API on 0.0.0.0:8000.
- Prints the address to enter in the mobile app ("Server manzili").
For production use PostgreSQL + HTTPS (see README / docker-compose.yml).
"""
import os
import secrets
import socket
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.chdir(HERE)
sys.path.insert(0, str(HERE))


def _set_env_value(key: str, value: str) -> None:
    """Write KEY=value into backend/.env (replacing an existing line)."""
    env = HERE / ".env"
    lines = env.read_text(encoding="utf-8").splitlines() if env.exists() else []
    out, done = [], False
    for line in lines:
        if line.strip().startswith(key + "="):
            out.append(f"{key}={value}")
            done = True
        else:
            out.append(line)
    if not done:
        out.append(f"{key}={value}")
    env.write_text("\n".join(out) + "\n", encoding="utf-8")


def _check_ai_key(key: str) -> str:
    """Return a short human-readable status of the key (one cheap API call)."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key, timeout=20.0, max_retries=0)
        client.models.list(limit=1)
        return "OK"
    except Exception as e:  # noqa: BLE001
        name = type(e).__name__
        if name == "AuthenticationError":
            return "KALIT NOTO'G'RI (Anthropic kalitni qabul qilmadi)"
        if name == "PermissionDeniedError":
            return "KALITGA RUXSAT YO'Q (hisobni/balansni tekshiring)"
        if name in ("APIConnectionError", "APITimeoutError"):
            return "INTERNETGA ULANIB BO'LMADI (kalit tekshirilmadi)"
        return f"TEKSHIRIB BO'LMADI ({name})"


def _ensure_ai_key() -> None:
    """Ask for the Anthropic API key on first start (interactive console only) and save it to .env."""
    if os.environ.get("AI_API_KEY") or _env_file_has("AI_API_KEY"):
        return
    if not sys.stdin or not sys.stdin.isatty():
        return
    print("\n" + "-" * 64)
    print(" AI funksiyalari uchun Anthropic API kaliti kerak.")
    print(" Kalitni olish: https://console.anthropic.com  ->  API Keys  ->  Create Key")
    print(" Kalit 'sk-ant-' bilan boshlanadi. Hozir kiritmasangiz, Enter bosing (AI o'chiq bo'ladi).")
    print("-" * 64)
    try:
        key = input(" API kalit: ").strip()
    except (EOFError, KeyboardInterrupt):
        return
    if not key:
        return
    if not key.startswith("sk-ant-"):
        print(" Ogohlantirish: kalit odatda 'sk-ant-' bilan boshlanadi. Baribir saqlanmoqda.")
    _set_env_value("AI_API_KEY", key)
    os.environ["AI_API_KEY"] = key
    print(" Kalit backend/.env fayliga saqlandi.")


def _env_file_has(key: str) -> bool:
    env = HERE / ".env"
    return env.exists() and any(line.strip().startswith(key + "=") and line.split("=", 1)[1].strip()
                                for line in env.read_text(encoding="utf-8").splitlines())


if not os.environ.get("DATABASE_URL") and not _env_file_has("DATABASE_URL"):
    os.environ["DATABASE_URL"] = f"sqlite:///{(HERE / 'communiai_local.db').as_posix()}"
if not os.environ.get("JWT_SECRET") and not _env_file_has("JWT_SECRET"):
    secret_file = HERE / ".local_jwt_secret"
    if not secret_file.exists():
        secret_file.write_text(secrets.token_urlsafe(48), encoding="utf-8")
    os.environ["JWT_SECRET"] = secret_file.read_text(encoding="utf-8").strip()
os.environ.setdefault("LOCAL_STORAGE_DIR", str(HERE / "storage"))


def lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def main() -> None:
    from alembic import command
    from alembic.config import Config

    _ensure_ai_key()
    command.upgrade(Config(str(HERE / "alembic.ini")), "head")

    from app.core.config import get_settings
    s = get_settings()
    ai_status = _check_ai_key(s.AI_API_KEY) if s.ai_configured else None
    ip = lan_ip()
    print("\n" + "=" * 64)
    print(" CommuniAI backend ishga tushdi")
    print(f"   Telefon ilovasida 'Server manzili':  http://{ip}:8000")
    print("   Android emulator uchun:              http://10.0.2.2:8000")
    print("   API hujjatlari (brauzerda):          http://localhost:8000/docs")
    print(f"   Ma'lumotlar bazasi: {'SQLite (lokal fayl)' if s.DATABASE_URL.startswith('sqlite') else 'PostgreSQL'}")
    if not s.ai_configured:
        print("   DIQQAT: AI_API_KEY sozlanmagan — AI funksiyalar 'sozlanmagan' deb javob beradi.")
        print("           backend/.env fayliga AI_API_KEY=sk-ant-... yozing va qayta ishga tushiring.")
    else:
        print(f"   AI kaliti: {ai_status}   (model: {s.AI_MODEL})")
    print("   Telefon ulanmasa: telefon brauzerida yuqoridagi manzil + /health/ready ni oching.")
    print("   Windows Firewall so'rasa — 'Ruxsat berish' ni bosing.")
    print("   To'xtatish: Ctrl+C")
    print("=" * 64 + "\n")

    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()
