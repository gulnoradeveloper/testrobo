# data/

Ma’lumotlar katalogi. **Bu yerdagi fayllar git’ga qo‘shilmaydi** (`.gitignore`).

| Yo‘l | Mazmuni |
|---|---|
| `data/raw/` | Ruxsat olingan dataset (masalan, OAI) tasvirlari va `manifest.csv` |
| `data/splits/` | `prepare_dataset.py` natijasi: `manifest_split.csv`, `dataset_report.json` |
| `data/bogimtahlil.db` | Lokal ishga tushirishdagi SQLite bazasi |
| `data/storage/` | Tahlillarning vaqtinchalik fayllari (asl tasvir, Grad-CAM, PDF) — 24 soatdan so‘ng o‘chiriladi |

Osteoarthritis Initiative (OAI) ma’lumotlarini ochiq repozitoriyga joylashtirish **taqiqlanadi**.
Manifest formati: [`docs/MODEL_OQITISH.md`](../docs/MODEL_OQITISH.md).
