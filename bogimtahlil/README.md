# Bo‘g‘imTahlil 1.0

**Sun’iy intellekt asosida tizza bo‘g‘imining rentgen tasvirlarini tahlil qilish axborot tizimi**
*“Aniq tahlil sari aqlli qadam!”*

Tizza bo‘g‘imi rentgen tasvirini qabul qilib, uni tekshiradi, dastlabki ishlov beradi, o‘qitilgan neyron tarmoq
(ResNet-18 / EfficientNet-B0) yordamida Kellgren–Lawrence (KL0–KL4) darajasini bashorat qiladi, Grad-CAM e’tibor
xaritasini yaratadi va natijani o‘zbek tilidagi PDF hisobot sifatida beradi.

> ⚠️ **Ilmiy-tadqiqot prototipi.** Natijalar shifokor tashxisi o‘rnini bosmaydi. Klinik tasdiqlash va ruxsatlarsiz
> mustaqil tashxis qo‘yish yoki davolashni belgilash uchun ishlatilmaydi.

## Loyiha holati — **Qisman tayyor / Model mavjud emas**

| Qism | Holat |
|---|---|
| Veb-interfeys (5 bo‘lim, o‘zbek tilida, mobilga moslashgan) | ✅ Tayyor, brauzerda sinovdan o‘tgan |
| Backend API (8 ta asosiy endpoint), validatsiya, sessiya, tarix, o‘chirish, rate limit | ✅ Tayyor, testlangan |
| Preprocess, inference, Grad-CAM, PDF hisobot | ✅ Tayyor, testlangan |
| O‘qitish / baholash / taqqoslash / eksport / benchmark skriptlari | ✅ Tayyor, sintetik ma’lumotda smoke-test qilingan |
| O‘qitish zanjiri: OAI manifest → 70/15/15 → ResNet-18 + EfficientNet-B0 → tanlash → test → eksport (`ai/scripts/run_experiment.py`) | ✅ Tayyor, OAI formatidagi sintetik ma’lumotda uchidan-uchiga sinovdan o‘tgan |
| **O‘qitilgan model (`artifacts/model.pt`)** | ❌ **Mavjud emas** — OAI datasetiga kirish ruxsati va ma’lumotlar kerak |
| **Model metrikalari (test)** | ❌ **Hali baholanmagan** |
| Docker obrazlari | ⚠️ Konfiguratsiya yozilgan, `docker compose config` tekshirilgan; ishlab chiqish muhitida Docker daemon yo‘qligi sababli obraz yig‘ilmagan |

Model yo‘qligida dastur **hech qanday tasodifiy yoki namunaviy natija ko‘rsatmaydi**: `POST /api/v1/analyses`
`503 MODEL_NOT_READY` qaytaradi, interfeys esa “Sun’iy intellekt modeli hozircha tahlil qilish uchun tayyor emas.”
xabarini chiqaradi. Modelni tayyorlash tartibi: [`docs/MODEL_OQITISH.md`](docs/MODEL_OQITISH.md).

## Tuzilma

```text
bogimtahlil/
├── frontend/      React + TypeScript + Vite + Tailwind + shadcn/ui + Recharts + Axios
├── backend/       FastAPI + SQLAlchemy + Alembic + SQLite; PDF (ReportLab)
├── ai/            kltool (umumiy AI moduli) + o‘qitish/baholash skriptlari + konfiguratsiyalar
├── data/          dataset va lokal baza (git’ga qo‘shilmaydi)
├── experiments/   tajriba natijalari (history, grafiklar, metrikalar, benchmark)
├── artifacts/     o‘qitilgan model (model.pt, sha256, model_card.json)
├── reports/       ilmiy hisobot materiallari
├── tests/         pytest: tests/ai, tests/backend   (frontend testlari: frontend/src/test)
├── docs/          hujjatlar
├── docker-compose.yml · .env.example · .gitignore · pytest.ini
```

## Tez ishga tushirish (lokal)

```bash
# 1) Backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements-dev.txt -r ai/requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
cd backend && uvicorn app.main:app --reload --port 8000      # baza Alembic orqali avtomatik yaratiladi

# 2) Frontend (yangi terminalda)
cd frontend && npm install && npm run dev                     # http://localhost:5173

# 3) Testlar
pytest                       # loyiha ildizida — 82 ta test (+4 tasi real dataset/model bo‘lganda)
cd frontend && npm test      # 9 ta test
```

Docker bilan: `cp .env.example .env && docker compose up -d --build` → http://localhost:8080.
Batafsil: [`docs/ORNATISH.md`](docs/ORNATISH.md).

## Hujjatlar

- [`docs/ORNATISH.md`](docs/ORNATISH.md) — o‘rnatish va ishga tushirish yo‘riqnomasi
- [`docs/MODEL_OQITISH.md`](docs/MODEL_OQITISH.md) — dataset, o‘qitish, baholash, eksport (qayta ishlab ko‘riladigan tajriba)
- [`docs/ARXITEKTURA.md`](docs/ARXITEKTURA.md) — arxitektura, API, ma’lumotlar bazasi, xavfsizlik
- [`docs/BOSQICHLAR_HISOBOTI.md`](docs/BOSQICHLAR_HISOBOTI.md) — bosqichlar bo‘yicha bajarilgan ishlar hisoboti
- [`experiments/benchmark.md`](experiments/benchmark.md) — inference tezligi o‘lchovi
