# Amalga oshirish hisoboti (TZ 26.12)

Holat belgilari: ✅ bajarildi va tekshirildi · 🟡 bajarildi, lekin cheklov yoki to'liq tekshirilmagan · ❌ bajarilmadi

## Definition of Done (TZ 25)

| Mezon | Holat | Izoh |
|---|---|---|
| Flutter Android ilovasi ishga tushadi | 🟡 | APK GitHub Actions'da yig'iladi; flutter analyze/test o'tadi. Real qurilma yoki emulatorda qo'lda sinov ishlab chiqish muhitida o'tkazilmadi (emulator yo'q). |
| Backend ishga tushadi | ✅ | uvicorn bilan ishga tushirilib HTTP orqali tekshirildi |
| PostgreSQL ulanadi | ✅ | PostgreSQL 16, Alembic migratsiya up/down |
| Ro'yxatdan o'tish, kirish | ✅ | testlar + jonli smoke test |
| Loyiha yaratish va tahrirlash | ✅ | |
| PDF, DOCX, PPTX, TXT yuklash | ✅ | |
| Fayllardan matn ajratish | ✅ | OCR yo'q (TZ bo'yicha majburiy emas) — foydalanuvchiga aytiladi |
| AI haqiqiy loyiha ma'lumotlarini tahlil qiladi | 🟡 | Anthropic adapteri amalga oshirilgan va unit testlangan. Ishlab chiqish muhitida API kaliti bo'lmagani uchun **haqiqiy model bilan oxirigacha sinov o'tkazilmadi**; butun zanjir test provayderi bilan tekshirildi. Kalit qo'yilgach demo ssenariyni qo'lda tekshirish kerak. |
| AI ekspert savollarini beradi | 🟡 | yuqoridagi kabi |
| Talaba matnli javob yuboradi | ✅ | |
| AI javobni rubrika asosida tahlil qiladi | 🟡 | yuqoridagi kabi; backend hisoblash to'liq testlangan |
| Kompetensiyalar bo'yicha natijalar | ✅ | |
| Individual tavsiyalar | ✅ | |
| Qayta mashq | ✅ | |
| Natijalar DB da saqlanadi | ✅ | |
| Tarix | ✅ | |
| Boshqa foydalanuvchi ma'lumotlariga kirish bloklanadi | ✅ | testlangan |
| AI xatoliklari to'g'ri boshqariladi | ✅ | timeout, provider xatosi, noto'g'ri JSON, refusal, sozlanmagan, admin o'chirgan |
| Avtomatik testlar o'tadi | ✅ | backend 66, Flutter 7 |
| Professional mobil dizayn | ✅ | Material 3, light/dark, CommuniAI palitrasi va logotipi |
| APK build jarayoni hujjatlashtirilgan | ✅ | `BUILD_APK.md` |
| README va texnik hujjatlar | ✅ | |

## Funksional talablar

| Bo'lim | Holat | Izoh |
|---|---|---|
| 4.1 Talaba roli | ✅ | |
| 4.2 Administrator | ✅ | foydalanuvchilar, tizim holati, AI monitoring, xatoliklar, sozlamalar (AI yoqish/o'chirish, model, ro'yxatdan o'tish); loyiha matniga faqat talaba ruxsati + audit bilan |
| 5 Splash, Onboarding, Register, Login, Dashboard, pastki navigatsiya | ✅ | |
| 5.4 Parolni tiklash | 🟡 | SMTP orqali haqiqiy email; SMTP sozlanmaganda ilova buni ochiq aytadi. Haqiqiy SMTP server bilan sinalmagan. |
| 6 Project Hub (CRUD, fayllar, xavfsiz yuklash, loyiha sahifasi) | ✅ | |
| 7 AI Project Expert (A–F, dalilsiz xulosa yo'q) | ✅/🟡 | real model bilan sinalmagan |
| 8 Virtual himoya (4 rejim, 5/10/15, dinamik savollar, holatlar, davom ettirish) | ✅/🟡 | |
| 9 Communication Coach (6 qismli feedback, namuna alohida) | ✅ | |
| 10 Baholash modeli (A/B alohida, K6 baholanmagan ≠ 0, versiyalash) | ✅ | |
| 11 Loyihani rivojlantirish tavsiyalari | ✅ | ekspertiza va himoya asosida |
| 12 Adaptiv mexanizm | ✅ | |
| 13 Vazifaviy promptlar, prompt xavfsizligi | ✅ | |
| 14 JSON natijalar, ballar backendda | ✅ | |
| 15 Ma'lumotlar bazasi | ✅ | TZ jadvallari + qo'shimcha: `password_reset_tokens`, `ai_jobs`, `ai_request_logs`, `idempotency_records`, `system_settings` |
| 16 REST API (barcha endpointlar, async job, idempotency) | ✅ | qo'shimcha: `/resume`, `/cancel`, `/jobs/{id}`, `/me/*`, `/admin/*` |
| 17–18 UI/UX, 22 ekran | ✅ | barcha ekranlarda loading/empty/error/retry |
| 19 Xavfsizlik | ✅ | `SECURITY.md` |
| 20 Non-functional | 🟡 | p95 < 500 ms yuk testi o'tkazilmadi (alohida so'rovlar 3–30 ms) |
| 21 Testlar (unit, integration, e2e) | 🟡 | backend unit/integration/e2e ✅; mobil unit/widget ✅; qurilmadagi Flutter integration (UI e2e) testlari yo'q |
| 22 Papkalar tuzilmasi | ✅ | |
| 3.4 S3 storage | 🟡 | adapter yozilgan, real bucket bilan sinalmagan |
| Docker | 🟡 | `docker-compose.yml`, `Dockerfile` yozilgan; ishlab chiqish muhitida Docker registry yopiqligi sababli ishga tushirib ko'rilmadi |
| iOS | 🟡 | kod tayyor, yig'ilmagan |

## Muhim eslatmalar

- **Logotip** — taqdim etilgan rasm asosida vektor (SVG) qayta chizilgan (`mobile/assets/branding/logo.svg`).
  Asl PNG faylni `mobile/assets/images/logo.png` ga almashtirish bilan butun ilovada yangilanadi
  (ikonkalar uchun `mipmap-*` fayllarni ham yangilang).
- **Rate limiter va job runner** bitta server instansiyasi uchun mo'ljallangan (in-memory / thread pool).
  Gorizontal masshtablashda Redis va navbat servisi kerak.
- **APK imzosi** — CI APK'lari debug kaliti bilan imzolangan; Play Market uchun o'z keystore bilan yig'ing.
- **`flutter_markdown`** to'xtatilgan (discontinued) — uning rasmiy davomchisi `flutter_markdown_plus`
  ishlatildi.
- Pedagogik ballar validatsiyadan o'tmagan dastlabki diagnostika sifatida ko'rsatiladi (ilovada ham).
