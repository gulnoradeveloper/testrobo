# Windows uchun tez yo‘l

Talablar: **Python 3.11 yoki 3.12** (python.org, o‘rnatishda “Add python.exe to PATH” belgilansin) va **Node.js 20+**.

1. `1_ornatish.bat` — virtual muhit (`.venv`), Python va frontend kutubxonalarini o‘rnatadi, muhitni tekshiradi.
2. `2_ishga_tushirish.bat` — backend (8000) va frontendni (5173) ochadi, brauzerni ishga tushiradi.
3. `3_testlar.bat` — avtomatik testlar.

Keyingi buyruqlarni qo‘lda bajarishdan oldin har safar muhitni faollashtiring:

```bat
cd bogimtahlil
.venv\Scripts\activate
python ai\scripts\check_env.py
```

O‘qitilgan model bo‘lmasa, dastur ishlaydi, lekin tahlil “Sun’iy intellekt modeli hozircha tahlil qilish uchun
tayyor emas.” xabari bilan cheklanadi. Modelni o‘qitish uchun avval OAI ma’lumotlari kerak — `docs/MODEL_OQITISH.md`.
