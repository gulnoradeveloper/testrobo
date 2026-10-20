# REST API

To'liq interaktiv hujjat server ishga tushganda: **`/docs`** (Swagger UI), **`/redoc`**, **`/openapi.json`**.

## Umumiy qoidalar

- Bazaviy yo'l: `/api/v1`. Autentifikatsiya: `Authorization: Bearer <access_token>` (15 daqiqa).
- Refresh token (30 kun) har ishlatilganda almashtiriladi (rotation). Eski token qayta ishlatilsa butun
  token oilasi bekor qilinadi.
- **Yagona xato formati:**
  ```json
  {"error": {"code": "VALIDATION_ERROR", "message": "Kiritilgan ma'lumotlar noto'g'ri",
             "details": [{"field": "password", "message": "..."}], "request_id": "..."}}
  ```
- **Pagination:** `?page=1&page_size=20` (max 100) → `{"items", "total", "page", "page_size"}`.
- **Idempotency:** `POST /defenses`, `/projects/{id}/analyze`, `/defenses/{id}/answers`,
  `/practice-plans/{id}/attempts` uchun `Idempotency-Key` sarlavhasi — takroriy so'rov avvalgi javobni qaytaradi.
  Bundan tashqari bir xil fayl, bir xil loyiha versiyasi uchun ekspertiza va bir xil javob tabiiy ravishda
  dublikat yaratmaydi.
- **Rate limit:** umumiy (IP), auth (IP+yo'l), AI (foydalanuvchi) — `429 RATE_LIMITED` + `retry_after_seconds`.
- **AI amallari asinxron:** `202 Accepted` + `job` obyekti; holat `GET /jobs/{id}` yoki resurs orqali kuzatiladi.
- AI amallari foydalanuvchining roziligini talab qiladi (`403 AI_CONSENT_REQUIRED`).

## Endpointlar

### Authentication
| Metod | Yo'l | Izoh |
|---|---|---|
| POST | `/auth/register` | Ro'yxatdan o'tish (parol ≥10 belgi, zaif parollar bloklanadi) → tokenlar |
| POST | `/auth/login` | Kirish |
| POST | `/auth/refresh` | Token yangilash (rotation) |
| POST | `/auth/logout` | Refresh tokenni bekor qilish |
| GET | `/auth/me` | Joriy foydalanuvchi |
| POST | `/auth/password-reset/request` | Emailga kod yuborish (SMTP sozlanmagan bo'lsa `503 EMAIL_NOT_CONFIGURED`) |
| POST | `/auth/password-reset/confirm` | Kod bilan yangi parol o'rnatish |

### Projects / Files / Analysis
| Metod | Yo'l | Izoh |
|---|---|---|
| GET/POST | `/projects` | Ro'yxat (`q` qidiruv) / yaratish |
| GET/PATCH/DELETE | `/projects/{id}` | Tafsilotlar (fayllar, oxirgi ekspertiza, himoyalar tarixi) / tahrirlash / o'chirish |
| POST | `/projects/{id}/files` | `multipart/form-data` `file`: PDF, DOCX, PPTX, TXT ≤ 20 MB |
| GET | `/projects/{id}/files` | Fayllar |
| DELETE | `/projects/{id}/files/{file_id}` | Fayl va saqlangan nusxani o'chirish |
| POST | `/projects/{id}/analyze` | AI ekspertiza (202). `?force=true` — shu versiya uchun qayta |
| GET | `/projects/{id}/analyses` | Ekspertizalar tarixi |
| GET | `/analyses/{analysis_id}` | Ekspertiza natijasi / holati |

### Defense
| Metod | Yo'l | Izoh |
|---|---|---|
| POST | `/defenses` | `{project_id, mode: hackathon|client|academic|investor, question_limit: 5|10|15}` |
| GET | `/defenses` | Ro'yxat (`status`, `project_id` filtrlari) |
| GET | `/defenses/{id}` | Sessiya, savollar, javoblar, baholar, `active_job`, `pending_work` |
| POST | `/defenses/{id}/start` | CREATED→IN_PROGRESS, birinchi savol (idempotent) |
| POST | `/defenses/{id}/resume` | AI xatosidan keyin yetishmayotgan ishni qayta navbatga qo'yish |
| GET | `/defenses/{id}/current-question` | Joriy savol, progress, oxirgi feedback |
| POST | `/defenses/{id}/answers` | `{question_id, answer_text}` (202) — javob o'zgarmas |
| POST | `/defenses/{id}/complete` | Yakuniy baholash (FAILED dan qayta urinish ham shu) |
| POST | `/defenses/{id}/cancel` | Bekor qilish |
| GET | `/defenses/{id}/results` | Kompetentlik natijasi, tayyorgarlik, xulosa, `plan_id` |

### Communication Training
| Metod | Yo'l | Izoh |
|---|---|---|
| POST | `/practice-plans` | `{session_id}` → sessiya uchun adaptiv reja |
| GET | `/practice-plans` | Rejalar |
| GET | `/practice-plans/{id}` | Mashqlar va urinishlar |
| POST | `/practice-plans/{id}/attempts` | `{exercise_index, revised_answer}` (202) |
| POST | `/practice-attempts/{id}/retry` | Muvaffaqiyatsiz baholashni qayta urinish |
| GET | `/practice-plans/{id}/progress` | Oldin/keyin solishtiruv, K6 |

### Analytics / Profile
| Metod | Yo'l | Izoh |
|---|---|---|
| GET | `/me/competencies` | Oxirgi natija + kompetensiyalar dinamikasi |
| GET | `/me/progress` | Sessiyalar bo'yicha foizlar, mashq deltalari |
| GET | `/me/history` | Faoliyatlar tarixi |
| GET | `/me/dashboard` | Bosh sahifa ma'lumotlari |
| GET/PATCH | `/me` | Profil, `ai_consent`, `support_access_days` |
| POST | `/me/password` | Parolni o'zgartirish |
| GET | `/me/export` | Barcha shaxsiy ma'lumotlarni JSON eksport |
| DELETE | `/me` | Hisob va barcha ma'lumotlarni o'chirish |

### Jobs / Admin / System
| Metod | Yo'l | Izoh |
|---|---|---|
| GET | `/jobs/{id}` | AI vazifa holati (faqat egasi) |
| GET | `/admin/users`, PATCH `/admin/users/{id}?is_active=` | Foydalanuvchilar (loyiha matnisiz) |
| GET | `/admin/system` | DB, AI, email holati, 24 soatlik statistika |
| GET | `/admin/ai-requests`, `/admin/errors`, `/admin/audit-logs` | Monitoring |
| GET/PUT | `/admin/settings` | `ai_enabled`, `ai_model`, `registration_open` |
| POST | `/admin/projects/{id}/access` | Talaba ruxsati + sabab bilan, audit qilinadigan kirish |
| GET | `/health/live`, `/health/ready`, `/api/v1/meta` | Tizim holati, ochiq imkoniyatlar |
