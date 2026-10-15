# Bo‘g‘imTahlil — model tajribasi hisoboti

Yaratilgan: 2026-10-15 06:46 UTC · manba: `ai/scripts/make_report.py` (raqamlar faqat tajriba fayllaridan olinadi)

## 1–2. Ma’lumotlar to‘plami va taqsimot

**MAVJUD EMAS** — dataset hali tayyorlanmagan (`build_oai_manifest.py`, so‘ng `prepare_dataset.py`).

## 3. ResNet-18 (validation)

**MAVJUD EMAS** — model o‘qitilmagan (`train.py --config ai/configs/resnet18.yaml`)

## 4. EfficientNet-B0 (validation)

**MAVJUD EMAS** — model o‘qitilmagan (`train.py --config ai/configs/efficientnet_b0.yaml`)

## 5. Tanlangan model

**MAVJUD EMAS** — `compare_models.py` ishga tushirilmagan.

## 6. Mustaqil sinov (test) natijalari

**MAVJUD EMAS** — yakuniy test bajarilmagan (`evaluate.py --split test`)

## 7. `artifacts/model.pt`

**MAVJUD EMAS** — tahlil funksiyasi cheklangan holatda (API `503 MODEL_NOT_READY`).

## 8. Backend integratsiyasi

Integratsiya kodi tayyor va testlangan, lekin o‘qitilgan model yo‘qligi sababli real tahlil o‘chirilgan.

## 9. Cheklovlar

- Ehtimolliklar kalibrlanmagan (`calibration_evaluated: false`).
- Model faqat bitta tizzaning frontal (PA) rentgen tasviri uchun o‘qitilgan; proyeksiya avtomatik aniqlanmaydi.
- Natijalar bitta dataset (manba yuqorida) bo‘yicha; boshqa qurilma va populyatsiyalarda tashqi validatsiya qilinmagan.
- Klinik tashxis vositasi emas.
