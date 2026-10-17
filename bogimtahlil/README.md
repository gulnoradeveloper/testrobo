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

## Ishga tushirish (eng oson yo‘l)

- **Windows:** `BOGIMTAHLIL.bat` ni ikki marta bosing → brauzer o‘zi ochiladi (odatda http://127.0.0.1:8765).
- **Linux / macOS:** `./start.sh`

Faqat **Python 3.11/3.12** kerak (Node.js shart emas — interfeys `frontend/dist` da tayyor holda). Birinchi
ishga tushirishda yengil kutubxonalar o‘rnatiladi (`backend/requirements.txt`, PyTorch’siz). Batafsil:
[`ISHGA_TUSHIRISH.txt`](ISHGA_TUSHIRISH.txt).

PyTorch faqat o‘qitilgan model bilan tahlil uchun kerak: `pip install -r backend/requirements-ai.txt`.

## Ishlab chiquvchilar uchun

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements-dev.txt -r ai/requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
python start.py                                   # server + interfeys
cd frontend && npm install && npm run dev         # interfeys kodini o‘zgartirish (Node.js), so‘ng: npm run build
pytest                                            # testlar
```

## Hujjatlar

- [`docs/ORNATISH.md`](docs/ORNATISH.md) — o‘rnatish va ishga tushirish yo‘riqnomasi
- [`docs/MODEL_OQITISH.md`](docs/MODEL_OQITISH.md) — dataset, o‘qitish, baholash, eksport (qayta ishlab ko‘riladigan tajriba)
- [`docs/ARXITEKTURA.md`](docs/ARXITEKTURA.md) — arxitektura, API, ma’lumotlar bazasi, xavfsizlik
- [`docs/BOSQICHLAR_HISOBOTI.md`](docs/BOSQICHLAR_HISOBOTI.md) — bosqichlar bo‘yicha bajarilgan ishlar hisoboti
- [`experiments/benchmark.md`](experiments/benchmark.md) — inference tezligi o‘lchovi
