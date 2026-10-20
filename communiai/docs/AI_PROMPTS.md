# AI promptlari va AI qatlami

Kod: `backend/app/services/ai/` — `provider.py` (interfeys, retry, monitoring), `anthropic_provider.py`,
`prompts.py` (barcha promptlar, `PROMPT_VERSION = 1.0`), `schemas.py` (natija sxemalari), `services.py`.

## Provayderdan mustaqillik

Servislar faqat `AIProvider.generate(system, user_content, schema, max_tokens)` ga bog'liq.
`AI_PROVIDER` konfiguratsiyasi bo'yicha adapter tanlanadi. Hozir `anthropic` (rasmiy SDK, structured outputs
`messages.parse`, server-side refusal fallback) amalga oshirilgan. Yangi provayder qo'shish uchun shu
interfeysni bajaruvchi klass yozib, `get_provider()` ga ulash kifoya. Kalit bo'lmasa `DisabledProvider`
ishlaydi: har bir chaqiruv `AI_NOT_CONFIGURED` xatosini beradi — **soxta natija yo'q**.

## Vazifaviy promptlar (TZ 13)

| Servis | Sxema | Vazifa |
|---|---|---|
| Project Analysis | `ProjectAnalysisOut` | Xulosa, kuchli jihatlar (har biriga loyihadan aynan iqtibos), kamchiliklar (muammo/joy/ahamiyat/yechim), 3 guruh tavsiyalar, ≥5 ekspert savoli, himoya maslahatlari, 10 yo'nalish holati, 8 toifali loyiha tavsiyalari |
| Expert Question | `QuestionOut` | Bitta savol; rejim, loyiha, oldingi javoblar va baholovchining `needs_follow_up` belgisi asosida; takroriy savol rad etiladi |
| Communication Evaluation | `AnswerEvaluationOut` | K1–K5 bo'yicha ball + javobdan aynan iqtibos (dalil), texnik izoh alohida, qisqa 6 qismli feedback, tayyorgarlik (0–10) alohida |
| Improvement Coach | `FinalCoachOut` | Eng zaif 2 kompetensiya uchun mashqlar (backend tanlaydi), batafsil tahlil, loyiha tavsiyalari |
| Practice Evaluation | `PracticeEvaluationOut` | Qayta javob uchun K1–K5, K6 refleksiya (0–10), oldin/keyin solishtiruv |

System instruction matnlari TZ dagi inglizcha matnlar bilan boshlanadi va qo'shimcha qoidalar bilan
to'ldirilgan (`prompts.py`). Barcha odam o'qiydigan matnlar o'zbek (lotin) tilida qaytariladi.

## Prompt xavfsizligi (TZ 13.5)

1. Hujjatlar, loyiha maydonlari va javoblar `<untrusted_data source="...">` ichida beriladi; system
   promptda bu ma'lumotlar ichidagi buyruqlar bajarilmasligi aniq aytilgan.
2. Ma'lumot ichidagi `<untrusted_data>`/`</untrusted_data>` teglari `[tag removed]` bilan almashtiriladi —
   matn o'z "qobig'idan" chiqib keta olmaydi. Boshqaruv belgilari tozalanadi, hajm cheklanadi.
3. AI javobi Pydantic sxema bilan tekshiriladi; tuzilma xatosida cheklangan qayta urinish (default 3).
4. **Dalil tekshiruvi:** ball qo'yilgan har bir mezon iqtibosi talaba javobida topilishi shart, aks holda
   mezon "baholanmagan" bo'ladi. Ekspertizadagi kuchli jihat iqtibosi loyiha matnida topilmasa, olib tashlanadi.
5. Ballar mezon maksimumi bilan cheklanadi; umumiy ball, qamrov va daraja faqat backendda hisoblanadi.
6. Model rad etsa (`refusal`), vaqt tugasa yoki provayder xatosi bo'lsa — foydalanuvchiga tushunarli xabar,
   sessiya saqlanadi va qayta urinish mumkin.
7. Monitoring jadvali (`ai_request_logs`) prompt va javob matnini saqlamaydi; API kalit loglarga yozilmaydi.
8. Foydalanuvchi ma'lumotlari model o'qitish uchun ishlatilmaydi; AI ga yuborishdan oldin rozilik so'raladi.

## Model sozlamalari

`AI_MODEL=claude-opus-5-5`, `AI_EFFORT=medium` (tezlik/sifat muvozanati; murakkabroq tahlil uchun `high`),
`AI_TIMEOUT_SECONDS=120`. Administrator panelidan modelni almashtirish yoki AI ni vaqtincha o'chirish mumkin.
