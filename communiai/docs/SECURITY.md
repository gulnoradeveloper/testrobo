# Xavfsizlik va maxfiylik

| Talab (TZ 19) | Amalga oshirilishi |
|---|---|
| HTTPS | Release APK faqat HTTPS ga ulanadi (`network_security_config.xml`: cleartext faqat emulator/localhost). Prod: `docker compose --profile https` (Caddy, avtomatik TLS). Dev APK (`-PallowCleartext=true`) faqat lokal sinov uchun. |
| Maxfiy kalitlar backendda | `AI_API_KEY`, `JWT_SECRET`, SMTP, S3 — faqat `.env`/muhit. Ilovada hech qanday kalit yo'q. `/api/v1/meta` faqat ochiq bayroqlarni beradi. |
| JWT + refresh rotation | Access 15 daq (HS256). Refresh — tasodifiy 64 belgili token, DB da faqat SHA-256 xeshi; har ishlatishda almashtiriladi; qayta ishlatish aniqlansa butun oila bekor qilinadi; logout bekor qiladi; parol tiklanganda barcha tokenlar bekor. |
| Argon2id | `argon2-cffi` PasswordHasher (Argon2id). Parol ≥10 belgi, keng tarqalgan/oddiy parollar, email nomi bilan o'xshashlik bloklanadi. |
| Ownership | Har bir resurs egasi tekshiriladi, begona resurs uchun 404. Testlar bilan tasdiqlangan. |
| Upload validation | Kengaytma oq ro'yxati, e'lon qilingan MIME mosligi, magic bytes (PDF `%PDF-`, Office `PK` + `[Content_Types].xml` + `word/`/`ppt/`), TXT da binar ma'lumot yo'qligi, hajm limiti, fayl nomini tozalash, ZIP bomb himoyasi (elementlar soni, ochilgan hajm, siqilish nisbati), ajratilgan matn hajmi limiti, shifrlangan PDF rad etiladi. Fayllar hech qachon bajarilmaydi. |
| Prompt injection | `AI_PROMPTS.md` → "Prompt xavfsizligi". |
| SQL injection | Faqat SQLAlchemy ORM / parametrlangan so'rovlar. |
| XSS | Mobil ilova AI matnini oddiy `Text` sifatida chiqaradi; markdown bloklarida havola/rasm faol emas. API `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Cache-Control: no-store`. |
| Rate limiting | Global (IP), auth (IP+yo'l, brute-force), AI (foydalanuvchi). Bitta instansiya uchun in-memory; ko'p instansiyada Redis tavsiya etiladi. |
| Audit logging | `audit_logs`: ro'yxatdan o'tish, kirish, loyiha/fayl amallari, AI so'rovlari, himoya, eksport, o'chirish, admin amallari va admin kirishlari (rad etilganlari ham). |
| Shaxsiy ma'lumotlar izolyatsiyasi | Admin ro'yxatlarida loyiha matni yo'q. Loyiha mazmuniga kirish faqat talaba bergan muddatli ruxsat + sabab bilan va auditda. |
| Fayllarni xavfsiz o'chirish | Lokal storage: fayl nol baytlar bilan qayta yozilib o'chiriladi; S3: obyekt o'chiriladi. DB dagi ajratilgan matn ham o'chiriladi. |
| API kalitlari loglarda yo'q | Loglarga faqat metod, yo'l, status, vaqt yoziladi (query/body emas). AI monitoringda prompt/javob matni yo'q. |
| AI ga yuborish roziligi | AI amallari `ai_consent_at` talab qiladi; ilova rozilik oynasini ko'rsatadi, Sozlamalarda bekor qilish mumkin. |
| Fayllar xususiy | Ochiq URL yo'q; fayllar faqat metadata sifatida ko'rinadi; S3 da server-side encryption. |
| Eksport va o'chirish | `GET /me/export` (JSON), `DELETE /me` (barcha ma'lumot + fayllar). |
| Sessiya ma'lumotlari | Tokenlar Flutter Secure Storage (Android Keystore) da; `allowBackup=false`. |

## Production tekshiruv ro'yxati

- [ ] `APP_ENV=production`, kuchli `JWT_SECRET` (aks holda server ishga tushmaydi)
- [ ] HTTPS (Caddy yoki boshqa reverse proxy), faqat release APK
- [ ] `CORS_ALLOWED_ORIGINS` faqat kerakli veb manzillar
- [ ] S3 bucket xususiy, versioning/lifecycle siyosati
- [ ] PostgreSQL zaxira nusxalari
- [ ] SMTP sozlangan (parol tiklash uchun)
- [ ] Release APK o'z keystore bilan imzolangan (`docs/BUILD_APK.md`)
