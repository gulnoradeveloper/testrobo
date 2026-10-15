# Arxitektura

```
Brauzer (React SPA) ──/api/v1──▶ FastAPI ──▶ ModelService (kltool: preprocess → CNN → softmax → Grad-CAM)
                                   │                └─ model ishga tushishda bir marta yuklanadi
                                   ├─▶ SQLite (SQLAlchemy + Alembic): analyses, model_versions, artifacts
                                   └─▶ data/storage/<uuid>/ original.png · heatmap.png · overlay.png · report.pdf
```

Modullar mustaqil rivojlanadi: `ai/kltool` (PyTorch kodi) backend va o‘qitish skriptlari uchun umumiy;
frontend backend bilan faqat REST API orqali bog‘langan.

## Tahlil zanjiri (`POST /api/v1/analyses`)

1. Fayl hajmi chegarasigacha o‘qiladi (+1 bayt) → `FILE_TOO_LARGE`.
2. `validation.py`: bo‘sh fayl, kengaytma, e’lon qilingan MIME, haqiqiy imzo (JPEG/PNG magic bytes) o‘zaro mosligi,
   Pillow `verify()` + to‘liq dekodlash, piksel soni (≤ 50 MP, decompression bomb), minimal tomon 128 px,
   bir xil rangli bo‘sh tasvir. EXIF orientatsiyasi qo‘llanadi.
3. `projection_confirmed=true` majburiy — dastur proyeksiyani avtomatik aniqlamaydi, foydalanuvchi tasdiqlaydi.
4. Model yo‘q bo‘lsa → `503 MODEL_NOT_READY` (soxta natija yo‘q).
5. Preprocess: grayscale → kesmasdan kvadratga to‘ldirish → 224×224 → [0,1] → 3 kanal → ImageNet normallashtirish.
6. Forward (`eval()`, `inference_mode`) → softmax → argmax.
7. Grad-CAM: oxirgi konvolyutsion blok (`layer4[-1]` / `features[-1]`), bashorat qilingan sinf uchun; xarita
   letterbox geometriyasi bo‘yicha asl tasvir koordinatalariga qaytariladi. Xato yoki bo‘sh xarita natijada
   ochiq bildiriladi (`GRADCAM_FAILED` / `GRADCAM_EMPTY`).
8. Fayllar server yaratgan nomlar bilan PNG sifatida qayta kodlanib saqlanadi (metama’lumotlar olib tashlanadi).

## API

| Usul | Manzil | Vazifa |
|---|---|---|
| GET | `/api/v1/health` | Tizim, baza va model holati |
| GET | `/api/v1/model/info` | Model nomi, arxitektura, versiya, SHA-256, preprocess, dataset, metrikalar, cheklovlar |
| POST | `/api/v1/analyses` | `multipart/form-data`: `file`, `projection_confirmed` → tahlil natijasi (201) |
| GET | `/api/v1/analyses` | Joriy sessiya tarixi; `grade=0..4`, `sort=newest\|oldest\|grade_asc\|grade_desc` |
| GET | `/api/v1/analyses/{id}` | Tahlil natijasi |
| GET | `/api/v1/analyses/{id}/image` | Saqlangan (anonimlashtirilgan) asl tasvir |
| GET | `/api/v1/analyses/{id}/heatmap?variant=heatmap\|overlay` | Grad-CAM (RGBA xarita yoki ustma-ust tasvir) |
| GET | `/api/v1/analyses/{id}/report` | A4 PDF hisobot (birinchi so‘rovda yaratiladi) |
| DELETE | `/api/v1/analyses/{id}` | Tahlil, fayllar va yozuvlarni o‘chirish (204) |

Tahlil javobi: `id` (UUID), `number`, `status`, `model{name,version,architecture,checkpoint_sha256,training_status}`,
`prediction{kl_grade,label,title,description,reference}`, `probabilities[5]`, `timing{preprocess_ms,inference_ms,gradcam_ms,total_ms}`,
`image`, `heatmap{available,…}`, `report_url`, `disclaimer`, `probability_note`, `limitations`, `created_at`, `expires_at`.

Xatolik formati (barcha endpointlar): `{"error": {"code": "...", "message": "<o‘zbekcha>", "details": ...}}`

| Kod | HTTP | Xabar |
|---|---|---|
| NO_FILE | 400 | Fayl tanlanmagan. |
| UNSUPPORTED_FORMAT | 415 | Fayl formati qo‘llab-quvvatlanmaydi. |
| FILE_TOO_LARGE | 413 | Fayl hajmi belgilangan chegaradan oshgan. |
| IMAGE_UNREADABLE | 422 | Tasvirni o‘qib bo‘lmadi. |
| IMAGE_DIMENSIONS | 422 | Tasvir o‘lchamlari ruxsat etilgan chegaradan tashqarida. |
| PROJECTION_NOT_CONFIRMED | 422 | Tasvir bitta tizzaning frontal rentgen proyeksiyasi ekanini tasdiqlang. |
| MODEL_NOT_READY | 503 | Sun’iy intellekt modeli hali tayyor emas. |
| ANALYSIS_FAILED | 500 | Tahlilni bajarishda xatolik yuz berdi. |
| NOT_FOUND | 404 | Tahlil natijasi topilmadi. |
| FORBIDDEN | 403 | Ushbu ma’lumotni ko‘rishga ruxsat yo‘q. |
| RATE_LIMITED | 429 | So‘rovlar soni juda ko‘p. … |

“Server bilan bog‘lanib bo‘lmadi.” xabari frontendda tarmoq xatosida ko‘rsatiladi.

## Ma’lumotlar bazasi (Alembic: `backend/alembic/versions/0001_initial.py`)

- **analyses**: id, session_id, image_hash, predicted_class, probabilities_json, model_version, status,
  processing_time_ms, created_at, expires_at (+ timing_json, image_width, image_height, error_code, model_version_id)
- **model_versions**: id, model_name, version, architecture, checkpoint_hash, metrics_json, created_at
  (+ preprocess_version, class_names, training_status)
- **artifacts**: id, analysis_id, artifact_type (original/heatmap/overlay/report), file_path, expires_at (+ created_at)

Fayllar BLOB sifatida emas, `data/storage/` katalogida (0700) saqlanadi.

## Xavfsizlik va maxfiylik

- Sessiya: tasodifiy 256-bit token, `HttpOnly`, `SameSite=Lax`, HTTPS’da `Secure`; bazada faqat SHA-256 hashi.
- Begona sessiya tahliliga murojaat → 403; o‘chirish, rasm, xarita, hisobot ham himoyalangan.
- Ism, telefon, pasport, asl fayl nomi saqlanmaydi; foydalanuvchi fayl nomi hech qachon yo‘l sifatida ishlatilmaydi.
- Muddat (standart 24 soat) tugaganda yozuvlar va fayllar fon vazifasi orqali o‘chiriladi.
- Rate limiting: IP bo‘yicha (standart 240 so‘rov/daqiqa, 10 tahlil/daqiqa).
- Loglarda tasvir, fayl nomi, cookie yozilmaydi; kutilmagan xatolar foydalanuvchiga ichki tafsilotsiz qaytariladi.
- Checkpoint `weights_only=True` bilan yuklanadi, ixtiyoriy SHA-256 tekshiruvi.
- Xavfsizlik sarlavhalari: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, HTTPS’da HSTS.
- Rate limiter bitta jarayon xotirasida ishlaydi; bir nechta nusxa bilan joylashtirishda umumiy saqlash (Redis) kerak.
