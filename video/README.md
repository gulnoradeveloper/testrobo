# BEGOYIM taqdimot videosi (kod orqali)

~96 soniya, 1920×1080, 30 fps, o‘zbek tilida, sintez qilingan fon musiqasi bilan.

| Vaqt | Sahna |
|---|---|
| 0–6 s | Logotip va shior |
| 6–15 s | Muammo: mohir ayollar, lekin mahorat daromadga aylanmaydi |
| 15–22 s | Yechim: BEGOYIM va 13 ta xizmat yo‘nalishi |
| 22–26 s | Qahramon: Aziza opa (Buxoro, Navbahor MFY) |
| 26–56 s | Platformadagi yo‘l — 7 qadam, haqiqiy skrinshotlar |
| 56–64 s | AI Smart Matching (haqiqiy natijalar) |
| 64–72 s | Ishonch: mahalla tasdig‘i, BEGOYIM Safe, psixologik yordam |
| 72–78 s | Mahalla dashboardi |
| 78–86 s | Final va chaqiriq |
| 86–96 s | Loyiha muallifi: Bo‘ronova Gulnora Yodgorovna, mualliflik huquqi |

## Qayta yaratish

```bash
pip install playwright numpy imageio-ffmpeg
python manage.py migrate && python manage.py seed_demo
python manage.py runserver 127.0.0.1:8765      # skrinshotlar uchun (ixtiyoriy)
python video/capture.py                         # assets/shots/ ni yangilash
python video/render.py --preview 3 40 70        # alohida kadrlarni tekshirish
python video/render.py                          # video/out/begoyim_taqdimot.mp4
```

Matn va vaqtlarni `scenes.html` dagi `render(t)` funksiyasida o‘zgartirish mumkin.
Shriftlar: Playfair Display, Open Sans, Great Vibes (SIL Open Font License).
