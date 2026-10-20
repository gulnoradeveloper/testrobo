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

    command.upgrade(Config(str(HERE / "alembic.ini")), "head")

    from app.core.config import get_settings
    s = get_settings()
    ip = lan_ip()
    print("\n" + "=" * 64)
    print(" CommuniAI backend ishga tushdi")
    print(f"   Telefon ilovasida 'Server manzili':  http://{ip}:8000")
    print("   Android emulator uchun:              http://10.0.2.2:8000")
    print("   API hujjatlari (brauzerda):          http://localhost:8000/docs")
    print(f"   Ma'lumotlar bazasi: {'SQLite (lokal fayl)' if s.DATABASE_URL.startswith('sqlite') else 'PostgreSQL'}")
    if not s.ai_configured:
        print("   DIQQAT: AI_API_KEY sozlanmagan — AI funksiyalar 'sozlanmagan' deb javob beradi.")
        print("           backend/.env fayliga AI_API_KEY=... yozing va qayta ishga tushiring.")
    print("   To'xtatish: Ctrl+C")
    print("=" * 64 + "\n")

    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()
