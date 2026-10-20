# Testlash

## Backend (pytest, PostgreSQL)

```bash
cd backend
createdb communiai_test   # yoki TEST_DATABASE_URL ni ko'rsating
pytest
```

Testlar haqiqiy FastAPI ilovasi, PostgreSQL, fayl saqlash, matn ajratish, prompt yig'ish, validatsiya,
ballarni hisoblash va fon vazifalari bilan ishlaydi. Faqat AI provayder testlar uchun maxsus
`ScriptedProvider` (`tests/conftest.py`) bilan almashtiriladi — u faqat testlarda mavjud, production kodida
soxta provayder yo'q.

| Fayl | Qamrov (TZ 21) |
|---|---|
| `test_auth.py` | ro'yxatdan o'tish, takroriy email, zaif parol, login, noto'g'ri parol, refresh rotation va qayta ishlatishni aniqlash, logout, yaroqsiz token, begona resursga kirishni rad etish, parol tiklash (SMTP sozlanmagan/sozlangan) |
| `test_projects.py` | CRUD, majburiy maydonlar, PDF/DOCX/PPTX/TXT yuklash va matn ajratish, dublikat yuklash, noto'g'ri format, soxta signatura, MIME nomuvofiqligi, katta fayl, ZIP bomb, matnsiz PDF, fayl o'chirish, fayl nomi tozalash |
| `test_ai.py` | rozilik talabi, AI sozlanmaganda soxta natija yo'qligi, kontekstga mos tahlil, takroriy tahlil qayta ishlatilishi, dalilsiz kuchli jihatni olib tashlash, noto'g'ri JSON → retry, retry tugashi, sxema buzilishi, timeout/provider xatosi, prompt injection (teg qochishi, ballni oshirish), dalilsiz ball, admin AI ni o'chirishi |
| `test_defense.py` | to'liq himoya oqimi, dinamik savollar, javob o'zgarmasligi va tartibi, idempotent sessiya yaratish, AI uzilishidan keyin davom ettirish, yakuniy baholash xatosidan qayta urinish, sessiyalar izolyatsiyasi, bekor qilish va noto'g'ri o'tishlar, qayta mashq oldin/keyin, dashboard/tarix/eksport/o'chirish |
| `test_rubric.py` | max 100, darajalar chegaralari, baholanmagan ≠ 0, o'rtacha va cheklash, K6 ni javob orqali kiritib bo'lmasligi, deterministik qiyoslash, tayyorgarlik alohidaligi |
| `test_anthropic_provider.py` | Anthropic adapteri: so'rov shakli, refusal / max_tokens / bo'sh natija, timeout, auth, rate limit, server xatolari |
| `test_system.py` | health, OpenAPI, xato formati va request id, pagination, rate limit, admin roli va audit, meta maxfiylikni oshkor qilmasligi |
| `test_e2e_demo.py` | TZ 24 demo ssenariysi boshidan oxirigacha (PPTX bilan, chiqib-qayta kirishgacha) |

Natija: **66 passed**.

## Mobil (flutter test)

```bash
cd mobile && flutter analyze && flutter test
```

`test/app_test.dart`: API xato formatini o'qish, tarmoq xatosi, foydalanuvchi modeli, "Hali baholanmagan"
ko'rsatilishi (0 emas), login va ro'yxatdan o'tish formalari validatsiyasi, formatlash.

## CI

`.github/workflows/communiai.yml`: backend testlari (PostgreSQL service, migratsiya up/down), Flutter
analyze + test, release va dev APK yig'ish.

## Haqiqiy AI bilan qo'lda tekshirish

`AI_API_KEY` sozlangan serverda demo ssenariyni (TZ 24) ilovada bajaring. Admin panel → "AI so'rovlari"
bo'limida har bir chaqiruvning kechikishi va holati ko'rinadi.

## Unumdorlik

Oddiy API (AI siz) so'rovlari lokal muhitda 3–30 ms oralig'ida (uvicorn loglari). AI amallari fon
vazifasida bajariladi va ularning vaqti provayderga bog'liq.
