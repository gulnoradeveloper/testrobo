# artifacts/

O‘qitilgan model fayllari uchun katalog. Backend standart holatda `artifacts/model.pt` ni yuklaydi.

**Hozirgi holat: o‘qitilgan model mavjud emas.** Shu sababli dastur tahlil funksiyasini bajarmaydi va
“Sun’iy intellekt modeli hozircha tahlil qilish uchun tayyor emas.” xabarini ko‘rsatadi.

O‘qitish natijasida bu yerda paydo bo‘ladi (`ai/scripts/run_experiment.py`):

- `resnet18_best.pt`, `efficientnet_b0_best.pt` — har bir arxitekturaning validation bo‘yicha eng yaxshi checkpointi
- `model.pt` — validation bo‘yicha tanlangan va testda baholangan, dasturga eksport qilingan model

`model.pt` tarkibi:

- `model.pt` — vaznlar + arxitektura, sinflar tartibi, preprocess konfiguratsiyasi, dataset ma’lumoti, test metrikalari
- `model.pt.sha256` — SHA-256 qiymati (`BT_MODEL_SHA256` ga yozib, yuklashda tekshirish mumkin)
- `model_card.json` — model kartasi

`*.pt` fayllar git’ga qo‘shilmaydi (hajmi katta va dataset litsenziyasiga bog‘liq).
