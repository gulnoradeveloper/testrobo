# Inference tezligi o‘lchovi

**Sana:** 2026-10-15 · **Skript:** `ai/scripts/benchmark.py` · **Takrorlar:** 20 (birinchi isinish o‘lchovi hisobga olinmagan)

**Muhit:** Intel Xeon @ 2.10 GHz, 4 ta vCPU, GPU yo‘q, PyTorch 2.14 (CPU), 4 ta oqim.
**Kirish tasviri:** 1024 × 1280 piksel, grayscale PNG.
**O‘lchangan zanjir:** dekodlash → preprocess (letterbox 224×224, normallashtirish) → forward → softmax → Grad-CAM.

| Arxitektura | Median | P90 |
|---|---|---|
| ResNet-18 | 117 ms | 134 ms |
| EfficientNet-B0 | 140 ms | 176 ms |

**Muhim:** o‘lchov o‘qitilmagan (tasodifiy vaznli) checkpointlarda bajarilgan. Hisoblash vaqti vaznlarning
qiymatiga bog‘liq emas (arxitektura bir xil), shuning uchun tezlik bahosi o‘qitilgan model uchun ham amal qiladi;
**aniqlik haqida esa bu o‘lchov hech narsa demaydi.**

API orqali to‘liq tahlil (fayl tekshiruvi, natija PNG fayllarini saqlash va bazaga yozish bilan) shu kompyuterda
1024×1280 tasvir uchun taxminan 0,5–1,3 s ni tashkil etdi. TT maqsadi — CPUda median ≤ 10 s — bajarilgan.

Qayta o‘lchash:

```bash
python ai/scripts/benchmark.py --checkpoint artifacts/model.pt --image <tizza.png> --runs 20
```
