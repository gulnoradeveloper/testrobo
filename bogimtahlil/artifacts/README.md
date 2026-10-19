# artifacts/

O‘qitilgan model fayllari uchun katalog. Backend standart holatda `artifacts/model.pt` ni yuklaydi.

**Hozirgi holat:** `model.pt` — EfficientNet-B0 (`efficientnet_b0-kl-1.0.0`), Google Colab’da (T4 GPU) Chen 2018 /
OAI datasetining 5778 ta o‘qitish tasvirida o‘qitilgan, 826 ta tekshiruv tasviri bo‘yicha ResNet-18 bilan taqqoslanib
tanlangan, 1656 ta test tasvirida bir marta baholangan. Tafsilotlar: `model_card.json`, `../experiments/EXPERIMENT_REPORT.md`.
Tahlil uchun PyTorch kerak: `AI_ORNATISH.bat` (Windows) yoki `pip install -r backend/requirements-ai.txt`.

O‘qitish natijasida bu yerda paydo bo‘ladi (`ai/scripts/run_experiment.py`):

- `resnet18_best.pt`, `efficientnet_b0_best.pt` — har bir arxitekturaning validation bo‘yicha eng yaxshi checkpointi
- `model.pt` — validation bo‘yicha tanlangan va testda baholangan, dasturga eksport qilingan model

`model.pt` tarkibi:

- `model.pt` — vaznlar + arxitektura, sinflar tartibi, preprocess konfiguratsiyasi, dataset ma’lumoti, test metrikalari
- `model.pt.sha256` — SHA-256 qiymati (`BT_MODEL_SHA256` ga yozib, yuklashda tekshirish mumkin)
- `model_card.json` — model kartasi

`*.pt` fayllar git’ga qo‘shilmaydi (hajmi katta va dataset litsenziyasiga bog‘liq).
