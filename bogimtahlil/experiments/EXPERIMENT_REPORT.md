# Bo‘g‘imTahlil — model tajribasi hisoboti

Yaratilgan: 2026-10-19 03:30 UTC · manba: `ai/scripts/make_report.py` (raqamlar faqat tajriba fayllaridan olinadi)

## 1–2. Ma’lumotlar to‘plami va taqsimot

Jami tasvirlar: **8260**, bemorlar: **ma’lum emas** (datasetda bemor ID yo‘q), manba: Knee Osteoarthritis Severity Grading Dataset (Chen, Mendeley Data 2018; OAI asosida)
Ajratish: manifestdagi tayyor split (datasetning o‘z train/val/test taqsimoti).

| Guruh | Tasvirlar | Ulushi | KL0 | KL1 | KL2 | KL3 | KL4 |
|---|---|---|---|---|---|---|---|
| train | 5778 | 70.0% | 2286 | 1046 | 1516 | 757 | 173 |
| val | 826 | 10.0% | 328 | 153 | 212 | 106 | 27 |
| test | 1656 | 20.0% | 639 | 296 | 447 | 223 | 51 |

**Cheklov:** Datasetda bemor identifikatorlari yo‘q — bemorlar bo‘yicha ajratishni tekshirib bo‘lmaydi; bitta bemorning tasvirlari turli guruhlarga tushgan bo‘lishi mumkin.

Tozalash: {"ambiguous_knee_visit_records_removed": 0, "identical_images_removed": 0, "identical_images_with_conflicting_labels": 0, "identical_images_across_patients": 0}

## 3. ResNet-18 (validation)

Eng yaxshi epoch: 9 / 16, o‘qitish vaqti: 6.5 daq, qurilma: cuda, transfer learning: ha. Grafiklar: `resnet18/training_curves.png`, `resnet18/confusion_val.png`

Tasvirlar: 826, bemorlar: 826

| Ko‘rsatkich | Qiymat |
|---|---|
| Accuracy | 0.6174 |
| Balanced Accuracy | 0.6758 |
| Macro Precision | 0.6555 |
| Macro Recall | 0.6758 |
| Macro F1 | 0.6581 |
| Quadratic Weighted Kappa | 0.7829 |

| Sinf | Precision | Recall | F1 | Soni |
|---|---|---|---|---|
| KL0 | 0.756 | 0.680 | 0.716 | 328 |
| KL1 | 0.359 | 0.490 | 0.414 | 153 |
| KL2 | 0.654 | 0.481 | 0.554 | 212 |
| KL3 | 0.616 | 0.802 | 0.697 | 106 |
| KL4 | 0.893 | 0.926 | 0.909 | 27 |

Confusion matrix (qator — haqiqiy, ustun — bashorat):

| | KL0 | KL1 | KL2 | KL3 | KL4 |
|---|---|---|---|---|---|
| **KL0** | 223 | 79 | 21 | 5 | 0 |
| **KL1** | 52 | 75 | 19 | 7 | 0 |
| **KL2** | 19 | 52 | 102 | 39 | 0 |
| **KL3** | 1 | 3 | 14 | 85 | 3 |
| **KL4** | 0 | 0 | 0 | 2 | 25 |

KL0–KL2 o‘zaro xatolar: 242 / 693 (34.9%). Juftliklar: KL0->KL1: 79 (24.1%), KL0->KL2: 21 (6.4%), KL1->KL0: 52 (34.0%), KL1->KL2: 19 (12.4%), KL2->KL0: 19 (9.0%), KL2->KL1: 52 (24.5%)

## 4. EfficientNet-B0 (validation)

Eng yaxshi epoch: 10 / 17, o‘qitish vaqti: 9.0 daq, qurilma: cuda, transfer learning: ha. Grafiklar: `efficientnet_b0/training_curves.png`, `efficientnet_b0/confusion_val.png`

Tasvirlar: 826, bemorlar: 826

| Ko‘rsatkich | Qiymat |
|---|---|
| Accuracy | 0.6090 |
| Balanced Accuracy | 0.6564 |
| Macro Precision | 0.6866 |
| Macro Recall | 0.6564 |
| Macro F1 | 0.6629 |
| Quadratic Weighted Kappa | 0.8029 |

| Sinf | Precision | Recall | F1 | Soni |
|---|---|---|---|---|
| KL0 | 0.780 | 0.659 | 0.714 | 328 |
| KL1 | 0.296 | 0.503 | 0.373 | 153 |
| KL2 | 0.653 | 0.524 | 0.581 | 212 |
| KL3 | 0.815 | 0.708 | 0.758 | 106 |
| KL4 | 0.889 | 0.889 | 0.889 | 27 |

Confusion matrix (qator — haqiqiy, ustun — bashorat):

| | KL0 | KL1 | KL2 | KL3 | KL4 |
|---|---|---|---|---|---|
| **KL0** | 216 | 98 | 13 | 1 | 0 |
| **KL1** | 49 | 77 | 26 | 1 | 0 |
| **KL2** | 12 | 77 | 111 | 12 | 0 |
| **KL3** | 0 | 8 | 20 | 75 | 3 |
| **KL4** | 0 | 0 | 0 | 3 | 24 |

KL0–KL2 o‘zaro xatolar: 275 / 693 (39.7%). Juftliklar: KL0->KL1: 98 (29.9%), KL0->KL2: 13 (4.0%), KL1->KL0: 49 (32.0%), KL1->KL2: 26 (17.0%), KL2->KL0: 12 (5.7%), KL2->KL1: 77 (36.3%)

## 5. Tanlangan model

efficientnet_b0: validation macro_f1 = 0.6629 — eng yuqori. Qoida: validation macro_f1 (teng bo‘lsa: quadratic_weighted_kappa); test to‘plami ishlatilmagan.

## 6. Mustaqil sinov (test) natijalari

Test to‘plami bir marta, faqat `/content/bogimtahlil/experiments/efficientnet_b0/best.pt` uchun ishlatilgan (2026-10-17T09:54:24.367322+00:00).

Tasvirlar: 1656, bemorlar: 1656

| Ko‘rsatkich | Qiymat |
|---|---|
| Accuracy | 0.6473 |
| Balanced Accuracy | 0.6611 |
| Macro Precision | 0.7202 |
| Macro Recall | 0.6611 |
| Macro F1 | 0.6783 |
| Quadratic Weighted Kappa | 0.8257 |

| Sinf | Precision | Recall | F1 | Soni |
|---|---|---|---|---|
| KL0 | 0.783 | 0.732 | 0.757 | 639 |
| KL1 | 0.323 | 0.530 | 0.402 | 296 |
| KL2 | 0.748 | 0.519 | 0.613 | 447 |
| KL3 | 0.798 | 0.798 | 0.798 | 223 |
| KL4 | 0.949 | 0.725 | 0.822 | 51 |

Confusion matrix (qator — haqiqiy, ustun — bashorat):

| | KL0 | KL1 | KL2 | KL3 | KL4 |
|---|---|---|---|---|---|
| **KL0** | 468 | 158 | 13 | 0 | 0 |
| **KL1** | 98 | 157 | 38 | 3 | 0 |
| **KL2** | 32 | 155 | 232 | 28 | 0 |
| **KL3** | 0 | 16 | 27 | 178 | 2 |
| **KL4** | 0 | 0 | 0 | 14 | 37 |

KL0–KL2 o‘zaro xatolar: 494 / 1382 (35.7%). Juftliklar: KL0->KL1: 158 (24.7%), KL0->KL2: 13 (2.0%), KL1->KL0: 98 (33.1%), KL1->KL2: 38 (12.8%), KL2->KL0: 32 (7.2%), KL2->KL1: 155 (34.7%)

## 7. `artifacts/model.pt`

Mavjud. Arxitektura: efficientnet_b0, versiya: efficientnet_b0-kl-1.0.0, SHA-256: `845f5c7b70693dc0573ee02092ec452e30f966e5f9a94db1a257d7be7b301a3c`, sinflar: ['KL0', 'KL1', 'KL2', 'KL3', 'KL4'], kirish: 224×224, mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225].

## 8. Backend integratsiyasi

Backend yuklovchisi tekshiruvidan o‘tdi — server ishga tushganda real tahlil uchun yuklanadi.

CPU tezligi (x86_64, 1 oqim): median 194 ms, P90 203 ms.

## 9. Cheklovlar

- Ehtimolliklar kalibrlanmagan (`calibration_evaluated: false`).
- Model faqat bitta tizzaning frontal (PA) rentgen tasviri uchun o‘qitilgan; proyeksiya avtomatik aniqlanmaydi.
- Natijalar bitta dataset (manba yuqorida) bo‘yicha; boshqa qurilma va populyatsiyalarda tashqi validatsiya qilinmagan.
- Klinik tashxis vositasi emas.
