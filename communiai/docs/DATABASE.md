# Ma'lumotlar bazasi (PostgreSQL 16)

Sxema `backend/app/models/__init__.py` da, migratsiya `backend/alembic/versions/0001_initial_schema.py` da.
Barcha birlamchi kalitlar UUID. JSON maydonlar PostgreSQL'da `JSONB`. Enum qiymatlari `VARCHAR` + CHECK
(native enum emas — migratsiyalar oson bo'lishi uchun).

## Jadvallar

| Jadval | Vazifasi | Muhim maydonlar / cheklovlar |
|---|---|---|
| `users` | Foydalanuvchilar | `email` UNIQUE, `password_hash` (Argon2id), `role` (student/admin), `ai_consent_at`, `support_access_until`, `is_active` |
| `projects` | Loyihalar | `owner_id` FK→users (CASCADE, index), TZ dagi barcha maydonlar, `deleted_at` (soft delete, index) |
| `project_files` | Fayl metadata | `storage_key` UNIQUE (faylning o'zi DB da emas), `sha256`, `mime_type`, `file_size`, `extraction_status`, `extraction_error`, `extracted_text` |
| `project_analyses` | AI ekspertiza | `input_snapshot_hash` (index) — natija qaysi loyiha versiyasiga tegishli, `ai_model`, `prompt_version`, `result_json`, `status` |
| `defense_sessions` | Himoya sessiyalari | `mode`, `question_limit`, `status` (index), `rubric_version`, `project_snapshot_hash`, vaqt belgilari |
| `defense_questions` | Savollar | UNIQUE(`session_id`,`sequence_number`), `question_type` (main/follow_up), `project_reference`, `focus_area` |
| `defense_answers` | Javoblar | `question_id` UNIQUE (javob o'zgarmas), `user_id` |
| `answer_evaluations` | Har bir javob bahosi | `answer_id` UNIQUE, `rubric_version`, `ai_model`, `result_json` |
| `competency_results` | Sessiya natijasi | `session_id` UNIQUE, `rubric_version`, `total_score`, `max_applicable_score`, `coverage`, `level`, `criteria_json`, `readiness_json`, `summary_json` |
| `improvement_plans` | Adaptiv reja | `session_id` UNIQUE, `target_competencies`, `recommendations_json` (mashqlar + original javob id) |
| `practice_attempts` | Qayta mashqlar | `plan_id`, `exercise_index`, `target_competency`, `original_answer_id`, `revised_answer`, `evaluation_json` |
| `refresh_tokens` | Refresh tokenlar | `token_hash` UNIQUE (SHA-256, token o'zi saqlanmaydi), `family_id` (rotation va qayta ishlatishni aniqlash), `revoked_at` |
| `password_reset_tokens` | Parol tiklash | `token_hash` UNIQUE, `expires_at`, `used_at` |
| `audit_logs` | Audit | `actor_id`, `action`, `resource_type`, `resource_id`, `details`; index (`actor_id`,`created_at`) |
| `ai_jobs` | AI fon vazifalari | `kind`, `resource_id` (index), `status` (index), `error_code`, `error_message` |
| `ai_request_logs` | AI monitoring | operatsiya, model, kechikish, tokenlar, xato turi. **Prompt/javob matni saqlanmaydi** |
| `idempotency_records` | Idempotency | UNIQUE(`user_id`,`key`,`endpoint`), saqlangan javob |
| `system_settings` | Admin sozlamalari | `ai_enabled`, `ai_model`, `registration_open` (maxfiy kalitlar emas) |

## Ma'lumotlar izolyatsiyasi

Har bir so'rovda `owned_project` / `owned_session` / `_owned_plan` resurs egasini tekshiradi; begona resurs
uchun 404 qaytariladi (mavjudligini oshkor qilmaslik uchun). Foydalanuvchi o'chirilganda unga tegishli
barcha yozuvlar `ON DELETE CASCADE` orqali o'chadi, fayllar storage'dan o'chiriladi.

## Versiyalash

- `project_analyses.input_snapshot_hash` va `defense_sessions.project_snapshot_hash` — loyiha maydonlari va
  fayl SHA-256 lari asosidagi hash. Loyiha o'zgarsa eski ekspertiza "eskirgan" deb belgilanadi.
- `rubric_version` har bir baho, natija va rejada saqlanadi — rubrika o'zgarsa eski natijalar o'z versiyasi
  bilan qoladi.

## Migratsiyalar

```bash
alembic upgrade head      # qo'llash
alembic downgrade base    # orqaga qaytarish (CI da tekshiriladi)
alembic revision --autogenerate -m "..."   # model o'zgarganda
```
