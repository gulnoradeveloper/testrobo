# CommuniAI — Professional MVP 1.0

**Sun'iy intellekt asosida IT loyihalarini himoya qilish va kasbiy kommunikativ kompetentlikni rivojlantirish mobil platformasi.**

> Loyihangni ishonch bilan himoya qil!

Talaba loyihasini yuklaydi → AI loyihani o'rganadi → mos ekspert savollarini beradi → talaba javob beradi →
AI javobni rubrika asosida tahlil qiladi → kamchiliklarni tushuntiradi → individual mashq beradi →
talaba qayta javob beradi → natijalar solishtiriladi va saqlanadi.

| Qism | Texnologiya | Papka |
|---|---|---|
| Mobil ilova | Flutter 3.47, Dart 3.13, Material 3, Riverpod, GoRouter, Dio, Flutter Secure Storage, File Picker, flutter_markdown_plus, fl_chart | `mobile/` |
| Backend | Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PostgreSQL 16, JWT, Argon2id | `backend/` |
| AI qatlami | Provayderdan mustaqil `AIProvider` interfeysi; Anthropic Claude (`claude-opus-5-5`) adapteri, structured outputs | `backend/app/services/ai/` |
| Fayllar | Lokal (dev) yoki S3-compatible (prod) storage adapteri | `backend/app/services/storage/` |
| Hujjatlar | Arxitektura, DB, API, promptlar, rubrika, xavfsizlik, testlash, APK | `docs/` |

## Tezkor ishga tushirish

### 1. Backend (Docker bilan)

```bash
cd communiai
cp .env.example .env          # JWT_SECRET va AI_API_KEY ni kiriting
docker compose up -d --build  # http://localhost:8000  (OpenAPI: /docs)
docker compose exec backend python -m app.cli create-admin --email admin@example.uz
```

HTTPS (domen bilan, Caddy avtomatik sertifikat oladi): `.env` da `DOMAIN=api.sizning-domen.uz`, keyin
`docker compose --profile https up -d --build`.

### 2. Backend (Dockersiz, lokal)

```bash
cd communiai/backend
python3.13 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
cp ../.env.example .env       # DATABASE_URL, JWT_SECRET, AI_API_KEY
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Mobil ilova

```bash
cd communiai/mobile
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000   # Android emulator
```

Server manzilini ilovaning o'zida ham o'zgartirish mumkin: **Kirish ekrani → "Server manzili"** yoki
**Profil → Sozlamalar → Server**.

APK yig'ish va o'rnatish: [`docs/BUILD_APK.md`](docs/BUILD_APK.md). GitHub Actions har push'da
`CommuniAI-1.0.0-release.apk` (faqat HTTPS) va `CommuniAI-1.0.0-dev-http.apk` (lokal tarmoqdagi HTTP server
uchun) fayllarini yig'adi va `communiai-apk` branch'iga joylaydi.

## AI provayder

`AI_PROVIDER=anthropic` va `AI_API_KEY` sozlanganda barcha AI funksiyalar ishlaydi. Kalit bo'lmasa ilova
ishlashda davom etadi, ammo AI amallari **"AI xizmati serverda sozlanmagan"** deb ochiq aytadi — soxta yoki
demo natija hech qachon ko'rsatilmaydi. Administrator AI operatsiyalarini vaqtincha o'chirib qo'yishi va
modelni almashtirishi mumkin (Admin panel).

## Testlar

```bash
cd backend && pytest            # 66 ta test: auth, loyihalar, fayllar, AI, himoya, rubrika, e2e demo ssenariy
cd mobile && flutter analyze && flutter test
```

Batafsil: [`docs/TESTING.md`](docs/TESTING.md).

## Hujjatlar

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — modullar, oqimlar, holatlar mashinasi
- [DATABASE.md](docs/DATABASE.md) — jadvallar, bog'lanishlar, indekslar
- [API.md](docs/API.md) — REST endpointlar, xato formati, idempotency
- [AI_PROMPTS.md](docs/AI_PROMPTS.md) — vazifaviy promptlar va prompt xavfsizligi
- [EVALUATION_RUBRIC.md](docs/EVALUATION_RUBRIC.md) — K1–K6 rubrika, hisoblash, darajalar
- [SECURITY.md](docs/SECURITY.md) — xavfsizlik va maxfiylik choralari
- [TESTING.md](docs/TESTING.md) — test strategiyasi
- [BUILD_APK.md](docs/BUILD_APK.md) — Android APK yig'ish, imzolash
- [IMPLEMENTATION_REPORT.md](docs/IMPLEMENTATION_REPORT.md) — bajarilgan va bajarilmagan talablar hisoboti

> **Muhim ilmiy eslatma:** ilova ko'rsatadigan ballar va kompetentlik darajalari AI asosidagi dastlabki
> diagnostika bo'lib, validatsiyadan o'tgan pedagogik o'lchov hisoblanmaydi. Tajriba-sinovdan oldin ekspert
> bahosi va pilot sinov o'tkazilishi kerak.
