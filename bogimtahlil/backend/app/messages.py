"""Foydalanuvchiga ko‘rinadigan o‘zbekcha matnlar va KL ma’lumotnomasi.

KL tavsiflari Kellgren J.H., Lawrence J.S. "Radiological assessment of osteo-arthrosis",
Ann Rheum Dis. 1957;16(4):494–502 dagi daraja ta’riflari asosida berilgan. Ular darajaning
UMUMIY ta’rifi bo‘lib, model aynan shu tasvirda ushbu belgilarni aniqlaganini bildirmaydi.
"""
from __future__ import annotations

ERRORS: dict[str, str] = {
    "NO_FILE": "Fayl tanlanmagan.",
    "UNSUPPORTED_FORMAT": "Fayl formati qo‘llab-quvvatlanmaydi.",
    "FILE_TOO_LARGE": "Fayl hajmi belgilangan chegaradan oshgan.",
    "IMAGE_UNREADABLE": "Tasvirni o‘qib bo‘lmadi.",
    "IMAGE_DIMENSIONS": "Tasvir o‘lchamlari ruxsat etilgan chegaradan tashqarida.",
    "PROJECTION_NOT_CONFIRMED": "Tasvir bitta tizzaning frontal rentgen proyeksiyasi ekanini tasdiqlang.",
    "MODEL_NOT_READY": "Sun’iy intellekt modeli hali tayyor emas.",
    "ANALYSIS_FAILED": "Tahlilni bajarishda xatolik yuz berdi.",
    "GRADCAM_FAILED": "Faollik xaritasini yaratishda xatolik yuz berdi.",
    "REPORT_FAILED": "Hisobotni yaratishda xatolik yuz berdi.",
    "NOT_FOUND": "Tahlil natijasi topilmadi.",
    "FORBIDDEN": "Ushbu ma’lumotni ko‘rishga ruxsat yo‘q.",
    "RATE_LIMITED": "So‘rovlar soni juda ko‘p. Birozdan so‘ng qayta urinib ko‘ring.",
    "VALIDATION_ERROR": "So‘rov ma’lumotlari noto‘g‘ri.",
    "ROUTE_NOT_FOUND": "So‘ralgan manzil mavjud emas.",
    "INTERNAL_ERROR": "Serverda kutilmagan xatolik yuz berdi.",
}

KL_REFERENCE = {
    0: {
        "title": "Aniq rentgenologik belgilar yo‘q",
        "description": "Kellgren–Lawrence tasnifiga ko‘ra 0-daraja: osteoartritga xos rentgenologik belgilar (osteofitlar, "
        "bo‘g‘im yorig‘ining torayishi) aniqlanmaydi.",
    },
    1: {
        "title": "Shubhali o‘zgarishlar",
        "description": "1-daraja: bo‘g‘im yorig‘ining shubhali torayishi va osteofit lablanishi ehtimoli. "
        "Bu daraja rentgenologik jihatdan noaniq bo‘lib, mutaxassislar o‘rtasida ham farqli baholanishi mumkin.",
    },
    2: {
        "title": "Yengil o‘zgarishlar",
        "description": "2-daraja: aniq osteofitlar mavjudligi va bo‘g‘im yorig‘ining torayishi ehtimoli. "
        "Ko‘pchilik tadqiqotlarda KL ≥ 2 rentgenologik osteoartrit mezoni sifatida qabul qilinadi.",
    },
    3: {
        "title": "O‘rtacha o‘zgarishlar",
        "description": "3-daraja: bir nechta o‘rtacha osteofitlar, bo‘g‘im yorig‘ining aniq torayishi, ma’lum darajada "
        "subxondral skleroz va suyak uchlari shakli o‘zgarishi ehtimoli.",
    },
    4: {
        "title": "Og‘ir o‘zgarishlar",
        "description": "4-daraja: yirik osteofitlar, bo‘g‘im yorig‘ining keskin torayishi, kuchli subxondral skleroz va "
        "suyak uchlarining aniq deformatsiyasi.",
    },
}
KL_SOURCE = "Kellgren J.H., Lawrence J.S. Ann Rheum Dis. 1957;16(4):494–502."

DISCLAIMER = (
    "Ushbu natija sun’iy intellekt algoritmining ilmiy-tadqiqot natijasidir. U shifokor tashxisi o‘rnini bosmaydi "
    "va davolashni belgilash uchun asos bo‘lmaydi."
)
PROBABILITY_NOTE = (
    "Ko‘rsatilgan qiymatlar modelning softmax chiqishi bo‘lib, tashxisning ishonchliligi emas. "
    "Ehtimolliklarning klinik kalibrlanganligi alohida baholanmagan."
)
GRADCAM_NOTE = (
    "Rangli xarita neyron tarmoq qaror qabul qilishda e’tibor qaratgan sohalarni ko‘rsatadigan vizual izohdir. "
    "U anatomik patologiya joyini tasdiqlamaydi va rentgenolog annotatsiyasi o‘rnini bosmaydi."
)
LIMITATIONS = [
    "Model faqat bitta tizza bo‘g‘imining standart frontal (to‘g‘ri) rentgen proyeksiyasi uchun mo‘ljallangan; "
    "dastur proyeksiya va anatomik sohani avtomatik aniqlamaydi.",
    "Tasvir sifati, kontrast, joylashuv va qurilma farqlari natijaga ta’sir qiladi.",
    "KL darajasi rentgenologik tasnif bo‘lib, klinik tashxisga teng emas.",
    "Erta darajalar (KL0, KL1, KL2) o‘rtasida chalkashish ehtimoli yuqori.",
    "Klinik amaliyotda foydalanish uchun mustaqil klinik sinov va tegishli ruxsatlar talab etiladi.",
]
SPECIALIST_ADVICE = "Bo‘g‘imdagi og‘riq yoki harakat cheklanishi bo‘lsa, ortoped yoki revmatolog mutaxassisiga murojaat qiling."
