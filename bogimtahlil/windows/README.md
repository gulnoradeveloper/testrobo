# Windows uchun tez yo‘l

Talab: **Python 3.11 yoki 3.12** (python.org, o‘rnatishda “Add python.exe to PATH” belgilansin). Node.js shart emas — interfeys tayyor yig‘ilgan holda (`frontend/dist`) keladi va backend uni o‘zi beradi.

1. `1_ornatish.bat` — virtual muhit (`.venv`), Python va frontend kutubxonalarini o‘rnatadi, muhitni tekshiradi.
2. `2_ishga_tushirish.bat` — serverni ishga tushiradi va brauzerda **http://127.0.0.1:8000** ni ochadi. Oyna ochiq turishi kerak.
3. `3_testlar.bat` — avtomatik testlar.

Keyingi buyruqlarni qo‘lda bajarishdan oldin har safar muhitni faollashtiring:

```bat
cd bogimtahlil
.venv\Scripts\activate
python ai\scripts\check_env.py
```

O‘qitilgan model bo‘lmasa, dastur ishlaydi, lekin tahlil “Sun’iy intellekt modeli hozircha tahlil qilish uchun
tayyor emas.” xabari bilan cheklanadi. Modelni o‘qitish uchun avval OAI ma’lumotlari kerak — `docs/MODEL_OQITISH.md`.

## Muammolar

- **Sahifa ochilmaydi (ERR_CONNECTION_REFUSED):** `2_ishga_tushirish.bat` oynasidagi xabarni o‘qing. Server ishga tushishi
  10–20 soniya oladi — sahifani yangilang. Manzil `http://127.0.0.1:8000` (5173 emas).
- **“8000-port band”:** boshqa dastur portni egallagan — uni yoping yoki kompyuterni qayta ishga tushiring.
- **`No module named ...`:** `1_ornatish.bat` ni qayta ishga tushiring.
- `ishlab_chiqish_vite.bat` — faqat interfeys kodini o‘zgartiruvchilar uchun (Node.js kerak).
