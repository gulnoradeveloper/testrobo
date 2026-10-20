# Kompetentlikni baholash modeli

Kod: `backend/app/services/evaluation/rubric.py` (versiyalangan rubrikalar, hisoblash).

## Ikki mustaqil yo'nalish

| | Ko'rsatkich | Qanday hisoblanadi |
|---|---|---|
| **A** | Kasbiy kommunikativ kompetentlik (asosiy) | K1–K6 rubrikasi, 100 ball |
| **B** | Loyihani texnik va mazmuniy taqdim etishga tayyorgarlik (qo'shimcha) | Har javob uchun 0–10, o'rtachasi foizda; A bilan **aralashtirilmaydi** |

## Rubrika v1.0

| Kod | Kompetensiya | Max | Qachon baholanadi |
|---|---|---:|---|
| K1 | Kasbiy fikrni aniq va tushunarli ifodalash | 20 | Har bir javob |
| K2 | Savolni tushunish va mazmunli javob berish | 20 | Har bir javob |
| K3 | Texnik qarorni dalillar bilan asoslash | 20 | Har bir javob |
| K4 | Fikrning mantiqiy izchilligi va tuzilishi | 15 | Har bir javob |
| K5 | Auditoriyaga mos kommunikatsiya | 15 | Har bir javob (rejim = auditoriya) |
| K6 | Refleksiya va feedback asosida takomillashtirish | 10 | Faqat qayta mashqda |
| | **Jami** | **100** | |

Matn asosida baholanmaydi: ovoz, intonatsiya, nutq ravonligi, his-hayajon, shaxsiyat, jamoaviy hamkorlik,
haqiqiy muzokara samaradorligi.

## Hisoblash (backend)

1. AI har bir javob uchun K1–K5: `score`, `assessed`, aynan iqtibos (`evidence`), izoh, tavsiya, cheklov.
2. Iqtibos javobda topilmasa → mezon `assessed=false` (ball olib tashlanadi). Ball `[0, max]` ga cheklanadi.
3. Sessiya bo'yicha mezon balli = baholangan kuzatuvlar o'rtachasi.
4. `total_score` = baholangan mezonlar yig'indisi; `max_applicable_score` = faqat baholangan mezonlar
   maksimumlari yig'indisi; `coverage = max_applicable_score / 100`.
5. **K6 qayta mashqsiz 0 deb hisoblanmaydi** — "Hali baholanmagan" sifatida ko'rsatiladi va maksimumdan
   chiqariladi (masalan: 62 / 90, qamrov 90%).
6. Daraja `total_score / max_applicable_score` foizidan aniqlanadi.

## Darajalar (dastlabki tadqiqot mezonlari)

| Foiz | Daraja |
|---|---|
| 86–100 | Yetuk |
| 71–85 | Mas'uliyatli |
| 56–70 | Shakllanayotgan |
| 0–55 | Intiluvchan |

Chegaralar rubrika konfiguratsiyasida (`RUBRICS["1.0"].levels`). O'zgartirish uchun yangi versiya
(`"1.1"`) qo'shiladi va `RUBRIC_VERSION` o'zgartiriladi — eski natijalar o'z versiyasi bilan saqlanadi
(`answer_evaluations`, `competency_results`, `improvement_plans` da `rubric_version`).

## Adaptiv mexanizm

Eng past foizli 2 ta baholangan mezon (K1–K5) deterministik tanlanadi → har biriga mashq → qayta javob
bir xil rubrika bilan baholanadi → `score_comparison` (oldin/keyin/farq) va K6 saqlanadi.

## Ilmiy cheklov

Ballar va darajalar avtomatik ravishda validatsiyadan o'tgan pedagogik o'lchov **emas**. Tajriba-sinovdan
oldin ekspert bahosi va pilot sinov o'tkazilishi kerak. Empirik validatsiya uchun: `/me/export` yoki DB dan
`answer_evaluations.result_json` (mezon, ball, dalil) eksport qilinib, ekspert baholari bilan
solishtirilishi mumkin (masalan, Cohen's kappa / ICC). Bir xil baholar uchun backend hisoblash deterministik
(test bilan tasdiqlangan).
