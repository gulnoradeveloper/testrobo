# Bo‘g‘imTahlil taqdimot videosi (kod orqali)

~2 daqiqa (122 s), 1920×1080, 30 fps, o‘zbek tilida. Barcha raqamlar `experiments/EXPERIMENT_REPORT.md` dan,
dastur kadrlari — o‘qitilgan model bilan ishlayotgan dasturning haqiqiy skrinshotlari (`capture.py`).
Fon musiqasi `render.py` da numpy bilan sintez qilingan original kompozitsiya (tashqi namunasiz).

| Vaqt | Sahna |
|---|---|
| 0–7 s | Logotip, “Aniq tahlil sari aqlli qadam!” |
| 7–17 s | Muammo: tizza osteoartriti, KL baholashning qiyinligi |
| 17–27 s | Yechim: rentgen → tekshiruv → neyron tarmoq → KL0–KL4 → Grad-CAM va PDF |
| 27–37 s | KL0–KL4 darajalari (datasetdagi haqiqiy rentgenlar) |
| 37–90 s | Namoyish: bosh sahifa, yuklash, natija (KL4, 98,1%), Grad-CAM, PDF va tarix, model sahifasi |
| 90–101 s | O‘qitish: 8 260 rentgen, ResNet-18 va EfficientNet-B0 qiyosi, tanlov |
| 101–110 s | Mustaqil sinov: Accuracy 64,7% · Macro F1 0,678 · QWK 0,826 |
| 110–116 s | Texnologiyalar, ishonchlilik va cheklovlar |
| 116–122 s | Final |

## Qayta yaratish (bogimtahlil/ ildizidan)

```bash
pip install -r backend/requirements.txt -r backend/requirements-ai.txt playwright numpy
python video/capture.py                       # video/assets/ — skrinshotlar (server o‘zi ishga tushadi)
python video/render.py --preview 4 50 105     # alohida kadrlarni tekshirish (video/out/preview_*.png)
python video/render.py                        # video/out/bogimtahlil_taqdimot.mp4 va _web.mp4
```

Talablar: ffmpeg, pdftoppm (poppler), Chromium (`BT_CHROME` muhit o‘zgaruvchisi bilan yo‘lini berish mumkin).
Matn va vaqtlar `scenes.html` dagi `SCENES` ro‘yxatida.
