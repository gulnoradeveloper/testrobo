# Arxitektura

## Umumiy ko'rinish

```
 Flutter ilova (Android/iOS)                 FastAPI backend                         Tashqi xizmatlar
 ┌───────────────────────────┐   HTTPS     ┌──────────────────────────────────┐
 │ features/* (ekranlar)      │  JSON/JWT   │ api/v1/*  (router, validatsiya)   │
 │ core/providers (Riverpod)  │ ─────────▶ │ api/deps  (auth, rate limit,      │
 │ core/api (Dio, refresh)    │            │            idempotency, audit)     │
 │ core/storage (SecureStore) │            │ services/                          │──▶ PostgreSQL
 └───────────────────────────┘            │   projects (extraction, context)   │──▶ Lokal disk / S3
                                          │   ai (provider, prompts, schemas)  │──▶ AI provayder (Claude)
                                          │   defense (workflow, state machine)│──▶ SMTP (parol tiklash)
                                          │   evaluation (rubrika, hisoblash)  │
                                          │   jobs (AI vazifalari, thread pool)│
                                          │ models (SQLAlchemy), alembic        │
                                          └──────────────────────────────────┘
```

### Backend qatlamlari

| Qatlam | Mas'uliyat |
|---|---|
| `app/api/v1` | HTTP endpointlar, Pydantic validatsiya, ownership tekshiruvi, holat o'tishlari |
| `app/api/deps.py` | JWT autentifikatsiya, admin/consent talablari, pagination, rate limit, idempotency, audit |
| `app/services/ai` | `AIProvider` interfeysi, Anthropic adapteri, vazifaviy promptlar, natija sxemalari, 4 ta AI servis |
| `app/services/projects` | Fayl validatsiyasi va matn ajratish, AI kontekstini yig'ish, snapshot hash |
| `app/services/defense` | Himoya workflow: savol yaratish, javobni baholash, yakuniy baholash, qayta mashq |
| `app/services/evaluation` | Versiyalangan rubrika va ballarni **backend tomonida** hisoblash |
| `app/services/jobs.py` | Uzoq AI amallarini `ai_jobs` jadvalida kuzatiladigan fon vazifalari sifatida bajarish |
| `app/services/storage` | Fayllarni xususiy saqlash (local / S3) |
| `app/models` | Normalizatsiyalangan PostgreSQL sxemasi |

### Mobil ilova tuzilmasi

```
lib/
  core/        api (Dio klient, xato formati, repository), providers, router, theme, storage, config
  features/    auth, dashboard, projects, project_analysis, defense, communication_coach,
               practice, analytics, profile
  shared/      umumiy widgetlar (Loading/Empty/Error/Retry, BusyButton, ScoreBar, logo)
```

Barcha ekranlar real API ma'lumotlari bilan ishlaydi. AI amallari kutilayotganda ilova vazifa holatini
ko'rsatadi va 2–3 soniyada so'rov yuborib (polling) yangilaydi.

## Asosiy oqimlar

### Loyiha ekspertizasi
1. `POST /projects/{id}/analyze` → `project_analyses` (pending) + `ai_jobs` yoziladi, 202 qaytadi.
2. Fon vazifasi loyiha maydonlari + ajratilgan matnni `<untrusted_data>` ichida AI ga yuboradi.
3. Natija `ProjectAnalysisOut` sxemasi bilan validatsiya qilinadi; dalili loyiha matnida topilmagan
   "kuchli jihatlar" olib tashlanadi.
4. Bir xil loyiha versiyasi (snapshot hash) uchun takroriy so'rov yangi AI chaqiruvi yaratmaydi.

### Virtual himoya (holatlar mashinasi)

```
CREATED ──start──▶ IN_PROGRESS ──complete──▶ COMPLETED ──▶ EVALUATING ──▶ EVALUATED
   │                    │                                       │
   └──cancel──▶ CANCELLED ◀──cancel                              └──xato──▶ FAILED ──complete──▶ EVALUATING
```

- Har bir javobdan so'ng `defense_answer` vazifasi: javobni baholash (Communication Evaluation) → keyingi
  savolni oldingi javoblar va "needs_follow_up" belgisi asosida yaratish (Expert Question).
- Javob `defense_answers.question_id` UNIQUE — yuborilgan javobni o'zgartirib bo'lmaydi.
- AI ishlamay qolsa javob saqlanadi, sessiya `IN_PROGRESS` holatida qoladi, `pending_work` ko'rsatiladi;
  `POST /resume` yetishmayotgan ishni qayta navbatga qo'yadi.
- Yakuniy baholash: backend rubrika bo'yicha ballarni hisoblaydi → Improvement Coach eng zaif 2 ta
  kompetensiya uchun mashq yaratadi → `competency_results` va `improvement_plans` yoziladi.

### Adaptiv mashq
1. Baholangan K1–K5 ichidan foizi eng past 2 tasi tanlanadi (deterministik).
2. Har biri uchun aniq savolga qayta javob topshirig'i yaratiladi.
3. Qayta javob o'sha rubrika versiyasi bilan baholanadi + K6 (refleksiya) baholanadi.
4. Oldin/keyin farqi `practice_attempts.evaluation_json.score_comparison` da saqlanadi.

## Kelajakdagi kengayish

- **Ovozli muloqot:** `AnswerIn` ga audio kirish qo'shiladi; speech-to-text servis `services/ai` ga yangi
  provayder sifatida ulanadi; rubrikaning yangi versiyasi (masalan 2.0) nutq ravonligini qo'shadi —
  eski natijalar o'z `rubric_version`i bilan saqlanib qoladi.
- **Jamoaviy loyihalar:** `project_members` jadvali va `owned_project` tekshiruvini a'zolikka kengaytirish.
- **O'qituvchi kabineti:** yangi `teacher` roli, guruhlar va talaba roziligiga asoslangan kirish.
- **Ko'p instansiya:** rate limiter va job runner'ni Redis/queue (masalan, RQ yoki Celery) ga almashtirish
  (interfeyslar shunga tayyor).
