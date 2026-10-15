# O‘rnatish yo‘riqnomasi

## Talablar

- Python 3.11+ (3.13 da ham sinovdan o‘tgan)
- Node.js 20+ — faqat interfeys kodini o‘zgartirish uchun; tayyor interfeys `frontend/dist` da keladi va backend uni
  `http://127.0.0.1:8000` manzilida o‘zi beradi
- 4 GB RAM, ~3 GB disk (PyTorch CPU)
- GPU ixtiyoriy: mavjud bo‘lsa (`BT_DEVICE=auto`) avtomatik ishlatiladi
- Tashqi pullik AI API talab qilinmaydi

## 1. Backend

```bash
cd bogimtahlil
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements-dev.txt -r ai/requirements.txt \
    --extra-index-url https://download.pytorch.org/whl/cpu
cp .env.example backend/.env           # ixtiyoriy; standart qiymatlar lokal ishlash uchun yetarli
cd backend
uvicorn app.main:app --port 8000
```

Ishga tushishda:
1. `alembic upgrade head` avtomatik bajariladi (`data/bogimtahlil.db` yaratiladi). Qo‘lda: `cd backend && alembic upgrade head`.
2. Model `artifacts/model.pt` dan **bir marta** yuklanadi. Fayl yo‘q / buzilgan / mos emas / o‘qitilmagan bo‘lsa —
   server ishlayveradi, lekin tahlil `503 MODEL_NOT_READY` bilan rad etiladi (`GET /api/v1/model/info` da sababi ko‘rinadi).
3. Muddati o‘tgan tahlillar har 15 daqiqada o‘chiriladi.

API hujjati (Swagger): http://localhost:8000/api/docs

## 2. Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173  (/api so‘rovlari 127.0.0.1:8000 ga proksi qilinadi)
npm run build      # ishlab chiqarish uchun: dist/
```

## 3. Docker Compose

```bash
cp .env.example .env
# o‘qitilgan modelni artifacts/model.pt ga joylashtiring (bo‘lmasa tahlil cheklangan holatda qoladi)
docker compose up -d --build
```

Interfeys: http://localhost:8080. Ma’lumotlar `appdata` volume’ida saqlanadi; `artifacts/` faqat o‘qish uchun ulanadi.

## 4. Modelni ulash

```bash
cp /yo‘l/model.pt artifacts/model.pt
cp /yo‘l/model.pt.sha256 artifacts/model.pt.sha256
# ixtiyoriy: hashni majburiy tekshirish
echo "BT_MODEL_SHA256=$(cut -d' ' -f1 artifacts/model.pt.sha256)" >> backend/.env
# serverni qayta ishga tushiring
```

Backend checkpointni faqat quyidagi shartlarda qabul qiladi: format versiyasi to‘g‘ri, arxitektura `resnet18` yoki
`efficientnet_b0`, sinflar tartibi aynan `KL0..KL4`, preprocess versiyasi dasturniki bilan bir xil, vaznlar
arxitekturaga to‘liq mos, `training_status = "trained"`. Yuklash `torch.load(weights_only=True)` bilan bajariladi.

## 5. Internetga joylashtirish (HTTPS)

Ochiq serverda HTTPS majburiy. Tavsiya: Caddy/nginx teskari proksisi + Let’s Encrypt sertifikati, frontend
konteyneri oldida. So‘ng `.env` da:

```
BT_SESSION_COOKIE_SECURE=true
BT_FORCE_HTTPS=true
BT_TRUST_PROXY_HEADERS=true
```

`BT_FORCE_HTTPS` HTTP so‘rovlarni HTTPS ga yo‘naltiradi va HSTS sarlavhasini qo‘shadi.

## 6. Testlar

```bash
pytest                         # loyiha ildizida: AI moduli + backend (82 ta; 4 tasi real dataset/model paydo bo‘lganda ishlaydi)
cd frontend && npm test        # Vitest (9 ta)
```

Testlar tasodifiy vaznli, `untrained-test-fixture` deb belgilangan checkpoint yaratadi va uni faqat
`allow_untrained_model=True` sozlamasi bilan yuklaydi. Bu checkpoint faqat dastur zanjirini tekshirish uchun.

## 7. Demo / texnik sinov rejimi (o‘qitilgan model yo‘q bo‘lganda)

Interfeysni texnik namoyish qilish uchun test checkpointi bilan ishga tushirish mumkin:

```bash
python ai/scripts/make_test_checkpoint.py --out /tmp/fixture.pt
cd backend && BT_ALLOW_UNTRAINED_MODEL=true BT_MODEL_PATH=/tmp/fixture.pt uvicorn app.main:app
```

Bu rejimda interfeysning barcha sahifalarida qizil “O‘qitilmagan test modeli” ogohlantirishi, PDF hisobotda esa
“natija ma’noga ega emas” yozuvi chiqadi. **Himoyada bu rejimni real sun’iy intellekt natijasi sifatida ko‘rsatmang.**
