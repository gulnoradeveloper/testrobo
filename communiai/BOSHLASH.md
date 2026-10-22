# CommuniAI — ishga tushirish bo'yicha qo'llanma

Ilova ikki qismdan iborat:

1. **Server (backend)** — kompyuteringizda ishlaydi, ma'lumotlarni saqlaydi va AI bilan ishlaydi.
2. **Mobil ilova (APK)** — telefonga o'rnatiladi va serverga ulanadi.

> Ilova serversiz ishlamaydi: avval serverni yoqing, keyin telefonda ilovani oching.

---

## 1-qadam. Serverni kompyuterda ishga tushirish

### Windows

1. Python o'rnating: https://www.python.org/downloads/ (3.11 yoki yangi).
   O'rnatishda **"Add python.exe to PATH"** belgisini albatta qo'ying.
2. ZIP ni oching va `communiai` papkasidagi **`start-backend.bat`** faylini ikki marta bosing.
3. Birinchi marta kutubxonalar o'rnatiladi (2–5 daqiqa, internet kerak).
4. Oynada quyidagiga o'xshash yozuv chiqadi:
   ```
   CommuniAI backend ishga tushdi
     Telefon ilovasida 'Server manzili':  http://192.168.1.15:8000
   ```
   Shu manzilni yozib oling. **Oynani yopmang** — oyna yopilsa server to'xtaydi.
5. Windows "Brandmauer / Firewall" ruxsat so'rasa — **"Ruxsat berish" (Allow access)** ni bosing
   (xususiy tarmoq uchun).

### Linux / macOS

```bash
cd communiai
./start-backend.sh
```

### AI ni yoqish (API kalit)

AI ekspertiza va himoya uchun **Anthropic (Claude) API kaliti** kerak. Kalit telefonga emas, faqat
**kompyuterdagi serverga** qo'yiladi (xavfsizlik uchun ilova ichida kalit saqlanmaydi).

1. https://console.anthropic.com saytida ro'yxatdan o'ting → **Billing** bo'limida balans qo'shing
   (kalit balanssiz ishlamaydi) → **API Keys → Create Key**. Kalit `sk-ant-...` bilan boshlanadi.
2. **Eng oson yo'l:** `start-backend.bat` ni ishga tushiring — kalit hali kiritilmagan bo'lsa, oyna uni
   so'raydi: `API kalit:` deb chiqqanda kalitni joylang (sichqonchaning o'ng tugmasi → Paste) va Enter bosing.
   Kalit avtomatik `backend/.env` fayliga saqlanadi va darhol tekshiriladi:
   - `AI kaliti: OK` — hammasi tayyor;
   - `KALIT NOTO'G'RI` — kalitni qayta nusxalang;
   - `KALITGA RUXSAT YO'Q` — console.anthropic.com da balans/hisobni tekshiring.
3. **Qo'lda:** `backend/.env` faylini Bloknot bilan oching va `AI_API_KEY=` qatoriga yozing:
   ```
   AI_API_KEY=sk-ant-sizning-kalitingiz
   ```
   Saqlang, server oynasini yoping va `start-backend.bat` ni qayta ishga tushiring.

Kalitni almashtirish uchun `backend/.env` dagi `AI_API_KEY=` qatorini o'zgartiring va serverni qayta
ishga tushiring. Kalitni hech kimga bermang va internetga joylamang.

Kalit bo'lmasa ilova ishlaydi (ro'yxatdan o'tish, loyihalar, fayllar), lekin AI ekspertiza va himoya
"AI xizmati serverda sozlanmagan" deb javob beradi — soxta natija ko'rsatilmaydi.

---

## 2-qadam. Telefonga ilovani o'rnatish

1. Telefon va kompyuter **bitta Wi-Fi** tarmog'ida bo'lishi kerak.
2. `apk/CommuniAI-1.0.0-dev-http.apk` faylini telefonga ko'chiring (Telegram "Saqlangan xabarlar",
   USB kabel yoki Google Drive orqali).
3. Faylni oching → **"Noma'lum manbalardan o'rnatish"** ga ruxsat bering → **O'rnatish**.
   Agar **Play Protect** ogohlantirsa: **"Batafsil" → "Baribir o'rnatish"** ni bosing
   (ilova Play Market'dan emas, shuning uchun bu ogohlantirish odatiy).
4. Agar avval CommuniAI ning eski versiyasi o'rnatilgan bo'lsa — **avval uni o'chiring**, keyin yangisini o'rnating
   (eski versiyalar boshqa kalit bilan imzolangan edi; bundan keyingi versiyalar ustiga o'rnatiladi).

> `CommuniAI-1.0.0-release.apk` faqat **HTTPS** (domenli) server uchun. Uyda/kompyuterda sinash uchun
> **dev-http** versiyasini ishlating.

---

## 3-qadam. Ilovani serverga ulash

1. Ilovani oching → tanishtiruv ekranlaridan o'ting.
2. Kirish ekranining pastidagi **"Server manzili"** tugmasini bosing.
3. 1-qadamda yozib olgan manzilni kiriting, masalan `http://192.168.1.15:8000`.
4. **"Ulanishni tekshirish"** tugmasini bosing: yashil belgi chiqsa — aloqa bor (AI ulangan-ulanmaganini ham
   ko'rsatadi); qizil bo'lsa — sababi va nima qilish kerakligi yoziladi. So'ng **Saqlash**.
5. **"Ro'yxatdan o'tish"** — hisob yarating va ishlashni boshlang.

Ulanishni tekshirish: telefon brauzerida `http://192.168.1.15:8000/health/ready` manzilini oching.
`"status":"ready"` chiqsa — ulanish to'g'ri.

---

## Muammolar va yechimlar

| Belgisi | Yechim |
|---|---|
| "Serverga ulanib bo'lmadi" | Server oynasi ochiqmi? Telefon va kompyuter bitta Wi-Fi'dami? Manzil to'g'rimi (`http://` bilan, oxirida `:8000`)? Firewall 8000-portga ruxsat berganmi? |
| Telefon brauzerida ham ochilmaydi | Windows: Boshqaruv paneli → Windows Defender Firewall → "Ilovaga ruxsat berish" → Python ni "Xususiy" tarmoq uchun belgilang. Ba'zi umumiy Wi-Fi (kafe, universitet) qurilmalar orasidagi ulanishni bloklaydi — telefonning "Hotspot"ini yoqib, kompyuterni unga ulang. |
| "AI xizmati serverda sozlanmagan" | `backend/.env` ga `AI_API_KEY` yozing va serverni qayta ishga tushiring. |
| Ilova o'rnatilmaydi | Eski versiyani o'chiring; telefonda kamida 200 MB bo'sh joy bo'lsin; Android 7.0 yoki yangi. |
| `start-backend.bat` darrov yopiladi | Python o'rnatilmagan yoki PATH ga qo'shilmagan. `cmd` da `python --version` ni tekshiring. |

## Brauzer versiyasi (ixtiyoriy)

Server ishlab turganda ilovani kompyuter brauzerida ham sinash mumkin: `mobile/web` dan yig'ilgan versiya
uchun `flutter run -d chrome` (Flutter SDK kerak).

## Production (internetga chiqarish)

Doimiy server uchun Docker + PostgreSQL + HTTPS: `README.md` → "Backend (Docker bilan)" va
`docs/SECURITY.md` ni ko'ring. Bunda telefonlarga **release** APK o'rnatiladi.
