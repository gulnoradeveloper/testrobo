# Sun’iy intellekt modelini tayyorlash (qayta ishlab ko‘riladigan tajriba)

Barcha bosqichlar `ai/` katalogidagi kod bilan bajariladi. Training va inference **bir xil** `kltool` paketidan
foydalanadi (preprocess, arxitektura, checkpoint formati, Grad-CAM) — shu tufayli ular orasida nomuvofiqlik bo‘lmaydi.

## 0. Muhit

```bash
pip install -r ai/requirements.txt          # GPU uchun mos PyTorch CUDA versiyasini o‘rnating
```

ImageNet vaznlari (`pretrained: true`) birinchi ishga tushirishda `download.pytorch.org` dan yuklab olinadi.

## 1. Dataset: Osteoarthritis Initiative (OAI)

1. https://nda.nih.gov/oai saytida ro‘yxatdan o‘ting va **OAI Data Use Agreement** shartlarini qabul qiling.
   Shartlar ma’lumotlarni qayta tarqatishni taqiqlaydi — tasvirlar va yorliqlarni ochiq repozitoriyga joylamang.
2. Rentgen tasvirlari (bilateral PA fixed-flexion) va KL yorliqlari (masalan, `kXR_SQ_BU##` fayllaridagi `V##XRKL`)
   ni yuklab oling.
3. Har bir tizzani alohida tasvirga ajrating (MVP bitta tizza tasvirini qabul qiladi). Ajratish usulini
   (qo‘lda / avtomatik lokalizatsiya) tajriba hisobotida yozing.
4. `data/raw/manifest.csv` tuzing:

| ustun | izoh |
|---|---|
| `image_path` | bitta tizza tasviri (PNG/JPG), manifestga nisbatan yo‘l |
| `patient_id` | OAI `ID` (anonim) |
| `side` | `L` / `R` |
| `view` | `PA` (frontal) — boshqalari avtomatik chiqariladi |
| `timepoint` | `V00`, `V01`, ... |
| `kl_grade` | 0..4 — aynan shu tizza, shu tashrif uchun |

Agar sizda sinflar bo‘yicha papkalarga ajratilgan tayyor dataset bo‘lsa (`<split>/<grade>/*.png`),
`ai/scripts/import_folder_dataset.py` manifest yaratadi. Bemor ID fayl nomida bo‘lmasa, bemor bo‘yicha
ajratishni **tekshirib bo‘lmaydi** — buni cheklov sifatida hujjatlashtiring.

## 2. Tozalash va bemorlar bo‘yicha 70/15/15 ajratish

```bash
python ai/scripts/prepare_dataset.py --manifest data/raw/manifest.csv --out data/splits
```

Skript: noto‘g‘ri KL qiymatlari, frontal bo‘lmagan proyeksiyalar, takrorlangan (bemor, tomon, vaqt) kalitlari,
bayt darajasida bir xil tasvirlar (SHA-256), bir xil tasvirga turli yorliqlar va topilmagan fayllarni aniqlaydi;
bemorlarni (eng yuqori KL bo‘yicha stratifikatsiya, `seed=42`) train/val/test ga ajratadi va **bitta bemor
bir nechta guruhga tushsa to‘xtaydi**. Natija: `data/splits/dataset_report.json` (sinflar nomutanosibligi ham shu yerda).

## 3. O‘qitish

```bash
python ai/scripts/train.py --config ai/configs/resnet18.yaml
python ai/scripts/train.py --config ai/configs/efficientnet_b0.yaml
```

Parametrlar (TT 10-bo‘lim): 224×224, AdamW, lr = 1e-4, batch 32, ≤ 50 epoch, early stopping 7, Weighted
Cross-Entropy (teskari chastota vaznlari), seed 42. Har bir epoch `experiments/<arch>/history.csv` ga yoziladi.
Eng yaxshi checkpoint **faqat validation macro F1** bo‘yicha saqlanadi. Augmentatsiya: gorizontal aks ettirish,
±7° burish, yorqinlik/kontrast — faqat train guruhida.

## 4. Modellarni taqqoslash (validation bo‘yicha)

```bash
python ai/scripts/compare_models.py experiments/resnet18 experiments/efficientnet_b0
```

## 5. Yakuniy test — faqat tanlangan model uchun, bir marta

```bash
python ai/scripts/evaluate.py --checkpoint experiments/efficientnet_b0/best.pt --split test
```

Hisoblanadi: Accuracy, Balanced Accuracy, Precision/Recall/F1 (sinflar bo‘yicha va macro), Confusion Matrix,
Quadratic Weighted Kappa va KL0–KL1–KL2 o‘zaro chalkashish tahlili (`early_grade_confusion`).
Test natijasiga qarab giperparametrlarni o‘zgartirish **taqiqlanadi** (aks holda test mustaqil bo‘lmay qoladi).

## 6. Eksport va dasturga ulash

```bash
python ai/scripts/export_model.py --run experiments/efficientnet_b0 \
    --dataset-name "Osteoarthritis Initiative (OAI)" --dataset-license "OAI Data Use Agreement" \
    --dataset-notes "PA fixed-flexion, V00–V06, bitta tizza kesmalari" --out artifacts/model.pt
python ai/scripts/benchmark.py --checkpoint artifacts/model.pt --image <tizza.png>
```

Server qayta ishga tushirilgach, “Sun’iy intellekt modeli” sahifasida test metrikalari avtomatik ko‘rinadi.

## Ehtimolliklar kalibrlanishi

Softmax qiymatlari kalibrlanmagan. `export_model.py` `calibration_evaluated: false` yozadi va interfeys buni
ochiq ko‘rsatadi. Kalibrlash (masalan, temperature scaling + ECE) kelgusi ish sifatida qoldirilgan.
