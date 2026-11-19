/*
 * BEGOYIM — vazirlik uchun ma'ruza matni (DOCX).
 *   NODE_PATH=<node_modules> node build_speech.js out/BEGOYIM_maruza_matni.docx
 */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, AlignmentType, BorderStyle, Footer, PageNumber,
  Table, TableRow, TableCell, WidthType, ShadingType, LevelFormat,
} = require("docx");

const OUT = process.argv[2] || "out/BEGOYIM_maruza_matni.docx";
const AUTHOR = "Bo‘ronova Gulnora Yodgorovna";
const FONT = "Times New Roman";
const CRIMSON = "A3123F", GOLD = "B8862E", GREY = "7A6A70";

const p = (text, opts = {}) => new Paragraph({
  spacing: { after: 140, line: 300 }, alignment: AlignmentType.JUSTIFIED, ...opts.para,
  children: (Array.isArray(text) ? text : [text]).map((t) => (typeof t === "string" ? new TextRun({ text: t, font: FONT, size: 28, ...opts.run }) : t)),
});
const b = (text) => new TextRun({ text, font: FONT, size: 28, bold: true });
const cue = (text) => new Paragraph({
  spacing: { before: 220, after: 80 }, keepNext: true,
  children: [new TextRun({ text: `▸ ${text}`, font: FONT, size: 22, italics: true, bold: true, color: GOLD })],
});
const h = (text, level = 1) => new Paragraph({
  heading: level === 1 ? "Heading1" : "Heading2", keepNext: true,
  spacing: { before: level === 1 ? 360 : 240, after: 160 },
  children: [new TextRun({ text, font: FONT, size: level === 1 ? 32 : 28, bold: true, color: CRIMSON })],
});
const rule = () => new Paragraph({ spacing: { after: 200 }, border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: GOLD, space: 1 } }, children: [] });
const bullet = (text) => new Paragraph({ numbering: { reference: "dots", level: 0 }, spacing: { after: 80, line: 290 }, children: [new TextRun({ text, font: FONT, size: 26 })] });

const children = [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 }, children: [new TextRun({ text: "BEGOYIM", font: FONT, size: 44, bold: true, color: CRIMSON })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 }, children: [new TextRun({ text: "Ayollar bandligi va farovonligi milliy raqamli ekotizimi", font: FONT, size: 30, bold: true })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 }, children: [new TextRun({ text: "Vazirlikdagi taqdimot uchun ma’ruza matni", font: FONT, size: 26, italics: true, color: GREY })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 }, children: [new TextRun({ text: `Ma’ruzachi: ${AUTHOR} · Taxminiy davomiylik: 5–6 daqiqa`, font: FONT, size: 24, color: GREY })] }),
  rule(),
  p([new TextRun({ text: "Qanday foydalanish: ", font: FONT, size: 24, bold: true, color: GOLD }), new TextRun({ text: "oltin rangli “▸ N-slayd” belgisi shu qismni o‘qishdan oldin qaysi slaydni ochish kerakligini ko‘rsatadi. 2-slayddagi video (3 daqiqa) ixtiyoriy — vaqt bo‘lsa, ma’ruzadan oldin yoki keyin ko‘rsating.", font: FONT, size: 24, color: GREY })]),

  h("Ma’ruza"),
  cue("1-slayd · Titul"),
  p("Assalomu alaykum, hurmatli vazirlik rahbariyati, hurmatli mutasaddilar va yig‘ilish ishtirokchilari!"),
  p("Bugun e’tiboringizga ayollarning iqtisodiy mustaqilligini mustahkamlash, ularning bandligini ta’minlash va ijtimoiy farovonligini oshirishga qaratilgan BEGOYIM innovatsion raqamli platformasi loyihasini taqdim etmoqchiman."),

  cue("4-slayd · Asosiy savol"),
  p("Bugungi kunda mamlakatimizda xotin-qizlarni qo‘llab-quvvatlash, ularning bandligini ta’minlash va tadbirkorlik faoliyatini rivojlantirishga katta e’tibor qaratilmoqda."),
  p("Shunga qaramay, jamiyatimizda o‘z hunari, bilimi va kasbiy salohiyatiga ega bo‘lgan, ammo uni barqaror daromad manbaiga aylantirishda qiyinchiliklarga duch kelayotgan ayollar mavjud."),
  p(["Biz o‘z oldimizga muhim savol qo‘ydik: ", b("ayolning hunari bor, ishlash istagi bor, lekin mijozi bo‘lmasa, uning iqtisodiy mustaqilligini qanday ta’minlaymiz?")]),
  p("Ana shu savolga amaliy yechim sifatida BEGOYIM loyihasi ishlab chiqilmoqda."),

  cue("7-slayd · Uchta ustuvor yo‘nalish"),
  p(["BEGOYIM — oddiy xizmatlar e’lonlari platformasi emas. Bu ayolning mavjud salohiyatini aniqlashdan boshlab, uni real daromadga yo‘naltirishgacha bo‘lgan jarayonni raqamlashtirishga qaratilgan ", b("yaxlit ekotizimdir"), ". U uchta ustuvor yo‘nalishga tayanadi: iqtisodiy mustaqillik, ijtimoiy himoya va shaxsiy rivojlanish."]),

  cue("8-slayd · Raqamli ko‘prik"),
  p("Platforma orqali tikuvchilik, pazandachilik, hunarmandchilik, repetitorlik, maishiy va masofaviy xizmatlar bilan shug‘ullanuvchi ayollar o‘z xizmatlarini taklif etishlari, mijozlar bilan bog‘lanishlari va buyurtmalar olishlari mumkin bo‘ladi."),

  cue("13-slayd · Sun’iy intellekt"),
  p("Sun’iy intellekt texnologiyalari esa ayolning ko‘nikmasi, hududi va xizmat turiga qarab mos buyurtmalarni tavsiya etishga yordam beradi."),

  cue("11-slayd · Mahalla hamkorligi"),
  p(["Loyihaning muhim ustunligi — ", b("mahalla tizimi bilan hamkorlikdir"), "."]),
  p("Mahalladagi xotin-qizlar faoli ayollarning mavjud ko‘nikmalarini aniqlash, ularni platformaga jalb qilish va tegishli tartibda tasdiqlash jarayonlarida ishtirok etishi mumkin."),

  cue("15-slayd · O‘lchanadigan natija"),
  p("Tuman va shahar Oila va xotin-qizlar bo‘limlari esa maxsus raqamli boshqaruv paneli orqali hududlarda qancha ayol xizmat ko‘rsatayotgani, qancha buyurtma bajarilgani va nechta ayol daromad topishni boshlaganini kuzatish imkoniyatiga ega bo‘ladi."),
  p("Bu esa bandlikni faqat ro‘yxatdagi ko‘rsatkichlar bilan emas, balki real iqtisodiy natijalar asosida baholash imkonini yaratadi."),

  cue("16–17-slaydlar · BEGOYIM HIMOYA"),
  p("Hurmatli yig‘ilish ishtirokchilari!", { para: { keepNext: true } }),
  p(["Biz loyihani yanada rivojlantirib, unga ayollar xavfsizligi va ijtimoiy himoyasiga qaratilgan ", b("BEGOYIM HIMOYA"), " modulini kiritishni ham taklif etmoqdamiz."]),
  p("Ushbu modul orqali ayollar tazyiq, zo‘ravonlik, kamsitish, shilqimlik va boshqa muammoli holatlar yuzasidan mahalla hamda vakolatli tashkilotlarga xavfsiz murojaat qilishlari mumkin bo‘ladi."),
  p("Murojaatlar tegishli mas’ullarga yo‘naltiriladi, ko‘rib chiqilish jarayoni kuzatiladi va murojaatchiga belgilangan tartibda javob qaytariladi. Murojaatchining xavfsizligi, roziligi va ma’lumotlari maxfiyligi ustuvor bo‘ladi."),

  cue("18-slayd · Strategik modullar"),
  p("Shuningdek, platformada psixologik maslahat, kasbiy rivojlanish va tadbirkorlik ko‘nikmalarini shakllantirish imkoniyatlarini ham bosqichma-bosqich joriy etish ko‘zda tutilmoqda."),
  p(["Bizning asosiy maqsadimiz — ayolni faqat ish bilan ta’minlash emas, balki uning ", b("iqtisodiy mustaqilligi, huquqiy himoyasi va ijtimoiy farovonligiga kompleks yondashishdir"), "."]),

  cue("20–21-slaydlar · Respublika pilot dasturi"),
  p("BEGOYIMni dastlab tanlangan mahallalarda sinovdan o‘tkazish, natijalarni ilmiy-amaliy jihatdan baholash va keyinchalik respublika hududlariga bosqichma-bosqich kengaytirishni taklif etamiz."),
  p("Buning uchun vazirlik va tegishli tashkilotlar bilan hamkorlikda pilot hududlarni belgilash, mahalla xotin-qizlar faollarini jalb qilish hamda platformani mavjud bandlik va ijtimoiy qo‘llab-quvvatlash mexanizmlari bilan uyg‘unlashtirish muhim ahamiyatga ega."),

  cue("23-slayd · Murojaat va taklif"),
  p("Hurmatli rahbarlar!", { para: { keepNext: true } }),
  p("Biz yangi tashkilot yoki murakkab boshqaruv tizimini yaratishni emas, balki mavjud mahalla va xotin-qizlarni qo‘llab-quvvatlash tizimining samaradorligini zamonaviy raqamli texnologiyalar yordamida oshirishni taklif qilmoqdamiz."),
  p(["BEGOYIM loyihasini respublika miqyosida rivojlantirish uchun uni dastlab ", b("Buxoro, Samarqand va Toshkent"), " hududlaridagi tanlangan mahallalarda pilot tariqasida joriy etishni taklif qilamiz."]),
  p("Buning uchun Oila va xotin-qizlar bo‘limlari bilan hamkorlik mexanizmini yo‘lga qo‘yish, mahallalardagi xotin-qizlar faollarini jalb etish hamda platformaning amaliy samaradorligini birgalikda baholashda tashkiliy ko‘mak so‘raymiz."),

  cue("24-slayd · Final"),
  p("Ishonamizki, BEGOYIM kelajakda mamlakatimizdagi minglab ayollarning o‘z hunari va salohiyati orqali iqtisodiy mustaqillikka erishishiga xizmat qiladigan milliy platformaga aylanishi mumkin."),
  p([b("BEGOYIM — har bir ayolga imkoniyat, har bir oilaga farovonlik sari qadam!")], { para: { alignment: AlignmentType.CENTER } }),

  cue("25-slayd · Muallif"),
  p([b("E’tiboringiz uchun rahmat!")], { para: { alignment: AlignmentType.CENTER } }),
];

// --- Ilova: pilot raqamlari ---
children.push(h("Ilova 1. Pilot dasturi bo‘yicha asosiy raqamlar"));
const W = [2400, 6626];
const row = (a, c, head = false) => new TableRow({
  children: [a, c].map((t, i) => new TableCell({
    width: { size: W[i], type: WidthType.DXA },
    shading: head ? { type: ShadingType.CLEAR, color: "auto", fill: "F6E7C8" } : undefined,
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({ children: [new TextRun({ text: t, font: FONT, size: 24, bold: head || i === 0, color: i === 0 && !head ? CRIMSON : undefined })] })],
  })),
});
children.push(new Table({
  width: { size: 9026, type: WidthType.DXA }, columnWidths: W,
  rows: [
    row("Ko‘rsatkich", "Taklif etilayotgan maqsad (6 oylik pilot)", true),
    row("3 ta hudud", "Buxoro, Samarqand, Toshkent"),
    row("15 ta", "Tanlab olinadigan mahalla"),
    row("1 500 nafar", "Platformaga jalb etish maqsad qilingan ayol"),
    row("300 nafar", "Kamida bitta yakunlangan buyurtma olishi rejalashtirilgan ayol"),
    row("1–2-oy", "Tayyorlash va jalb etish: mahallalar, faollarni o‘qitish, ro‘yxatga olish, katalog"),
    row("3–4-oy", "Buyurtmalar va bandlik: mijozlar va korxonalar bilan bog‘lash, dastlabki buyurtmalar"),
    row("5–6-oy", "Baholash va kengaytirish: buyurtma, daromad, faollik, qoniqish tahlili; keyingi hududlar"),
  ],
}));
children.push(p("Raqamlar loyiha maqsadlari bo‘lib, tasdiqlangan natijalar emas. Ular hamkorlar va resurslar asosida kelishiladi. BEGOYIM HIMOYA moduli alohida xavfsizlik auditi, vakolatli tashkilotlar bilan kelishuv va ma’lumotlarni himoya qilish tartibi ishlab chiqilgandan keyin pilotga chiqariladi.", { run: { size: 22, italics: true, color: GREY }, para: { spacing: { before: 120, after: 140 } } }));

// --- Ilova: savollarga javoblar ---
children.push(h("Ilova 2. Ehtimoliy savollarga qisqa javoblar"));
[
  ["BEGOYIMning mavjud bandlik tizimlaridan farqi nimada?", "BEGOYIM e’lonlar ro‘yxati emas, balki to‘liq jarayon: mahalla tasdig‘i, sun’iy intellekt orqali mijoz bilan moslashtirish, buyurtmadan baho va daromad hisobigacha. Oila va xotin-qizlar bo‘limlari esa real natijalarni dashboard orqali kuzatadi."],
  ["Platformada ayollar uchun buyurtmalar qayerdan keladi?", "Mahalla va hudud aholisi, mahalliy tadbirkorlar hamda BEGOYIM Hamkor moduli orqali tashkilotlar — maktablar, bog‘chalar, korxonalar, mehmonxonalar. Maqsad — yakka buyurtmalardan tashqari muntazam buyurtmalar oqimini yaratish."],
  ["Loyiha respublika bo‘ylab ishlay oladimi?", "Ha. Platforma viloyat–tuman–mahalla tuzilmasida qurilgan, barcha hududlar ma’lumotnomasi tayyor. Pilot natijalariga qarab bosqichma-bosqich kengaytiriladi."],
  ["Murojaatlar maxfiyligi qanday ta’minlanadi?", "Ishlaydigan MVP’da psixologik murojaat mazmuni faqat murojaatchi va mutaxassisga ko‘rinadi — mahalla vakili va administratorga ham ko‘rinmaydi. BEGOYIM HIMOYA uchun alohida xavfsizlik auditi, murojaatchi roziligi va manfaatlar to‘qnashuvida mustaqil mas’ulga yo‘naltirish mexanizmi nazarda tutilgan."],
  ["Loyihaning muvaffaqiyati qanday o‘lchanadi?", "Faol xizmat ko‘rsatuvchilar, birinchi buyurtmasini olgan ayollar, takroriy buyurtmalar, yakunlangan buyurtmalar qiymati va foydalanuvchilar qoniqishi. Platformadagi buyurtma qiymati tasdiqlangan shaxsiy daromad bilan tenglashtirilmaydi."],
].forEach(([q, a]) => {
  children.push(new Paragraph({ keepNext: true, spacing: { before: 160, after: 60 }, children: [new TextRun({ text: q, font: FONT, size: 26, bold: true, color: CRIMSON })] }));
  children.push(p(a, { run: { size: 26 } }));
});

// --- Ilova: eslatmalar ---
children.push(h("Ilova 3. Ma’ruzachi uchun eslatmalar"));
[
  "Hozir ishlaydigan imkoniyatlar (MVP) va taklif etilayotgan modullarni aniq ajrating — ishlab chiqilmagan funksiyalarni ishlayotgan tizim sifatida ko‘rsatmang.",
  "Barcha 7 ta modulni bir vaqtda moliyalashtirishni so‘ramang. Asosiy so‘rov — bandlik, buyurtmalar, mahalla hamkorligi va natijalarni baholashga qaratilgan MVP pilotiga kelishuv.",
  "BEGOYIM HIMOYA — ikkinchi yo‘nalish: alohida ijtimoiy ahamiyatga ega, lekin xavfsizlik va huquqiy tayyorgarlik talab qiladi.",
  "Savol-javob vaqtida 26-slaydni (savollarga tayyor javoblar) ochish mumkin.",
].forEach((t) => children.push(bullet(t)));

const doc = new Document({
  creator: AUTHOR, title: "BEGOYIM — ma’ruza matni",
  styles: { default: { document: { run: { font: FONT, size: 28 } } } },
  numbering: { config: [{ reference: "dots", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 300 } } } }] }] },
  sections: [{
    properties: { page: { margin: { top: 1134, bottom: 1134, left: 1440, right: 1134 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
      new TextRun({ text: `© 2026 ${AUTHOR} · BEGOYIM · `, font: FONT, size: 18, color: GREY }),
      new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18, color: GREY }),
    ] })] }) },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, buf);
  console.log("written", OUT);
});
