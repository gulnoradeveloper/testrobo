# Bosqichlar bo‘yicha hisobot (TT 21 va 24-bo‘limlar)

Sana: 2026-10-15 · Versiya: 1.0

## 1-bosqich. Dastur asosi

- **Bajarilgan ishlar:** `bogimtahlil/` katalog tuzilmasi (frontend, backend, ai, data, experiments, artifacts, reports, tests, docs); FastAPI ilovasi; SQLite + SQLAlchemy + Alembic migratsiyasi; `.env.example` orqali konfiguratsiya; React Router navigatsiyasi (5 bo‘lim).
- **Ishlayotgan imkoniyatlar:** server ishga tushadi, baza avtomatik yaratiladi, `GET /api/v1/health` real holatni qaytaradi.
- **Yaratilgan fayllar:** `backend/app/{main,config,database,models,errors,session,ratelimit}.py`, `backend/alembic/`, `frontend/` (Vite, Tailwind, tsconfig).
- **Tekshiruv natijalari:** migratsiya har bir API testida haqiqiy `alembic upgrade head` orqali bajariladi.
- **Aniqlangan xatoliklar:** yo‘q.
- **Holat:** Tayyor.

## 2-bosqich. Foydalanuvchi interfeysi

- **Bajarilgan ishlar:** Bosh sahifa, Rentgen tahlili, Natijalar, Tahlillar tarixi, Sun’iy intellekt modeli, Dastur haqida, 404 sahifasi. shadcn/ui uslubidagi komponentlar (Button, Card, Badge, Alert, AlertDialog, Slider, Checkbox, Progress). TT ranglari. Mobil menyu, faol bo‘lim ajratilishi.
- **Ishlayotgan imkoniyatlar:** barcha tugmalar serverga bog‘langan; ishlamaydigan tugma yo‘q. Bosh sahifadagi statistik ko‘rsatkichlar faqat `/model/info` dagi real test metrikalaridan olinadi (hozir: “hali baholanmagan”).
- **Tekshiruv natijalari:** `tsc` xatosiz; Vitest — 9 test; Playwright (Chromium) bilan 1440×900 va 390×844 ekranlarda to‘liq ssenariy (yuklash → tahlil → natija → PDF → tarix → o‘chirish) muvaffaqiyatli, gorizontal siljish 0 px, konsol xatolari yo‘q.
- **Aniqlangan xatoliklar:** “Birlashtirilgan tasvir” oynasida xarita noto‘g‘ri masshtablangan edi — tuzatildi.
- **Holat:** Tayyor.

## 3-bosqich. Server qismi

- **Bajarilgan ishlar:** TT dagi 8 ta endpoint + `/image`; fayl validatsiyasi (hajm, MIME, magic bytes, dekodlash, piksel chegarasi); anonim sessiyalar; yagona xatolik formati va TT dagi o‘zbekcha xabarlar; rate limiting; xavfsizlik sarlavhalari; muddati o‘tgan ma’lumotlarni avtomatik tozalash.
- **Tekshiruv natijalari:** 40 dan ortiq backend testi (validatsiya, API integratsiyasi, sessiya izolyatsiyasi, o‘chirish, tozalash, rate limit, shaxsiy ma’lumot saqlanmasligi).
- **Aniqlangan xatoliklar:** yo‘q.
- **Holat:** Tayyor.

## 4-bosqich. Sun’iy intellekt modelini yaratish

- **Bajarilgan ishlar:** `kltool` (preprocess, ResNet-18/EfficientNet-B0, checkpoint formati va moslik tekshiruvi, Grad-CAM, metrikalar, dataset/bemor bo‘yicha ajratish); skriptlar: `prepare_dataset`, `import_folder_dataset`, `train`, `compare_models`, `evaluate`, `export_model`, `benchmark`; YAML konfiguratsiyalar (TT parametrlari).
- **Ishlayotgan imkoniyatlar:** butun zanjir sintetik (rentgen bo‘lmagan) tasvirlarda smoke-test qilingan — barcha artefaktlar (history.csv, grafiklar, eval_test.json, confusion matrix, model.pt, sha256, model_card) yaratiladi.
- **Aniqlangan cheklov:** ishlab chiqish muhitidan OAI ma’lumotlariga va ImageNet vaznlariga kirish imkoni bo‘lmadi; OAI uchun Data Use Agreement talab qilinadi. **ResNet-18 va EfficientNet-B0 real ma’lumotlarda o‘qitilmagan, metrikalar mavjud emas.** Uydirma natijalar yaratilmagan.
- **Keyingi qadam:** `docs/MODEL_OQITISH.md` bo‘yicha OAI ruxsatini olish, manifest tuzish, ikki modelni o‘qitish va taqqoslash.
- **Holat:** Model mavjud emas (kod tayyor).

## 5-bosqich. Sun’iy intellektni dasturga ulash

- **Bajarilgan ishlar:** model server ishga tushganda bir marta yuklanadi; SHA-256, arxitektura, sinflar tartibi, preprocess versiyasi va `training_status` tekshiriladi; real softmax ehtimolliklari; asl koordinatalardagi Grad-CAM; o‘qitilmagan checkpoint standart sozlamada rad etiladi.
- **Tekshiruv natijalari:** API qaytargan ehtimolliklar modelning bevosita chiqishi bilan solishtiriladi (1e-5 aniqlikda); model yo‘q / buzilgan / mos emas / o‘qitilmagan holatlarida tahlil bajarilmasligi tekshirilgan; model so‘rovlarda qayta yuklanmasligi tekshirilgan.
- **Aniqlangan xatoliklar:** o‘qitilmagan EfficientNet-B0 da Grad-CAM xaritasi butunlay bo‘sh chiqishi aniqlandi (tasodifiy vaznlarda aktivatsiyalar ~1e-14) — endi bunday holat “Faollik xaritasi bo‘sh” deb ochiq ko‘rsatiladi.
- **Holat:** Qisman tayyor — integratsiya ishlaydi, o‘qitilgan model kutilmoqda.

## 6-bosqich. Hisobot va tarix

- **Bajarilgan ishlar:** A4 PDF (Open Sans — o‘zbekcha harflar to‘g‘ri), TT 15-bo‘limidagi barcha bandlar va har bir sahifa pastidagi ogohlantirish; sessiya tarixi (KL va sana bo‘yicha filtr, saralash); tasdiqlash oynasi bilan o‘chirish.
- **Tekshiruv natijalari:** PDF matni pypdf bilan tekshiriladi; o‘chirishdan so‘ng fayllar va yozuvlar yo‘qligi tekshiriladi.
- **Holat:** Tayyor.

## 7-bosqich. Yakuniy sinov

- **Tekshiruv natijalari:** pytest — 64/64; Vitest — 9/9; Playwright E2E — desktop va mobil; CPU benchmark — median 117 ms (ResNet-18) / 140 ms (EfficientNet-B0), API orqali to‘liq tahlil ≈ 0,5–1,3 s (`experiments/benchmark.md`).
- **Bajarilmagan / tekshirilmagan:** Docker obrazlari yig‘ilmagan (muhitda Docker daemon yo‘q; `docker compose config` muvaffaqiyatli). Edge va Firefox brauzerlarida qo‘lda sinov o‘tkazilmagan (faqat Chromium). Real rentgen tasvirlari bilan sinov — o‘qitilgan model bo‘lmagani sababli o‘tkazilmagan.
- **Loyiha holati:** **Qisman tayyor / Model mavjud emas.** TT 23-bo‘limidagi 6, 7, 15-mezonlar o‘qitilgan model talab qiladi va hozircha bajarilmagan.

---

## 8-bosqich. Modelni o‘qitish va integratsiya qilish (2-ish topshirig‘i)

- **Bajarilgan ishlar:**
  - `kltool/oai.py` + `configs/oai_columns.yaml` + `build_oai_manifest.py` — OAI `kXR_SQ_BU##` yorliqlarini tasvir indeksi bilan (bemor, tomon, tashrif) kaliti bo‘yicha 1:1 bog‘lash; ziddiyatli qayta o‘qishlar, yetishmayotgan kodlar, frontal bo‘lmagan va takroriy tasvirlarni chiqarish va sanash.
  - Manifest sxemasi TT ustunlariga o‘tkazildi: `image_path, patient_id, knee_side, visit_id, projection, kl_grade, dataset_source, split` (eski nomlar avtomatik moslashtiriladi).
  - `prepare_dataset.py` — har bir guruhda tasvir/bemor/KL0–KL4 soni; `train.py` — transfer learning (vaznlar bo‘lmasa to‘xtaydi), `artifacts/<arch>_best.pt`; `evaluate.py` — test qulfi; `compare_models.py` — adolatli taqqoslash sharti; `export_model.py` — to‘liq metadata va backend yuklovchisi bilan qayta tekshirish; `run_experiment.py` — butun jarayon; `make_report.py` — faqat fayllardan hisobot.
- **Tekshiruv natijalari:** pytest — 82 o‘tdi, 4 o‘tkazib yuborildi (real dataset/model talab qiladi). OAI formatidagi sintetik ma’lumotda `run_experiment.py` 8 bosqichi to‘liq bajarildi (2 daq 37 s, CPU); eksport qilingan model backendga standart (qat’iy) rejimda yuklandi va `test_real_model.py` o‘tdi. Sintetik natijalar repozitoriyga qo‘shilmagan.
- **Bajarilmagan:** real OAI ma’lumotlari yo‘q (kirish ruxsati va tarmoq cheklovi), ImageNet vaznlari yuklab olinmadi. Shuning uchun ResNet-18 va EfficientNet-B0 o‘qitilmagan, metrikalar yo‘q, `artifacts/model.pt` yo‘q. `oai_columns.yaml` dagi ustun nomlari OAI data dictionary bilan solishtirilmagan (`verified: false`).
- **Loyiha holati:** **Model mavjud emas** — o‘qitish uchun barcha kod tayyor va tekshirilgan.
