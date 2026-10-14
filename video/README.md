# BEGOYIM taqdimot videosi (kod orqali)

~150 soniya, 1920×1080, 30 fps, o‘zbek tilida. Fon musiqasi — `music.py` da kod bilan yaratilgan original kompozitsiya (dutor, nay, doira; Re minor, 96 BPM), tashqi namunalarsiz.

Auditoriya: mahalla raislari, Oila va xotin-qizlar bo‘limi vakillari va qaror qabul qiluvchi rahbarlar. Urg‘u — ayollarning
mavjud imkoniyatlarini daromadga aylantirish; video uchta savolga javob beradi:
1) qanday muammoni hal qiladi, 2) hududga qanday natija beradi, 3) nega qo‘llab-quvvatlash kerak.

| Vaqt | Sahna |
|---|---|
| 0–7 s | Logotip: “Har bir ayol imkoniyatga loyiq!” |
| 7–17 s | Har bir mahallada iste’dod, har bir xonadonda imkoniyat |
| 17–24 s | ① Muammo: yangi kasb emas — mehnatini qadrlaydigan mijoz kerak |
| 24–33 s | Yechim: hunar va mijoz o‘rtasidagi raqamli ko‘prik (AI) |
| 33–40 s | Ish o‘rni faqat korxonada yaratilmaydi — uydan turib daromad |
| 40–47 s | Mahalla — bandlikning eng yaqin hamkori |
| 47–75 s | Platformadagi yo‘l: 7 qadam, haqiqiy skrinshotlar |
| 75–83 s | Sun’iy intellekt moslashtiruvi (haqiqiy natija) |
| 83–91 s | Ishonch va farovonlik: tasdiqlash, baholash, psixolog |
| 91–100 s | ② Oila va xotin-qizlar bo‘limi uchun o‘lchanadigan natija |
| 100–110 s | Pilot bosqich maqsadli ko‘rsatkichlari (5 / 500 / 200 / 100) — erishilgan natija emas |
| 110–120 s | ③ Aniq hamkorlik modeli (5 hamkor) |
| 120–128 s | Mahalla hamda Oila va xotin-qizlar bo‘limi vakillariga murojaat |
| 128–140 s | Final: Mahalla + Oila va xotin-qizlar bo‘limi + Raqamli texnologiya = Ayollar bandligi va farovonligi |
| 140–150 s | Loyiha muallifi: Bo‘ronova Gulnora Yodgorovna, mualliflik huquqi |

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

## Tayyor qo‘shiqdan minus (instrumental) olish

```bash
pip install onnxruntime numpy
curl -LO https://github.com/TRvlvr/model_repo/releases/download/all_public_uvr_models/UVR-MDX-NET-Inst_HQ_3.onnx
python video/separate.py qoshiq.mp3 minus.wav --model UVR-MDX-NET-Inst_HQ_3.onnx
python video/render.py --music minus.wav
```

Qo‘shiq va minus fayllari repozitoriyaga qo‘shilmaydi. Videoni ommaga tarqatishda qo‘shiq mualliflik
huquqi egasining ruxsatini olish tavsiya etiladi; `--music` berilmasa, `music.py` dagi original kompozitsiya ishlatiladi.
