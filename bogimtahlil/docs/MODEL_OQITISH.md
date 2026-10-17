# Sun’iy intellekt modelini o‘qitish, baholash va dasturga ulash

Barcha bosqichlar `ai/` katalogidagi kod bilan bajariladi. Training va inference **bir xil** `kltool` paketidan
foydalanadi (preprocess, arxitektura, checkpoint formati, Grad-CAM).

> **Hozirgi holat:** OAI dataseti yuklanmagan, model o‘qitilmagan, `artifacts/model.pt` yo‘q.
> Quyidagi kod sintetik OAI-formatidagi ma’lumotlarda uchidan-uchiga sinovdan o‘tkazilgan; haqiqiy natijalar
> faqat siz real ma’lumotda ishga tushirgandan keyin paydo bo‘ladi (`experiments/EXPERIMENT_REPORT.md`).

## Qisqa yo‘l (bitta buyruq)

```bash
pip install -r ai/requirements.txt
python ai/scripts/build_oai_manifest.py --labels data/raw/oai/kXR_SQ_BU*.txt \
    --image-index data/raw/knee_crops/index.csv --out data/raw/manifest.csv
python ai/scripts/run_experiment.py --manifest data/raw/manifest.csv \
    --dataset-name "Osteoarthritis Initiative (OAI)" --dataset-license "OAI Data Use Agreement"
```

`run_experiment.py` ketma-ket bajaradi: ajratish → ResNet-18 va EfficientNet-B0 ni o‘qitish → ikkalasini
validation’da baholash → validation bo‘yicha tanlash → tanlangan modelni testda **bir marta** baholash →
`artifacts/model.pt` ga eksport → CPU tezligini o‘lchash → `experiments/EXPERIMENT_REPORT.md`.
Keyin serverni qayta ishga tushiring — model avtomatik yuklanadi.

## 1. OAI ma’lumotlarini olish

1. OAI ma’lumotlari bepul, lekin **ro‘yxatdan o‘tish va Data Use Agreement’ni qabul qilish** talab qilinadi:
   - https://oai.epi-ucsf.org/datarelease (UCSF — OAI ma’lumotlar relizlari, ASCII/SAS fayllar);
   - https://nda.nih.gov/oai (NIH NDA — tasvirlar va relizlar).
   Ishlab chiqish muhitidan bu saytlarga kirish imkoni bo‘lmadi — yuklab olishni o‘zingiz bajarasiz.
   Ma’lumotlarni qayta tarqatish taqiqlangan — `data/` git’ga qo‘shilmaydi.
2. Yuklab oling:
   - KL yorliqlari: *Semi-Quantitative Central Reading of Knee X-rays (Boston University)* — `kXR_SQ_BU##` fayllari
     (har biri bitta tashrif: 00, 01, 03, 05, 06, 08, 10) va ularning **data dictionary**’si;
   - bilateral PA fixed-flexion tizza rentgen tasvirlari (DICOM).
3. **Ustun nomlarini tekshiring.** `ai/configs/oai_columns.yaml` dagi nomlar (`ID`, `SIDE`, `READPRJ`,
   `V##XRKL`, SIDE kodlari `1=R, 2=L`, ajratuvchi `|`) data dictionary bilan solishtirilmagan
   (`verified: false`) — ishlab chiqish muhitidan nda.nih.gov ga kirish imkoni bo‘lmadi. Solishtirib, to‘g‘ri
   bo‘lsa `verified: true` qiling, aks holda tuzating. Shungacha `build_oai_manifest.py` ishlamaydi.
   Ustun topilmasa, kod mavjud ustunlar ro‘yxati bilan xato beradi — taxminiy birlashtirish qilinmaydi.

## 2. Bitta tizza tasvirlari va tasvir indeksi

OAI rentgeni ikki tizzani birga ko‘rsatadi; MVP bitta tizza tasvirini qabul qiladi. Har bir tizzani alohida PNG
ga kesing (usulni hisobotda yozing) va `index.csv` tuzing:

```
image_path,patient_id,knee_side,visit_id,projection
crops/9000099_V00_R.png,9000099,R,V00,PA
```

**Tomonni tekshiring:** PA rentgenda bemorning o‘ng tizzasi odatda tasvirning chap tomonida bo‘ladi (DICOM
belgilariga qarab tasdiqlang). Tomon xatosi yorliqlarni noto‘g‘ri bog‘laydi.

## 3. Manifest: yorliqlarni tasvirlar bilan bog‘lash — `build_oai_manifest.py`

- KL qiymati `"2"` yoki `"2: 2"` ko‘rinishida bo‘lishi mumkin — boshidagi butun son olinadi; `"."` bilan
  boshlanadigan yetishmayotgan qiymat kodlari chiqariladi.
- Bitta (bemor, tomon, tashrif) uchun bir nechta o‘qish (`READPRJ`) bo‘lsa: bir xil bo‘lsa olinadi, farq qilsa
  chiqariladi (`duplicate_policy: agree_or_drop`) yoki `prefer_project` bo‘yicha tanlanadi.
- Bog‘lash kaliti `(patient_id, knee_side, visit_id)`, qat’iy 1:1. Frontal bo‘lmagan, bitta kalitga bir nechta
  tasvir to‘g‘ri kelgan va yorlig‘i yo‘q tasvirlar chiqariladi; hammasi `manifest_report.json` da sanaladi.

Natija ustunlari: `image_path, patient_id, knee_side, visit_id, projection, kl_grade, dataset_source` (+ `split`).

## 4. Bemorlar bo‘yicha 70/15/15 — `prepare_dataset.py`

Bemorlar (eng yuqori KL bo‘yicha stratifikatsiya, `seed=42`) guruhlarga ajratiladi; bitta bemor ikki guruhga
tushsa skript to‘xtaydi. `dataset_report.json`: har bir guruhdagi tasvirlar, bemorlar, KL0–KL4 soni, takrorlar.
`tests/ai/test_real_split.py` real taqsimot mavjud bo‘lganda kesishmani avtomatik tekshiradi.

## 5. O‘qitish — `train.py`

| Parametr | Qiymat |
|---|---|
| Transfer learning | ImageNet vaznlari, oxirgi qatlam → 5 sinf |
| Kirish | 224×224, kesmasdan (letterbox), ImageNet normallashtirish |
| Optimizer / lr | AdamW, 1e-4, weight decay 0.01 |
| Loss | Weighted Cross-Entropy (train guruhidagi teskari chastota) |
| Batch / epoch | 32 / ≤ 50, early stopping 7 (validation macro F1) |
| Seed | 42 |
| Augmentatsiya (faqat train) | gorizontal aks ettirish, ±7°, yorqinlik/kontrast |

ImageNet vaznlari yuklab olinmasa, o‘qitish **to‘xtaydi** (tasodifiy vaznlardan jimgina boshlanmaydi).
Internetsiz muhitda: vaznlar faylini `pretrained_weights:` orqali ko‘rsating.

Natija: `experiments/<arch>/history.csv` (har epoch: train/val loss, accuracy, balanced acc, macro P/R/F1, QWK,
sinflar bo‘yicha recall, vaqt), `training_curves.png`, `val_metrics.json`, `best.pt`, va nusxasi
`artifacts/resnet18_best.pt` / `artifacts/efficientnet_b0_best.pt`.
Ikkala model bir xil manifest, sinflar tartibi va baholash kodidan foydalanadi (`compare_models.py` buni tekshiradi).

## 6–7. Baholash va tanlash

- `evaluate.py --split val` — ikkala model uchun barcha metrikalar + `confusion_val.png`.
- `compare_models.py` — **faqat validation macro F1** (teng bo‘lsa QWK) bo‘yicha tanlaydi → `model_comparison.json/.md`.
- `evaluate.py --split test` — faqat tanlangan model. Birinchi test bahosi `experiments/test_lock.json` ga
  yoziladi; boshqa checkpointni testda baholashga urinish **rad etiladi**.

## 8. Eksport — `export_model.py`

`artifacts/model.pt`: arxitektura, sinflar tartibi, tasvir o‘lchami, mean/std, preprocess versiyasi, model versiyasi,
dataset, validation va test metrikalari, tanlash sababi. SHA-256 — `model.pt.sha256` va `model_card.json` da.
Eksportdan so‘ng fayl backend yuklovchisi (`load_checkpoint`) bilan qayta tekshiriladi.

## 9. Backendga ulash

Server ishga tushganda `artifacts/model.pt` ni yuklaydi (standart sozlamada faqat `trained` checkpoint).
`tests/backend/test_real_model.py` real model mavjud bo‘lganda: yuklanishi, 5 ta ehtimollik, API natijasi
modelning bevosita chiqishiga tengligi, PDF yaratilishini tekshiradi:

```bash
pytest tests/backend/test_real_model.py tests/ai/test_real_split.py
```

## Ehtimolliklar kalibrlanishi

Softmax qiymatlari kalibrlanmagan (`calibration_evaluated: false`), interfeys buni ochiq ko‘rsatadi.
