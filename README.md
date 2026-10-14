# BEGOYIM MVP

**Loyiha muallifi:** Bo‘ronova Gulnora Yodgorovna  
© 2026 Bo‘ronova Gulnora Yodgorovna. Barcha huquqlar himoyalangan. BEGOYIM nomi, logotipi, konsepsiyasi va platformasi muallifning intellektual mulki hisoblanadi; muallif ruxsatisiz nusxa ko‘chirish va tarqatish taqiqlanadi.

**Ayollar bandligi va farovonligi raqamli ekotizimi** — *“Ayoldan ayolga — imkoniyat va ko‘mak.”*

Texnik topshiriq (TT) asosida tayyorlangan MVP: ayollar ko‘nikmasini xizmatga aylantirish, mahalla orqali verifikatsiya,
AI Smart Matching, buyurtma va daromadni boshqarish hamda psixologik yordamga yozilish.

## Tez ishga tushirish (lokal, SQLite)

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo          # hududlar, 13 kategoriya, ko‘nikmalar + demo foydalanuvchilar
python manage.py runserver
```

Brauzerda: http://127.0.0.1:8000 · Django admin: http://127.0.0.1:8000/admin/

## Docker (PostgreSQL + Nginx + Gunicorn)

```bash
cp .env.example .env      # DJANGO_SECRET_KEY va POSTGRES_PASSWORD ni o‘zgartiring
docker compose up -d --build
```

`SEED_ARGS=` (bo‘sh) qilsangiz, demo foydalanuvchilar ham yuklanadi; standart holatda faqat ma’lumotnomalar yuklanadi.
HTTPS sertifikati (masalan, certbot) sozlangach `.env` da `DJANGO_SECURE_SSL_REDIRECT=1` qiling — shunda secure cookie va HSTS yoqiladi.

## Demo hisoblar (parol hammasi uchun: `Begoyim2026!`)

| Rol | Telefon | Izoh |
|---|---|---|
| Administrator | +998900000001 | `/panel/` va `/admin/` |
| Mahalla vakili | +998900000002 | Buxoro sh., Navbahor MFY |
| Mahalla vakili | +998900000003 | Toshkent, Chilonzor, Qatortol MFY |
| Psixolog | +998900000004, +998900000005 | Nodira Karimova, Malika Sobirova |
| Xizmat ko‘rsatuvchi | +998901000001 … +998901000009 | Dilnoza, Mohira, Gulchehra, … |
| Buyurtmachi | +998902000001 … +998902000003 | Sevara, Kamola, Dildora |

> Demo ma’lumotlar faqat taqdimot uchun. Production’da `seed_demo --reference-only` ishlating.

## Jonli demo ssenariysi (TT, 26-bo‘lim)

1. **Ro‘yxatdan o‘tish** → “Xizmat ko‘rsatuvchi” roli, Buxoro sh. / Navbahor MFY.
2–3. **Profil** va **ko‘nikma** (“Parda tikish”), portfolio rasmi.
4. Profil sahifasida **“Mahalla verifikatsiyasiga yuborish”**.
5. `+998900000002` bilan kirib, **Kabinet → Verifikatsiya arizalari → Tasdiqlash**.
6. Ayol **Xizmatlarim → Yangi xizmat** — “Parda tikish”.
7. `+998902000001` bilan **Xizmatlar** sahifasida qidiruv.
8. **AI tavsiya**: “Ertaga Buxoro shahrida parda tikib beradigan ayol kerak”.
9. **Buyurtma berish** → 10. ijrochi **Qabul qilish** → 11. **Ishni boshladim** (IN_PROGRESS) → 12. **Ishni yakunladim** (COMPLETED).
13. Buyurtmachi **baho** beradi (faqat bir marta, faqat COMPLETED).
14. Ijrochi **Daromad** dashboardida buyurtma va hisoblangan daromad.
15. **Mahalla dashboardida** agregat ko‘rsatkichlar yangilanadi.

Bu ssenariy avtomatik test sifatida ham yozilgan: `python manage.py test apps`
(`apps/core/tests.py` — 15 bosqich, RBAC, mahalla hududi cheklovi, psixologik maxfiylik, rate limit, fayl tekshiruvi, API oqimi).

## Arxitektura

```
config/            Django sozlamalari, URL
apps/core          hududlar (viloyat/tuman/mahalla), bildirishnomalar, shikoyatlar, audit log,
                   bosh sahifa, admin panel (/panel/), PWA (manifest + service worker)
apps/accounts      telefon asosidagi User (rollar), Profile, Skill/UserSkill, portfolio,
                   VerificationRequest, mahalla dashboardi
apps/catalog       Category, Service, ServiceImage, Favorite, Order, OrderStatusHistory, Review,
                   qidiruv/filtrlash, daromad dashboardi
apps/psychology    Psychologist, PsychologistSchedule, Consultation (maxfiy)
apps/ai            AI qatlam: parser.py (intent/parametrlar) + matcher.py (MatchScore)
apps/api           Django REST Framework + JWT, rolga asoslangan ruxsatlar
templates/, static/  EduWell (TemplateMo 573) shabloni BEGOYIM brend ranglariga moslangan
```

Biznes-logika `services.py` modullarida — web sahifalar ham, REST API ham bir xil qoidalarni ishlatadi
(holat o‘tishlari, verifikatsiya, sharh, bildirishnoma, audit).

### Frontend
TT Next.js + Tailwind’ni tavsiya qiladi; ushbu MVP’da buyurtmachi taqdim etgan **EduWell** HTML shabloni va
**BEGOYIM logotiplari** asosida Django server-rendered frontend qilingan (mobil-first, katta tugmalar, PWA).
REST API (`/api/...`) tayyor — keyingi bosqichda Next.js frontend shu API ustiga qurilishi mumkin.

### AI Smart Matching
```
So‘rov → matnni normallashtirish → intent/parametrlar (xizmat, hudud, vaqt, shakl)
       → bazadan faol xizmatlar → MatchScore → Top 3–5 → tushuntirish
MatchScore = xizmat mosligi (40) + hudud mosligi (25) + reyting (15) + verifikatsiya (10) + mavjudlik (10)
```
Kategoriya kalit so‘zlari admin paneldan tahrirlanadi. AI faqat bazada mavjud xizmatlarni qaytaradi,
hech narsani “tasdiqlamaydi” va qaror qabul qilmaydi.

### Buyurtma holatlari
`NEW → ACCEPTED → IN_PROGRESS → COMPLETED`, shuningdek `REJECTED` (ijrochi) va `CANCELLED` (buyurtmachi).
Mijoz manzilidagi buyurtmalarda **BEGOYIM Safe**: “Ishni boshladim / Ishni yakunladim” vaqti qayd qilinadi.
SOS/geolokatsiya MVP’da ishlaydigan funksiya sifatida ko‘rsatilmaydi (BEGOYIM 2.0).

## REST API

| Endpoint | Ruxsat |
|---|---|
| `POST /api/auth/register`, `POST /api/auth/login` (JWT), `POST /api/auth/refresh` | hamma (throttle) |
| `GET /api/profile`, `PATCH /api/profile/update` | tizimga kirgan |
| `GET /api/categories`, `/api/regions`, `/api/districts?region=`, `/api/mahallas?district=` | hamma |
| `GET/POST /api/services`, `GET/PATCH/DELETE /api/services/{id}` | o‘qish — hamma; yozish — faqat o‘z xizmatlari (ijrochi) |
| `GET /api/search?q=&category=&region=&price_min=&price_max=&min_rating=&verified=1&mode=&sort=` | hamma |
| `POST /api/ai/match` `{"text": "..."}` | hamma (throttle) |
| `GET/POST /api/orders`, `GET /api/orders/{id}`, `POST /api/orders/{id}/status` | ishtirokchilar |
| `GET/POST /api/reviews` | faqat buyurtmachi, faqat COMPLETED |
| `GET/POST /api/verification`, `POST /api/verification/{id}/decide` | ijrochi / o‘z mahallasi vakili |
| `GET /api/psychologists`, `GET/POST /api/consultations` | konsultatsiya — faqat mijoz va psixolog |
| `GET /api/notifications`, `POST /api/notifications/read_all` | o‘z bildirishnomalari |
| `GET/POST/PATCH /api/reports` | holatni faqat admin o‘zgartiradi |
| `GET /api/dashboard/provider` · `/mahalla` · `/admin` | tegishli rol |

## Xavfsizlik (TT, 23-bo‘lim)

- Parollar PBKDF2 xesh bilan saqlanadi; parol murakkabligi tekshiriladi.
- RBAC: web’da `role_required`, API’da rol permission klasslari; mahalla vakili faqat o‘z mahallasini ko‘radi.
- **Psixologik maxfiylik**: `Consultation` admin panelda ro‘yxatdan o‘tkazilmagan; mazmun bildirishnomaga,
  mahalla/admin dashboardiga va statistikaga chiqmaydi.
- CSRF, XSS (template autoescape), SQL injection (ORM), clickjacking himoyasi; xavfsiz `next` redirect.
- Rate limiting: login (5 urinish / 15 daqiqa), DRF throttle, Nginx `limit_req`.
- Fayl yuklash: faqat jpg/png/webp, 5 MB gacha, Pillow orqali haqiqiy rasm tekshiruvi.
- Audit log (`/admin/core/auditlog/`): ro‘yxatdan o‘tish, kirish, verifikatsiya, buyurtma holati, moderatsiya.
- Production: HTTPS redirect, secure cookie, HSTS (env orqali). Zaxira nusxa: `pg_dump` (PostgreSQL volume).
- Minimal ma’lumot: tug‘ilgan yil **yoki** yosh diapazoni.

## MVP chegaralari

- SMS OTP integratsiyasi qilinmagan (TT talabiga ko‘ra soxta “SMS yuborildi” yaratilmagan) — keyingi integratsiya.
- To‘lov tizimi, native mobil ilova, GPS tracking, video konsultatsiya — BEGOYIM 2.0 roadmap.
- Bildirishnomalar — ichki web notification center (SMS/Telegram/push keyinroq).
- Kategoriya rasmlari: `static/begoyim/img/categories/<slug>.jpg`; admin paneldan (Kategoriyalar → Rasm) yangisini yuklash mumkin.
