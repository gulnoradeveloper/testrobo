/*
 * BEGOYIM — animatsion taqdimot (PPTX) generatori.
 *   NODE_PATH=<node_modules> node build_deck.js out/BEGOYIM_taqdimot.pptx [video.mp4]
 * So'ng: python animate.py out/BEGOYIM_taqdimot.pptx  (kirish animatsiyalari va o'tishlar)
 *
 * Animatsiya uchun obyekt nomlari: "a<N>_<effekt>_<izoh>" — N bosqichi, effekt: fade | up | left | zoom.
 */
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa6");

const OUT = process.argv[2] || "out/BEGOYIM_taqdimot.pptx";
const VIDEO = process.argv[3];
const A = (p) => path.join(__dirname, "assets", p);
const V = (p) => path.join(__dirname, "..", "video", "assets", p);

const C = {
  crimson: "8E1238", crimson2: "A3123F", gold: "D6A24C", goldSoft: "F6E7C8", ink: "2B1A20",
  muted: "6F5F64", white: "FFFFFF", tint: "FBF1F3", probTint: "F4ECEE", green: "2E7D32", greenTint: "E8F5E9",
};
const HEAD = "Cambria", BODY = "Calibri";
const AUTHOR = "Bo‘ronova Gulnora Yodgorovna";

async function icon(Icon, color, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Icon, { color: "#" + color, size: String(size) }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
  pres.title = "BEGOYIM — Ayollar bandligi va farovonligi raqamli ekotizimi";
  pres.author = AUTHOR;
  pres.company = "BEGOYIM";
  pres.theme = { headFontFace: HEAD, bodyFontFace: BODY };

  const footer = (dark) => ({ text: { text: `© 2026 ${AUTHOR} · BEGOYIM`, options: { x: 0.6, y: 6.95, w: 7, h: 0.3, fontFace: BODY, fontSize: 10, color: dark ? "F6E7C8" : C.muted, margin: 0 } } });
  pres.defineSlideMaster({ title: "LIGHT", background: { path: A("bg_light.png") }, objects: [footer(false)], slideNumber: { x: 12.3, y: 6.92, w: 0.5, h: 0.3, fontFace: BODY, fontSize: 10, color: C.muted } });
  pres.defineSlideMaster({ title: "DARK", background: { path: A("bg_dark.png") }, objects: [footer(true)], slideNumber: { x: 12.3, y: 6.92, w: 0.5, h: 0.3, fontFace: BODY, fontSize: 10, color: "F6E7C8" } });

  const I = {};
  const iconList = {
    search: fa.FaMagnifyingGlass, house: fa.FaHouse, hand: fa.FaHandshake, mobile: fa.FaMobileScreen, chart: fa.FaChartColumn,
    comments: fa.FaComments, check: fa.FaCircleCheck, star: fa.FaStar, lock: fa.FaLock, people: fa.FaPeopleGroup,
    bank: fa.FaBuildingColumns, laptop: fa.FaLaptopCode, store: fa.FaStore, robot: fa.FaRobot, money: fa.FaMoneyBillWave,
    bulb: fa.FaLightbulb, arrow: fa.FaArrowRight, globe: fa.FaGlobe, clipboard: fa.FaClipboardList, line: fa.FaChartLine,
    shield: fa.FaShieldHeart, user: fa.FaUserCheck, flag: fa.FaFlag, heart: fa.FaHeart, xmark: fa.FaCircleXmark, play: fa.FaCirclePlay,
  };
  for (const [k, Ic] of Object.entries(iconList)) {
    I[k] = { w: await icon(Ic, "FFFFFF"), c: await icon(Ic, C.crimson2), g: await icon(Ic, C.gold) };
  }

  // ---- yordamchilar ----
  const txt = (s, text, o) => s.addText(text, { isTextBox: true, fontFace: BODY, margin: 0, valign: "top", ...o });
  function header(s, kicker, title, dark = false, step = 1) {
    if (kicker) txt(s, kicker.toUpperCase(), { x: 0.6, y: 0.5, w: 12, h: 0.3, fontSize: 12, bold: true, color: C.gold, charSpacing: 3, objectName: `a${step}_fade_kicker` });
    txt(s, title, { x: 0.6, y: 0.8, w: 12.1, h: 0.85, fontFace: HEAD, fontSize: 34, bold: true, color: dark ? C.white : C.ink, valign: "middle", objectName: `a${step}_fade_title` });
  }
  function iconCircle(s, ic, x, y, d, name, fill = C.crimson2, variant = "w") {
    s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill }, objectName: name + "_circle" });
    s.addImage({ data: I[ic][variant], x: x + d * 0.24, y: y + d * 0.24, w: d * 0.52, h: d * 0.52, objectName: name + "_icon" });
  }
  const card = (s, x, y, w, h, name, fill = C.white) => s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h, rectRadius: 0.15, fill: { color: fill }, line: { color: "EFE2E5", width: 0.75 },
    shadow: { type: "outer", color: "8E1238", opacity: 0.12, blur: 10, offset: 3, angle: 90 }, objectName: name,
  });
  // Rasmni kerakli nisbatda kesib (cover) qo'yish; skrinshotlar yuqori qismidan kesiladi
  const photo = async (s, file, x, y, w, h, name, top = false) => {
    const buf = await sharp(file).resize(Math.round(w * 220), Math.round(h * 220), { fit: "cover", position: top ? "top" : "centre" }).jpeg({ quality: 86 }).toBuffer();
    s.addImage({ data: "image/jpeg;base64," + buf.toString("base64"), x, y, w, h, objectName: name });
  };
  const notes = (s, t) => s.addNotes(t);

  // ================= 1. TITUL =================
  let s = pres.addSlide({ masterName: "LIGHT" });
  s.addImage({ path: A("logo.png"), x: 0.7, y: 0.9, w: 5.4, h: 4.36, objectName: "a1_zoom_logo" });
  txt(s, "MILLIY RAQAMLI EKOTIZIM", { x: 6.6, y: 1.25, w: 6.1, h: 0.35, fontSize: 13, bold: true, color: C.gold, charSpacing: 3, objectName: "a2_up_kicker" });
  txt(s, "Ayollar bandligi va farovonligi milliy raqamli ekotizimi", { x: 6.6, y: 1.6, w: 6.1, h: 1.3, fontFace: HEAD, fontSize: 30, bold: true, color: C.ink, objectName: "a2_up_title" });
  txt(s, "Ayoldan ayolga — imkoniyat va ko‘mak.", { x: 6.6, y: 3.05, w: 6.1, h: 0.6, fontFace: HEAD, fontSize: 24, italic: true, color: C.crimson2, objectName: "a3_up_slogan" });
  txt(s, [
    { text: "Loyiha muallifi: ", options: { color: C.muted } },
    { text: AUTHOR, options: { bold: true, color: C.ink } },
  ], { x: 6.6, y: 4.2, w: 6.1, h: 0.45, fontSize: 18, objectName: "a4_fade_author" });
  txt(s, "Iqtisodiy mustaqillik · Ijtimoiy himoya · Shaxsiy rivojlanish", { x: 6.6, y: 4.75, w: 6.1, h: 0.45, fontSize: 16, color: C.muted, objectName: "a4_fade_tagline" });
  notes(s, "Assalomu alaykum, hurmatli vazirlik rahbariyati, hurmatli mutasaddilar va yig‘ilish ishtirokchilari! Bugun e’tiboringizga ayollarning iqtisodiy mustaqilligini mustahkamlash, ularning bandligini ta’minlash va ijtimoiy farovonligini oshirishga qaratilgan BEGOYIM innovatsion raqamli platformasi loyihasini taqdim etmoqchiman.");

  // ================= 2. VIDEO =================
  s = pres.addSlide({ masterName: "DARK" });
  header(s, "Loyiha 3 daqiqada", "BEGOYIM taqdimot videosi", true);
  if (VIDEO && fs.existsSync(VIDEO)) {
    const coverFile = A("video_cover.jpg");
    const cover = fs.existsSync(coverFile) ? "data:image/jpeg;base64," + fs.readFileSync(coverFile).toString("base64") : undefined;
    s.addMedia({ type: "video", path: VIDEO, x: 2.23, y: 1.85, w: 8.87, h: 4.99, cover, objectName: "video" });
  } else {
    card(s, 1.67, 1.85, 10, 4.75, "a2_fade_videobox");
    txt(s, "Video: video/out/begoyim_taqdimot.mp4", { x: 1.67, y: 4, w: 10, h: 0.5, align: "center", fontSize: 18, color: C.muted, objectName: "a2_fade_videotext" });
  }
  notes(s, "Videoni ishga tushiring (slaydda videoni bosing). Video taxminan 3 daqiqa: muammolar, yechim, platforma, pilot ko‘rsatkichlar va hamkorlik modeli. Video tugagach, keyingi slaydlarda har bir qismni batafsil tushuntiramiz.");

  // ================= 3. ISTE'DOD =================
  s = pres.addSlide({ masterName: "LIGHT" });
  header(s, "Har bir mahallada", "Iste’dod bor — har bir xonadonda imkoniyat");
  txt(s, "Kimdir tikadi, kimdir mazali taom tayyorlaydi, kimdir bolalarga ta’lim beradi, hunarmandchilik yoki masofaviy ish bilan shug‘ullanadi.", { x: 0.6, y: 1.95, w: 5.4, h: 1.6, fontSize: 18, color: C.muted, objectName: "a2_up_lead" });
  card(s, 0.6, 3.85, 5.4, 1.35, "a3_up_quotecard");
  txt(s, "“Har bir mahalla — yangi daromad imkoniyatlari manbai.”", { x: 0.85, y: 4.0, w: 4.95, h: 1.05, fontFace: HEAD, fontSize: 21, italic: true, color: C.crimson2, valign: "middle", objectName: "a3_up_quote" });
  const grid = [["tikuvchilik.jpg", 6.4, 1.85, 3.2, 2.35], ["parda_big.jpg", 9.75, 1.85, 2.98, 2.35], ["osh_big.jpg", 6.4, 4.35, 2.1, 2.2], ["repetitorlik.jpg", 8.6, 4.35, 2.0, 2.2], ["hunar_big.jpg", 10.7, 4.35, 2.03, 2.2]];
  for (const [i, [f, x, y, w, h]] of grid.entries()) await photo(s, V("photos/" + f), x, y, w, h, `a${4 + i}_zoom_photo${i}`);
  notes(s, "Har bir mahallada hunarli ayollar bor: tikuvchi, pazanda, hunarmand, repetitor, masofaviy ishlay oladiganlar. Ularga yangi kasb o‘rgatish shart emas — ularning mavjud mahoratini daromadga aylantirish kerak.");

  // ================= 4. ASOSIY SAVOL =================
  s = pres.addSlide({ masterName: "DARK" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 4.4, y: 1.3, w: 4.55, h: 0.6, rectRadius: 0.3, fill: { color: "FFFFFF", transparency: 88 }, line: { color: "F6E7C8", width: 1 }, objectName: "a1_fade_qpill" });
  txt(s, "① Qanday muammoni hal qiladi?", { x: 4.4, y: 1.3, w: 4.55, h: 0.6, align: "center", valign: "middle", fontSize: 18, bold: true, color: C.goldSoft, objectName: "a1_fade_qtext" });
  txt(s, "Biz o‘z oldimizga muhim savol qo‘ydik:", { x: 0.8, y: 2.25, w: 11.7, h: 0.5, align: "center", fontSize: 20, color: "FFE0C7", objectName: "a2_fade_lead" });
  txt(s, [{ text: "Ayolning hunari bor, ishlash istagi bor, lekin mijozi bo‘lmasa —", options: { color: C.white, breakLine: true } }, { text: "uning iqtisodiy mustaqilligini qanday ta’minlaymiz?", options: { color: C.goldSoft } }],
    { x: 0.8, y: 2.9, w: 11.7, h: 2.2, align: "center", valign: "middle", fontFace: HEAD, fontSize: 36, bold: true, objectName: "a3_zoom_big" });
  txt(s, "Javob — BEGOYIM: ayolning salohiyatini aniqlashdan real daromadgacha bo‘lgan yo‘lni raqamlashtiruvchi yaxlit ekotizim.", { x: 1.4, y: 5.4, w: 10.5, h: 0.8, align: "center", fontSize: 18, color: "FFE0C7", objectName: "a4_up_answer" });
  notes(s, "Bugungi kunda mamlakatimizda xotin-qizlarni qo‘llab-quvvatlash, ularning bandligini ta’minlash va tadbirkorlik faoliyatini rivojlantirishga katta e’tibor qaratilmoqda. Shunga qaramay, o‘z hunari va salohiyatiga ega, ammo uni barqaror daromadga aylantirishda qiyinchiliklarga duch kelayotgan ayollar mavjud. Biz o‘z oldimizga savol qo‘ydik: ayolning hunari bor, ishlash istagi bor, lekin mijozi bo‘lmasa, uning iqtisodiy mustaqilligini qanday ta’minlaymiz? Ana shu savolga amaliy yechim sifatida BEGOYIM ishlab chiqilmoqda.");

  // ================= 5. OLTI MUAMMO =================
  s = pres.addSlide({ masterName: "LIGHT" });
  header(s, "Muammolar", "Iste’dod bor — lekin daromad yo‘li to‘silgan");
  const probs = [
    ["search", "Mijoz topish qiyin", "Xizmat faqat qo‘ni-qo‘shni va tanishlar orqali taklif qilinadi — mijozlar doirasi tor."],
    ["house", "Uydan uzoqlashib bo‘lmaydi", "Farzand tarbiyasi va ro‘zg‘or tufayli ko‘p ayollar to‘liq kunlik ishga chiqa olmaydi."],
    ["hand", "Ishonch yetishmaydi", "Buyurtmachi notanish ijrochiga ishonmaydi, ayol ham o‘z xavfsizligidan xavotirda."],
    ["mobile", "Ma’lumot tarqoq", "Xizmatlar guruh va e’lonlarda sochilgan: sifat, narx va baho ko‘rinmaydi."],
    ["chart", "Natijani o‘lchab bo‘lmaydi", "Kim nimani biladi, kim ish izlayapti — mahalla va bo‘lim uchun aniq raqamli ma’lumot yo‘q."],
    ["comments", "Ruhiy yuk e’tiborsiz", "Ayollar psixologik yordam so‘rashdan tortinadi — maxfiy va qulay murojaat imkoni kam."],
  ];
  probs.forEach(([ic, h, p], i) => {
    const x = 0.6 + (i % 3) * 4.1, y = 1.95 + Math.floor(i / 3) * 2.45, n = 2 + i;
    card(s, x, y, 3.9, 2.25, `a${n}_up_card${i}`);
    iconCircle(s, ic, x + 0.25, y + 0.25, 0.62, `a${n}_up_ic${i}`, C.tint, "c");
    txt(s, String(i + 1).padStart(2, "0"), { x: x + 2.9, y: y + 0.2, w: 0.8, h: 0.5, align: "right", fontFace: HEAD, fontSize: 26, bold: true, color: "EAD3D8", objectName: `a${n}_up_no${i}` });
    txt(s, h, { x: x + 0.25, y: y + 0.98, w: 3.45, h: 0.4, fontSize: 17, bold: true, color: C.crimson2, objectName: `a${n}_up_h${i}` });
    txt(s, p, { x: x + 0.25, y: y + 1.38, w: 3.45, h: 0.8, fontSize: 13, color: C.muted, objectName: `a${n}_up_p${i}` });
  });
  notes(s, "Oltita to‘siq: 1) mijoz topish qiyin — xizmat faqat tanishlar orqali; 2) uydan uzoqlashib bo‘lmaydi — oila, farzandlar; 3) ishonch yetishmaydi — buyurtmachi ham, ayol ham xavotirda; 4) ma’lumot tarqoq — narx, sifat, baho ko‘rinmaydi; 5) natijani o‘lchab bo‘lmaydi — mahalla va bo‘limda aniq ma’lumot yo‘q; 6) ruhiy yuk — psixologik yordamga murojaat qilishdan tortinish.");

  // ================= 6. XULOSA =================
  s = pres.addSlide({ masterName: "DARK" });
  txt(s, "Natijada minglab ayollarning bilim va hunari daromad manbaiga aylanmay qolmoqda.", { x: 1.5, y: 1.6, w: 10.3, h: 1.0, align: "center", fontSize: 22, color: "FFE0C7", objectName: "a1_fade_lead" });
  txt(s, [{ text: "Ularga yangi kasb emas —", options: { color: C.white, breakLine: true } }, { text: "o‘z mehnatini qadrlaydigan mijoz kerak.", options: { color: C.goldSoft } }],
    { x: 0.8, y: 2.9, w: 11.7, h: 2.2, align: "center", valign: "middle", fontFace: HEAD, fontSize: 42, bold: true, objectName: "a2_zoom_quote" });
  notes(s, "Asosiy xulosa: ayollarga yangi kasb o‘rgatish emas, ularning mehnatini qadrlaydigan mijoz bilan bog‘lash kerak. BEGOYIM aynan shuni qiladi.");

  // ================= UCH USTUVOR YO'NALISH =================
  s = pres.addSlide({ masterName: "LIGHT" });
  header(s, "Yaxlit ekotizim", "BEGOYIMning uchta ustuvor yo‘nalishi");
  const pillars = [
    ["money", "Iqtisodiy mustaqillik", "Bandlik va daromad", [["Xizmatlar katalogi va buyurtmalar", 1], ["AI asosida mijoz bilan moslashtirish", 1], ["Daromad hisobi va dashboard", 1]]],
    ["shield", "Ijtimoiy himoya", "Xavfsizlik va murojaatlar", [["Mahalla tasdig‘i va reyting", 1], ["BEGOYIM Safe — ish vaqti qaydi", 1], ["HIMOYA — xavfsiz murojaat", 0]]],
    ["bulb", "Shaxsiy rivojlanish", "Ta’lim va farovonlik", [["Maxfiy psixologik maslahat", 1], ["BEGOYIM Academy — qisqa kurslar", 0], ["Mikro-tadbirkorlik yordamchisi", 0]]],
  ];
  pillars.forEach(([ic, h, sub, items], i) => {
    const x = 0.6 + i * 4.1, k = 2 + i;
    card(s, x, 1.9, 3.9, 4.55, `a${k}_up_pc${i}`);
    iconCircle(s, ic, x + 1.5, 2.1, 0.9, `a${k}_up_pic${i}`, i === 1 ? C.gold : C.crimson2);
    txt(s, h, { x: x + 0.2, y: 3.1, w: 3.5, h: 0.45, align: "center", fontFace: HEAD, fontSize: 20, bold: true, color: C.crimson2, objectName: `a${k}_up_ph${i}` });
    txt(s, sub, { x: x + 0.2, y: 3.55, w: 3.5, h: 0.35, align: "center", fontSize: 14, bold: true, color: C.gold, objectName: `a${k}_up_ps${i}` });
    items.forEach(([t, ready], j) => {
      const y = 4.05 + j * 0.75;
      s.addImage({ data: ready ? I.check.c : I.flag.g, x: x + 0.3, y: y + 0.05, w: 0.28, h: 0.28, objectName: `a${k}_up_pi${i}${j}` });
      txt(s, t, { x: x + 0.7, y, w: 3.0, h: 0.4, fontSize: 14, bold: true, color: C.ink, objectName: `a${k}_up_pt${i}${j}` });
      txt(s, ready ? "MVP’da ishlaydi" : "Taklif / rivojlantirish", { x: x + 0.7, y: y + 0.36, w: 3.0, h: 0.3, fontSize: 11, color: ready ? C.green : C.muted, objectName: `a${k}_up_pr${i}${j}` });
    });
  });
  txt(s, "Asosiy maqsad — ayolni faqat ish bilan ta’minlash emas, balki uning iqtisodiy mustaqilligi, huquqiy himoyasi va ijtimoiy farovonligiga kompleks yondashish.", { x: 0.6, y: 6.5, w: 12.13, h: 0.4, align: "center", fontSize: 13, italic: true, color: C.muted, objectName: "a5_fade_goal" });
  notes(s, "BEGOYIM — oddiy e’lonlar platformasi emas. Uchta ustuvor yo‘nalish: iqtisodiy mustaqillik — bandlik va daromad; ijtimoiy himoya — xavfsizlik va murojaatlar; shaxsiy rivojlanish — ta’lim va farovonlik. Yashil belgili imkoniyatlar ishlaydigan MVP’da mavjud; qolganlari loyiha taklifi sifatida bosqichma-bosqich joriy etiladi. Ishlab chiqilmagan funksiyalarni ishlayotgan tizim sifatida ko‘rsatmaymiz.");

  // ================= 7. RAQAMLI KO'PRIK =================
  s = pres.addSlide({ masterName: "LIGHT" });
  header(s, "Yechim", "BEGOYIM — hunar va mijoz o‘rtasidagi raqamli ko‘prik");
  card(s, 0.6, 2.0, 3.0, 3.6, "a2_left_hcard");
  await photo(s, V("photos/tikuvchilik.jpg"), 0.6, 2.0, 3.0, 2.3, "a2_left_hphoto");
  txt(s, "Hunar", { x: 0.85, y: 4.4, w: 2.6, h: 0.5, fontFace: HEAD, fontSize: 24, bold: true, color: C.crimson2, objectName: "a2_left_htitle" });
  txt(s, "Ayol o‘z xizmatini joylashtiradi", { x: 0.85, y: 4.9, w: 2.6, h: 0.6, fontSize: 14, color: C.muted, objectName: "a2_left_htext" });
  card(s, 9.73, 2.0, 3.0, 3.6, "a3_up_mcard");
  await photo(s, V("photos/boshqa.jpg"), 9.73, 2.0, 3.0, 2.3, "a3_up_mphoto");
  txt(s, "Mijoz", { x: 9.98, y: 4.4, w: 2.6, h: 0.5, fontFace: HEAD, fontSize: 24, bold: true, color: C.crimson2, objectName: "a3_up_mtitle" });
  txt(s, "Buyurtmachi kerakli mutaxassisni topadi", { x: 9.98, y: 4.9, w: 2.6, h: 0.6, fontSize: 14, color: C.muted, objectName: "a3_up_mtext" });
  s.addImage({ path: A("arc.png"), x: 3.55, y: 2.25, w: 6.2, h: 2.33, objectName: "a4_fade_arc" });
  s.addImage({ path: A("logo.png"), x: 5.6, y: 2.95, w: 2.15, h: 1.74, objectName: "a5_zoom_logo" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 5.4, y: 4.8, w: 2.55, h: 0.5, rectRadius: 0.25, fill: { color: C.goldSoft }, line: { color: C.goldSoft }, objectName: "a5_zoom_aipill" });
  txt(s, "AI moslashtiradi", { x: 5.4, y: 4.8, w: 2.55, h: 0.5, align: "center", valign: "middle", fontSize: 15, bold: true, color: C.crimson, objectName: "a5_zoom_aitext" });
  txt(s, "Ayol xizmatini joylaydi. Buyurtmachi mutaxassisni topadi. Sun’iy intellekt ularni o‘zaro moslashtirishga yordam beradi.", { x: 1.5, y: 5.95, w: 10.3, h: 0.7, align: "center", fontSize: 17, color: C.muted, objectName: "a6_fade_lead" });
  notes(s, "Yechim: BEGOYIM — hunar va mijoz o‘rtasidagi raqamli ko‘prik. Ayol xizmatini joylaydi, buyurtmachi topadi, sun’iy intellekt ularni moslashtiradi.");

  // ================= 8. MUAMMO -> YECHIM =================
  s = pres.addSlide({ masterName: "LIGHT" });
  header(s, "Har bir to‘siqqa — aniq yechim", "Muammo → BEGOYIM yechimi");
  const sol = [
    ["search", "Mijoz topish qiyin", "globe", "Raqamli katalog va AI tavsiya — xizmatni butun hudud ko‘radi"],
    ["house", "Uydan uzoqlashib bo‘lmaydi", "house", "Uyda yoki masofadan xizmat, moslashuvchan grafik"],
    ["hand", "Ishonch yetishmaydi", "check", "Mahalla tasdig‘i, reyting va BEGOYIM Safe"],
    ["mobile", "Ma’lumot tarqoq", "clipboard", "Narx, hudud, baho va portfolio — bitta platformada"],
    ["chart", "Natijani o‘lchab bo‘lmaydi", "line", "Mahalla va bo‘lim dashboardlari — real ko‘rsatkichlar"],
    ["comments", "Ruhiy yuk e’tiborsiz", "lock", "Psixologga maxfiy onlayn / oflayn yozilish"],
  ];
  sol.forEach(([pic, p, sic, t], i) => {
    const y = 1.9 + i * 0.8, n = 2 + i;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y, w: 4.6, h: 0.65, rectRadius: 0.12, fill: { color: C.probTint }, line: { color: C.probTint }, objectName: `a${n}_left_pbox${i}` });
    s.addImage({ data: I[pic].c, x: 0.78, y: y + 0.16, w: 0.33, h: 0.33, objectName: `a${n}_left_pic${i}` });
    txt(s, p, { x: 1.25, y, w: 3.85, h: 0.65, valign: "middle", fontSize: 15, bold: true, color: C.muted, objectName: `a${n}_left_ptext${i}` });
    s.addImage({ data: I.arrow.g, x: 5.45, y: y + 0.15, w: 0.5, h: 0.35, objectName: `a${n}_left_arr${i}` });
    card(s, 6.2, y, 6.53, 0.65, `a${n}_left_sbox${i}`);
    iconCircle(s, sic, 6.33, y + 0.09, 0.47, `a${n}_left_sic${i}`);
    txt(s, t, { x: 6.95, y, w: 5.7, h: 0.65, valign: "middle", fontSize: 15, bold: true, color: C.crimson2, objectName: `a${n}_left_stext${i}` });
  });
  notes(s, "Har bir muammoga aniq yechim: mijoz topish — raqamli katalog va AI; uydan chiqa olmaslik — uyda va masofadan xizmat; ishonch — mahalla tasdig‘i, reyting, BEGOYIM Safe; tarqoqlik — yagona platforma; o‘lchash — dashboardlar; ruhiy yuk — maxfiy psixologik yordam.");

  // ================= 10. HIKOYA =================
  s = pres.addSlide({ masterName: "LIGHT" });
  header(s, "Namunaviy hikoya", "Aziza opa: avval va BEGOYIM bilan");
  await photo(s, V("photos/korpacha_big.jpg"), 0.6, 1.9, 3.3, 4.0, "a2_zoom_photo");
  txt(s, "Navbahor mahallasi · parda va ko‘rpacha ustasi", { x: 0.6, y: 6.0, w: 3.3, h: 0.6, fontSize: 13, color: C.muted, objectName: "a2_zoom_cap" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 4.2, y: 1.9, w: 4.15, h: 4.7, rectRadius: 0.15, fill: { color: C.probTint }, line: { color: C.probTint }, objectName: "a3_left_before" });
  txt(s, "Avval", { x: 4.5, y: 2.1, w: 3.6, h: 0.6, fontFace: HEAD, fontSize: 26, bold: true, color: C.muted, objectName: "a3_left_bh" });
  ["Buyurtmalar faqat tanishlardan", "Narxini qanday belgilashni bilmaydi", "Yangi mijozlar unga ishonmaydi", "Daromad tasodifiy va beqaror"].forEach((t, i) => {
    s.addImage({ data: I.xmark.c, x: 4.5, y: 2.95 + i * 0.85, w: 0.32, h: 0.32, objectName: `a${4 + i}_fade_bx${i}` });
    txt(s, t, { x: 4.95, y: 2.88 + i * 0.85, w: 3.2, h: 0.75, fontSize: 16, bold: true, color: C.muted, objectName: `a${4 + i}_fade_bt${i}` });
  });
  card(s, 8.58, 1.9, 4.15, 4.7, "a8_up_after");
  txt(s, "BEGOYIM bilan", { x: 8.88, y: 2.1, w: 3.6, h: 0.6, fontFace: HEAD, fontSize: 26, bold: true, color: C.crimson2, objectName: "a8_up_ah" });
  ["Xizmati butun hududga ko‘rinadi", "Narx va xizmat shakli aniq", "“Mahalla tomonidan tasdiqlangan” belgisi", "Har bir buyurtma — baho va hisoblangan daromad"].forEach((t, i) => {
    s.addImage({ data: I.check.g, x: 8.88, y: 2.95 + i * 0.85, w: 0.32, h: 0.32, objectName: `a${9 + i}_fade_ax${i}` });
    txt(s, t, { x: 9.33, y: 2.88 + i * 0.85, w: 3.2, h: 0.75, fontSize: 16, bold: true, color: C.ink, objectName: `a${9 + i}_fade_at${i}` });
  });
  notes(s, "Bu namunaviy hikoya. Aziza opa — parda va ko‘rpacha ustasi. Avval buyurtmalar faqat tanishlardan, narx aniq emas, yangi mijozlar ishonmas edi. BEGOYIM bilan xizmati butun hududga ko‘rinadi, mahalla tasdig‘i bor, har bir buyurtma baho va daromad sifatida hisobga olinadi.");

  // ================= 11. MAHALLA HAMKOR =================
  s = pres.addSlide({ masterName: "DARK" });
  header(s, "Mahalla — bandlikning eng yaqin hamkori", "Mahalla + texnologiya + ayol mehnati", true);
  [["hand", "Mahalla — ", "ishonchni mustahkamlaydi."], ["bulb", "Texnologiya — ", "imkoniyatlarni birlashtiradi."], ["money", "Ayol — ", "o‘z mehnati bilan daromad topadi."]].forEach(([ic, a, b], i) => {
    iconCircle(s, ic, 1.6, 2.05 + i * 1.15, 0.85, `a${2 + i}_left_m${i}`, C.gold);
    txt(s, [{ text: a, options: { color: C.white } }, { text: b, options: { color: C.goldSoft } }], { x: 2.75, y: 2.05 + i * 1.15, w: 9, h: 0.85, valign: "middle", fontSize: 26, bold: true, objectName: `a${2 + i}_left_mt${i}` });
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 1.6, y: 5.6, w: 10.1, h: 0.95, rectRadius: 0.12, fill: { color: "FFFFFF", transparency: 90 }, line: { color: C.gold, width: 1 }, objectName: "a5_up_box" });
  txt(s, "Mahalladagi xotin-qizlar faoli ayollarni aniqlaydi, jalb qiladi va tasdiqlashda ishtirok etadi — BEGOYIM ularni mijozlar bilan bog‘laydi.", { x: 1.9, y: 5.6, w: 9.6, h: 0.95, valign: "middle", fontSize: 18, color: "FFE9CF", objectName: "a5_up_boxt" });
  notes(s, "Mahalla — bandlikning eng yaqin hamkori: ishonchni ta’minlaydi. Texnologiya imkoniyatlarni birlashtiradi. Ayol o‘z mehnati bilan daromad topadi.");

  // ================= 12. PLATFORMA YO'LI =================
  s = pres.addSlide({ masterName: "LIGHT" });
  header(s, "Platformadagi yo‘l", "Ro‘yxatdan o‘tishdan daromadgacha — 7 qadam");
  ["Ro‘yxatdan o‘tish", "Profil va ko‘nikma", "Mahalla tasdig‘i", "Xizmat joylash", "AI tavsiya", "Buyurtma va baho", "Daromad"].forEach((t, i) => {
    const x = 0.6 + i * 1.75;
    s.addShape(pres.shapes.OVAL, { x: x + 0.55, y: 1.85, w: 0.55, h: 0.55, fill: { color: i === 6 ? C.gold : C.crimson2 }, line: { color: C.white, width: 1.5 }, objectName: `a${2 + i}_up_n${i}` });
    txt(s, String(i + 1), { x: x + 0.55, y: 1.85, w: 0.55, h: 0.55, align: "center", valign: "middle", fontSize: 16, bold: true, color: C.white, objectName: `a${2 + i}_up_nt${i}` });
    txt(s, t, { x, y: 2.45, w: 1.65, h: 0.55, align: "center", fontSize: 13, bold: true, color: C.ink, objectName: `a${2 + i}_up_st${i}` });
    if (i < 6) s.addImage({ data: I.arrow.g, x: x + 1.35, y: 1.98, w: 0.4, h: 0.28, objectName: `a${2 + i}_up_sa${i}` });
  });
  card(s, 0.6, 3.25, 6.0, 3.45, "a9_up_shot1card");
  await photo(s, V("shots/verify.png"), 0.7, 3.35, 5.8, 3.25, "a9_up_shot1", true);
  card(s, 6.73, 3.25, 6.0, 3.45, "a10_up_shot2card");
  await photo(s, V("shots/income.png"), 6.83, 3.35, 5.8, 3.25, "a10_up_shot2", true);
  notes(s, "Platformadagi yo‘l 7 qadamdan iborat: ro‘yxatdan o‘tish, profil va ko‘nikma, mahalla tasdig‘i, xizmat joylash, AI tavsiya, buyurtma va baho, daromad. Chapda — mahalla vakilining verifikatsiya sahifasi, o‘ngda — ijrochining daromad dashboardi. Bu ishlaydigan MVP, jonli namoyish qilish mumkin.");

  // ================= 13. AI =================
  s = pres.addSlide({ masterName: "DARK" });
  header(s, "Sun’iy intellekt", "Har bir ayolga imkoniyat topishda ko‘maklashadi", true);
  card(s, 0.6, 1.95, 12.13, 0.85, "a2_left_query");
  txt(s, "“Ertaga Buxoro shahrida 2 ta xonani tozalaydigan ayol kerak.”", { x: 0.95, y: 1.95, w: 11.5, h: 0.85, valign: "middle", fontSize: 20, italic: true, color: C.ink, objectName: "a2_left_querytext" });
  ["xizmat = Uy tozalash", "hudud = Buxoro shahri", "vaqt = ertaga"].forEach((t, i) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6 + i * 3.0, y: 3.05, w: 2.8, h: 0.5, rectRadius: 0.12, fill: { color: C.goldSoft }, line: { color: C.goldSoft }, objectName: `a${3 + i}_up_chip${i}` });
    txt(s, t, { x: 0.6 + i * 3.0, y: 3.05, w: 2.8, h: 0.5, align: "center", valign: "middle", fontSize: 15, bold: true, color: C.crimson, objectName: `a${3 + i}_up_chipt${i}` });
  });
  [["Mohira Saidova", "★ 4,8"], ["Dilnoza Rahimova", "★ 4,6"]].forEach(([n, r], i) => {
    const x = 0.6 + i * 6.2, k = 6 + i;
    card(s, x, 3.85, 5.93, 1.65, `a${k}_up_m${i}`);
    s.addShape(pres.shapes.OVAL, { x: x + 0.3, y: 4.1, w: 1.15, h: 1.15, fill: { color: C.white }, line: { color: C.crimson2, width: 5 }, objectName: `a${k}_up_ring${i}` });
    txt(s, "99%", { x: x + 0.3, y: 4.1, w: 1.15, h: 1.15, align: "center", valign: "middle", fontSize: 20, bold: true, color: C.crimson, objectName: `a${k}_up_pct${i}` });
    txt(s, n, { x: x + 1.7, y: 4.15, w: 4, h: 0.45, fontSize: 19, bold: true, color: C.ink, objectName: `a${k}_up_n${i}` });
    txt(s, `Uy tozalash · Buxoro shahri · ${r} · ✓ Tasdiqlangan`, { x: x + 1.7, y: 4.65, w: 4.1, h: 0.6, fontSize: 13, color: C.muted, objectName: `a${k}_up_d${i}` });
  });
  txt(s, [{ text: "Ko‘nikma, hudud, reyting, mahalla tasdig‘i va bo‘shlik hisobga olinadi.", options: { breakLine: true } }, { text: "AI faqat tavsiya beradi — tanlov insonda.", options: { bold: true, color: C.goldSoft } }],
    { x: 0.6, y: 5.75, w: 12.13, h: 0.9, align: "center", fontSize: 16, color: "FFE9CF", objectName: "a8_fade_formula" });
  notes(s, "Sun’iy intellekt oddiy tilda yozilgan so‘rovdan xizmat turi, hudud va vaqtni aniqlaydi, so‘ng mos ijrochilarni foiz bilan ko‘rsatadi. Bu platformadagi haqiqiy natija. Muhim: AI qaror qabul qilmaydi, faqat tavsiya beradi.");

  // ================= 14. ISHONCH =================
  s = pres.addSlide({ masterName: "LIGHT" });
  header(s, "Bandlik bilan birga", "Ishonch va farovonlik");
  [["check", "Mahalla tomonidan tasdiqlash", "Mahalla vakili ijrochini tekshiradi — mijoz ishonch bilan buyurtma beradi."],
   ["star", "Xizmatlarni baholash", "Har bir bajarilgan buyurtma baholanadi — sifat va obro‘ ko‘rinib turadi."],
   ["shield", "BEGOYIM Safe", "Mijoz manzilidagi ishda boshlanish va yakunlanish vaqti qayd etiladi."],
   ["comments", "Psixologik ko‘mak", "Tajribali psixologlar bilan ONLINE yoki OFFLINE maslahat. Murojaat maxfiy."]].forEach(([ic, h, p], i) => {
    const y = 1.85 + i * 1.2, k = 2 + i;
    card(s, 0.6, y, 8.3, 1.05, `a${k}_left_f${i}`);
    iconCircle(s, ic, 0.8, y + 0.17, 0.7, `a${k}_left_fi${i}`);
    txt(s, h, { x: 1.7, y: y + 0.12, w: 7, h: 0.4, fontSize: 17, bold: true, color: C.crimson2, objectName: `a${k}_left_fh${i}` });
    txt(s, p, { x: 1.7, y: y + 0.52, w: 7, h: 0.45, fontSize: 14, color: C.muted, objectName: `a${k}_left_fp${i}` });
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 9.55, y: 1.75, w: 2.75, h: 5.0, rectRadius: 0.3, fill: { color: "1D1216" }, line: { color: "1D1216" }, objectName: "a6_up_phone" });
  await photo(s, V("shots/m_home.png"), 9.68, 1.88, 2.49, 4.74, "a6_up_phonescreen", true);
  notes(s, "Bandlik bilan birga ishonch va farovonlik: mahalla tasdig‘i, xizmatlarni baholash, BEGOYIM Safe — ish vaqti qaydi, va maxfiy psixologik ko‘mak. Psixologik murojaatlar mazmuni hech kimga, hatto administratorga ham ko‘rinmaydi.");

  // ================= 15. O'LCHANADIGAN NATIJA =================
  s = pres.addSlide({ masterName: "LIGHT" });
  header(s, "② Hududimizga qanday natija beradi?", "Oila va xotin-qizlar bo‘limi uchun — o‘lchanadigan natija");
  card(s, 0.6, 1.9, 6.6, 4.1, "a2_left_dashcard");
  await photo(s, V("shots/mahalla.png"), 0.7, 2.0, 6.4, 3.9, "a2_left_dash", true);
  [["user", "Qancha ayol xizmat taklif qilmoqda"], ["check", "Qancha buyurtma bajarildi"], ["line", "Qancha ayol daromad ola boshladi"]].forEach(([ic, t], i) => {
    iconCircle(s, ic, 7.6, 2.05 + i * 1.15, 0.8, `a${3 + i}_left_k${i}`);
    txt(s, t, { x: 8.6, y: 2.05 + i * 1.15, w: 4.1, h: 0.8, valign: "middle", fontSize: 18, bold: true, color: C.ink, objectName: `a${3 + i}_left_kt${i}` });
  });
  card(s, 0.6, 6.15, 12.13, 0.65, "a6_up_quote");
  txt(s, "“Bandlikni faqat hisobotlarda emas, real buyurtmalar va daromadlarda ko‘raylik.”", { x: 0.85, y: 6.15, w: 11.7, h: 0.65, valign: "middle", fontFace: HEAD, fontSize: 18, italic: true, color: C.crimson2, objectName: "a6_up_quotet" });
  notes(s, "Ikkinchi savol: hududimizga qanday natija beradi? Mahalla va Oila va xotin-qizlar bo‘limi real vaqtda ko‘radi: nechta ayol xizmat taklif qilmoqda, nechta buyurtma bajarildi, nechta ayol daromad ola boshladi. Dashboardda faqat umumiy ko‘rsatkichlar, shaxsiy va psixologik ma’lumotlar yo‘q.");

  // ================= HIMOYA: MAKET VA JARAYON =================
  s = pres.addSlide({ masterName: "LIGHT" });
  header(s, "Taklif etilayotgan modul · ayollar murojaatlari yagona raqamli tizimi", "BEGOYIM HIMOYA — xavfsiz murojaat va ko‘mak");
  card(s, 0.6, 1.9, 5.0, 4.85, "a2_left_mock");
  s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 1.9, w: 5.0, h: 0.75, fill: { color: C.crimson2 }, line: { color: C.crimson2 }, objectName: "a2_left_mockhead" });
  s.addImage({ data: I.shield.w, x: 0.8, y: 2.03, w: 0.48, h: 0.48, objectName: "a2_left_mockicon" });
  txt(s, "BEGOYIM HIMOYA", { x: 1.4, y: 1.9, w: 4.0, h: 0.75, valign: "middle", fontFace: HEAD, fontSize: 20, bold: true, color: C.white, objectName: "a2_left_mocktitle" });
  txt(s, "Sizning xavfsizligingiz va qadr-qimmatingiz muhim", { x: 0.85, y: 2.8, w: 4.5, h: 0.4, fontSize: 14, bold: true, color: C.crimson2, objectName: "a2_left_mocksub" });
  txt(s, "Tazyiq, zo‘ravonlik, shilqimlik, kamsitish yoki huquqlaringiz buzilishiga duch kelsangiz — mutaxassis va vakolatli tashkilotlarga maxfiy murojaat qiling. Siz yolg‘iz emassiz.", { x: 0.85, y: 3.2, w: 4.5, h: 1.1, fontSize: 12.5, color: C.muted, objectName: "a2_left_mocktext" });
  [["Murojaat yuborish", C.crimson2, C.white], ["Mutaxassis yordami", C.goldSoft, C.crimson], ["Xavfsizlik bo‘yicha yordam", C.goldSoft, C.crimson], ["Murojaat holati", C.goldSoft, C.crimson]].forEach(([t, f, c], i) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.85, y: 4.4 + i * 0.55, w: 4.5, h: 0.45, rectRadius: 0.1, fill: { color: f }, line: { color: f }, objectName: `a2_left_btn${i}` });
    txt(s, t, { x: 0.85, y: 4.4 + i * 0.55, w: 4.5, h: 0.45, align: "center", valign: "middle", fontSize: 14, bold: true, color: c, objectName: `a2_left_btnt${i}` });
  });
  const flow = [["mobile", "Ayol murojaat yuboradi", "Himoyalangan shakl orqali"], ["search", "Xavf va murojaat turini aniqlash", "Shoshilinch xavfda — tezkor yordam yo‘riqnomasi"], ["user", "Vakolatli mas’ulga yo‘naltirish", "Hudud, tur va maxfiylik talablariga muvofiq"], ["clipboard", "Ko‘rib chiqish va qayta aloqa", "Murojaat raqami, holati va natijasi"]];
  flow.forEach(([ic, h, p], i) => {
    const y = 1.95 + i * 1.18, k = 3 + i;
    iconCircle(s, ic, 6.05, y, 0.8, `a${k}_left_fl${i}`, i === 1 ? C.gold : C.crimson2);
    txt(s, `${i + 1}. ${h}`, { x: 7.05, y: y + 0.02, w: 5.7, h: 0.4, fontSize: 17, bold: true, color: C.ink, objectName: `a${k}_left_flh${i}` });
    txt(s, p, { x: 7.05, y: y + 0.42, w: 5.7, h: 0.4, fontSize: 14, color: C.muted, objectName: `a${k}_left_flp${i}` });
  });
  txt(s, "ⓘ Bu taklif etilayotgan interfeys maketi — hozircha ishlaydigan murojaat xizmati emas.", { x: 6.05, y: 6.45, w: 6.7, h: 0.35, fontSize: 12, italic: true, color: C.muted, objectName: "a7_fade_note" });
  notes(s, "Loyihani yanada rivojlantirib, BEGOYIM HIMOYA modulini kiritishni taklif etamiz. Ayollar tazyiq, zo‘ravonlik, kamsitish, shilqimlik va boshqa muammoli holatlar yuzasidan mahalla hamda vakolatli tashkilotlarga xavfsiz murojaat qila oladi. Murojaatlar tegishli mas’ullarga yo‘naltiriladi, ko‘rib chiqilishi kuzatiladi va murojaatchiga belgilangan tartibda javob qaytariladi. Bu — interfeys maketi, modul hali ishlab chiqilmagan.");

  // ================= HIMOYA: XAVFSIZLIK TAMOYILLARI =================
  s = pres.addSlide({ masterName: "DARK" });
  header(s, "BEGOYIM HIMOYA", "Murojaatchi xavfsizligi — birinchi o‘rinda", true);
  [["lock", "Maxfiylik va rozilik", "Zo‘ravonlik yoki tazyiq haqidagi murojaat mahalla faoli yoki barcha xodimlarga avtomatik yuborilmaydi. Ayolning xavfsizligi, roziligi va ma’lumotlari maxfiyligi ustuvor."],
   ["user", "Mustaqil yo‘naltirish", "Murojaat mahalla vakilining o‘zi yoki murojaatchining yaqin tanishi bilan bog‘liq bo‘lsa — u mustaqil vakolatli mas’ulga yo‘naltiriladi."],
   ["shield", "Favqulodda xizmatlar o‘rnini bosmaydi", "Shoshilinch xavf holatida platforma tezkor yordam yo‘riqnomasini beradi va favqulodda xizmatlarga yo‘naltiradi."]].forEach(([ic, h, p], i) => {
    const y = 1.95 + i * 1.4, k = 2 + i;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y, w: 12.13, h: 1.2, rectRadius: 0.12, fill: { color: "FFFFFF", transparency: 90 }, line: { color: C.gold, width: 1 }, objectName: `a${k}_left_pr${i}` });
    iconCircle(s, ic, 0.85, y + 0.2, 0.8, `a${k}_left_pri${i}`, C.gold);
    txt(s, h, { x: 1.9, y: y + 0.12, w: 10.6, h: 0.4, fontSize: 19, bold: true, color: C.goldSoft, objectName: `a${k}_left_prh${i}` });
    txt(s, p, { x: 1.9, y: y + 0.52, w: 10.6, h: 0.6, fontSize: 14.5, color: "FFE9CF", objectName: `a${k}_left_prp${i}` });
  });
  txt(s, "HIMOYA moduli pilotdan oldin: alohida xavfsizlik auditi, vakolatli tashkilotlar bilan kelishuv va shaxsiy ma’lumotlarni himoya qilish tartibi.", { x: 0.6, y: 6.25, w: 12.13, h: 0.55, align: "center", fontSize: 14, bold: true, color: C.goldSoft, objectName: "a5_fade_audit" });
  notes(s, "Respublika darajasidagi tizimda murojaatni oddiy botda mahalla xodimiga yuborishning o‘zi yetarli emas: ayrim murojaatlar maxfiylikni, ayrimlari zudlik bilan vakolatli xizmatlar aralashuvini talab qiladi. Uchta tamoyil: maxfiylik va rozilik; manfaatlar to‘qnashuvida mustaqil mas’ulga yo‘naltirish; platforma favqulodda xizmatlar o‘rnini bosmaydi. HIMOYA moduli xavfsizlik auditi va vakolatli tashkilotlar bilan kelishuvdan keyin pilotga chiqariladi.");

  // ================= 7 STRATEGIK MODUL =================
  s = pres.addSlide({ masterName: "LIGHT" });
  header(s, "Respublika darajasiga olib chiqadigan yo‘nalishlar", "BEGOYIMning 7 ta strategik moduli");
  const mods = [
    ["robot", "BEGOYIM AI", "Raqamli kasb maslahatchisi: mos xizmat, rivojlanish yo‘li va buyurtmalar"],
    ["chart", "BEGOYIM Mahalla", "Hududiy bandlik xaritasi: talabgir kasblar va faol ijrochilar"],
    ["store", "BEGOYIM Market", "Atlas-adras, kashtachilik, milliy liboslar — respublika bo‘ylab savdo"],
    ["laptop", "BEGOYIM Academy", "Raqamli savodxonlik, marketing, moliya bo‘yicha qisqa kurslar"],
    ["shield", "BEGOYIM HIMOYA", "Xavfsiz murojaat, psixologik yordamga yo‘naltirish, qayta aloqa"],
    ["line", "BEGOYIM Biznes", "Narx, xarajat-foyda, biznes-reja va qo‘llab-quvvatlash dasturlari"],
    ["bank", "BEGOYIM Hamkor", "Maktab, bog‘cha, korxonalar buyurtmasi — muntazam daromad oqimi"],
  ];
  mods.forEach(([ic, h, p], i) => {
    const row = i < 4 ? 0 : 1, col = row === 0 ? i : i - 4;
    const x = row === 0 ? 0.6 + col * 3.08 : 2.14 + col * 3.08, y = row === 0 ? 1.9 : 4.3, k = 2 + i;
    const star = h === "BEGOYIM Hamkor";
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 2.88, h: 2.2, rectRadius: 0.15, fill: { color: star ? "FFF8EA" : C.white }, line: { color: star ? C.gold : "EFE2E5", width: star ? 2.5 : 0.75 }, shadow: { type: "outer", color: "8E1238", opacity: 0.12, blur: 10, offset: 3, angle: 90 }, objectName: `a${k}_up_md${i}` });
    iconCircle(s, ic, x + 0.2, y + 0.2, 0.6, `a${k}_up_mi${i}`, star ? C.gold : C.crimson2);
    txt(s, h, { x: x + 0.9, y: y + 0.2, w: 1.9, h: 0.6, valign: "middle", fontSize: 15, bold: true, color: C.crimson2, objectName: `a${k}_up_mh${i}` });
    txt(s, p, { x: x + 0.2, y: y + 0.95, w: 2.5, h: 1.15, fontSize: 12.5, color: C.muted, objectName: `a${k}_up_mp${i}` });
    if (star) {
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + 1.65, y: y - 0.18, w: 1.1, h: 0.34, rectRadius: 0.1, fill: { color: C.gold }, line: { color: C.gold }, objectName: `a${k}_up_tag` });
      txt(s, "Ustuvor", { x: x + 1.65, y: y - 0.18, w: 1.1, h: 0.34, align: "center", valign: "middle", fontSize: 11, bold: true, color: C.white, objectName: `a${k}_up_tagt` });
    }
  });
  txt(s, "Ro‘yxatdan o‘tishning o‘zi bandlikni kafolatlamaydi — ayollar uchun real va takroriy buyurtmalar oqimi kerak (BEGOYIM Hamkor).", { x: 0.6, y: 6.55, w: 12.13, h: 0.35, align: "center", fontSize: 13, italic: true, color: C.muted, objectName: "a9_fade_note" });
  notes(s, "Respublika darajasiga olib chiqadigan 7 ta yo‘nalish: AI kasb maslahatchisi, hududiy bandlik xaritasi, milliy mahsulotlar bozori, Academy, HIMOYA, mikro-tadbirkorlik yordamchisi va BEGOYIM Hamkor. Hamkor modulini alohida ta’kidlayman: maktablar, bog‘chalar, korxonalar va mehmonxonalar buyurtma joylashtiradi — bu yakka buyurtmalardan tashqari muntazam daromad yaratadi. Bugun barcha modullarni moliyalashtirishni so‘ramaymiz — avval MVP pilotdan o‘tadi.");

  // ================= 17. HAMKORLIK MODELI =================
  s = pres.addSlide({ masterName: "LIGHT" });
  header(s, "③ Nima uchun qo‘llab-quvvatlashimiz kerak?", "Aniq hamkorlik modeli — yangi tashkilot emas");
  [["people", "Mahalla", "Hunarli va ish izlayotgan ayollarni aniqlash, ularni platformaga jalb etish."],
   ["bank", "Vazirlik va bo‘limlar", "Pilot hududlarni belgilash, bandlik va ijtimoiy himoya mexanizmlari bilan uyg‘unlashtirish."],
   ["heart", "Xotin-qizlar faollari", "Ayollarga platformadan foydalanishda amaliy yordam berish."],
   ["laptop", "BEGOYIM jamoasi", "Platformani ishlab chiqish, o‘qitish, texnik xizmat va tahlil."],
   ["store", "Tashkilot va tadbirkorlar", "BEGOYIM Hamkor orqali muntazam buyurtmalar, hamkorlik va mentorlik."]].forEach(([ic, h, p], i) => {
    const row = i < 3 ? 0 : 1, col = row === 0 ? i : i - 3;
    const x = row === 0 ? 0.6 + col * 4.1 : 2.65 + col * 4.1, y = row === 0 ? 1.9 : 4.35, k = 2 + i;
    card(s, x, y, 3.9, 2.2, `a${k}_up_p${i}`);
    iconCircle(s, ic, x + 0.25, y + 0.25, 0.65, `a${k}_up_pi${i}`);
    txt(s, h, { x: x + 1.05, y: y + 0.25, w: 2.7, h: 0.65, valign: "middle", fontSize: 16, bold: true, color: C.crimson2, objectName: `a${k}_up_ph${i}` });
    txt(s, p, { x: x + 0.25, y: y + 1.05, w: 3.45, h: 1.0, fontSize: 14, color: C.muted, objectName: `a${k}_up_pp${i}` });
  });
  notes(s, "Uchinchi savol: nima uchun qo‘llab-quvvatlash kerak? Chunki aniq hamkorlik modeli bor: mahalla ayollarni aniqlaydi, Oila va xotin-qizlar bo‘limi pilot hududni belgilaydi va tashkiliy ko‘mak beradi, faollar ayollarga yordam beradi, BEGOYIM jamoasi texnik tomonni ta’minlaydi, tadbirkorlar buyurtma va mentorlik beradi.");

  // ================= RESPUBLIKA PILOT DASTURI =================
  s = pres.addSlide({ masterName: "DARK" });
  header(s, "Respublika pilot dasturi · 6 oylik sinov modeli (taklif)", "Taklif etilayotgan maqsadli ko‘rsatkichlar", true);
  [["3", "ta", "pilot hudud: Buxoro, Samarqand, Toshkent"], ["15", "ta", "tanlab olinadigan mahalla"], ["1 500", "nafar", "platformaga jalb etish maqsad qilingan ayol"], ["300", "nafar", "kamida bitta yakunlangan buyurtma olishi rejalashtirilgan ayol"]].forEach(([n, u, l], i) => {
    const x = 0.6 + i * 3.08, k = 2 + i;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 2.0, w: 2.88, h: 2.9, rectRadius: 0.15, fill: { color: "FFFFFF", transparency: 90 }, line: { color: C.gold, width: 1 }, objectName: `a${k}_zoom_sbox${i}` });
    txt(s, n, { x, y: 2.15, w: 2.88, h: 1.15, align: "center", valign: "middle", fontFace: HEAD, fontSize: 54, bold: true, color: C.goldSoft, objectName: `a${k}_zoom_sn${i}` });
    txt(s, u, { x, y: 3.3, w: 2.88, h: 0.4, align: "center", fontSize: 18, bold: true, color: C.white, objectName: `a${k}_zoom_su${i}` });
    txt(s, l, { x: x + 0.2, y: 3.75, w: 2.48, h: 1.0, align: "center", fontSize: 14, color: "FFE0C7", objectName: `a${k}_zoom_sl${i}` });
  });
  txt(s, "ⓘ Raqamlar loyiha maqsadlari bo‘lib, tasdiqlangan natijalar emas. Ular hamkorlar va resurslar asosida kelishiladi.", { x: 0.6, y: 5.15, w: 12.13, h: 0.5, align: "center", fontSize: 14, color: "FFE0C7", objectName: "a6_fade_note" });
  txt(s, "“Bir ayol — bir imkoniyat. Bir mahalla — yuzlab yangi istiqbollar.”", { x: 0.6, y: 5.85, w: 12.13, h: 0.6, align: "center", fontFace: HEAD, fontSize: 22, italic: true, color: C.goldSoft, objectName: "a7_fade_quote" });
  notes(s, "BEGOYIMni dastlab tanlangan mahallalarda sinovdan o‘tkazishni taklif etamiz: 3 ta pilot hudud — Buxoro, Samarqand, Toshkent; 15 ta mahalla; 1 500 nafar ayolni jalb etish va kamida 300 nafar ayolning yakunlangan buyurtma olishi. Bu raqamlar maqsad, tasdiqlangan natija emas — hamkorlar va resurslar asosida kelishiladi.");

  // ================= PILOT BOSQICHLARI VA SO'ROV =================
  s = pres.addSlide({ masterName: "LIGHT" });
  header(s, "Pilot bosqichlari", "6 oy — uch bosqich");
  [["flag", "1–2-oy", "Tayyorlash va jalb etish", "Mahallalarni tanlash, xotin-qizlar faollarini o‘qitish, ayollarni ro‘yxatga olish, xizmatlar katalogi"],
   ["people", "3–4-oy", "Buyurtmalar va bandlik", "Xizmatlarni mijozlar bilan bog‘lash, korxonalar bilan hamkorlik, dastlabki buyurtmalar"],
   ["line", "5–6-oy", "Baholash va kengaytirish", "Buyurtmalar, daromad, faollik va qoniqishni tahlil qilish; keyingi hududlarni belgilash"]].forEach(([ic, t, h, p], i) => {
    const x = 0.6 + i * 4.1, k = 2 + i;
    card(s, x, 1.85, 3.9, 2.75, `a${k}_up_ph${i}`);
    iconCircle(s, ic, x + 0.25, 2.05, 0.7, `a${k}_up_phi${i}`, i === 2 ? C.gold : C.crimson2);
    txt(s, t, { x: x + 1.1, y: 2.05, w: 2.6, h: 0.35, fontSize: 14, bold: true, color: C.gold, objectName: `a${k}_up_pht${i}` });
    txt(s, h, { x: x + 1.1, y: 2.38, w: 2.65, h: 0.4, fontSize: 16, bold: true, color: C.crimson2, objectName: `a${k}_up_phh${i}` });
    txt(s, p, { x: x + 0.25, y: 3.0, w: 3.45, h: 1.5, fontSize: 13.5, color: C.muted, objectName: `a${k}_up_php${i}` });
  });
  card(s, 0.6, 4.8, 12.13, 1.95, "a5_up_ask", C.tint);
  txt(s, "Vazirlikdan so‘raymiz", { x: 0.9, y: 4.92, w: 11.5, h: 0.4, fontFace: HEAD, fontSize: 18, bold: true, color: C.crimson2, objectName: "a5_up_askh" });
  txt(s, [
    { text: "Buxoro, Samarqand va Toshkentda pilot mahallalarni belgilash", options: { bullet: true, breakLine: true } },
    { text: "Oila va xotin-qizlar bo‘limlari bilan hamkorlik mexanizmini yo‘lga qo‘yish", options: { bullet: true, breakLine: true } },
    { text: "Mahallalardagi xotin-qizlar faollarini jalb etish", options: { bullet: true, breakLine: true } },
    { text: "Platforma samaradorligini birgalikda baholashda tashkiliy ko‘mak", options: { bullet: true } },
  ], { x: 0.9, y: 5.32, w: 11.5, h: 1.35, fontSize: 14.5, color: C.ink, paraSpaceAfter: 2, objectName: "a6_fade_asklist" });
  notes(s, "Pilot uch bosqichda: 1–2-oy — tayyorlash va jalb etish; 3–4-oy — buyurtmalar va bandlik; 5–6-oy — baholash va kengaytirish. Vazirlikdan so‘raymiz: pilot hududlarni belgilash, Oila va xotin-qizlar bo‘limlari bilan hamkorlik mexanizmi, mahalla xotin-qizlar faollarini jalb etish va samaradorlikni birgalikda baholash. Biz yangi tashkilot yoki murakkab boshqaruv tizimini emas, mavjud mahalla va xotin-qizlarni qo‘llab-quvvatlash tizimining samaradorligini raqamli texnologiyalar bilan oshirishni taklif qilamiz.");

  // ================= MUVAFFAQIYAT KO'RSATKICHLARI =================
  s = pres.addSlide({ masterName: "LIGHT" });
  header(s, "Natija qanday o‘lchanadi?", "Muvaffaqiyatning asosiy ko‘rsatkichlari");
  [["user", "Faol xizmat ko‘rsatuvchilar"], ["flag", "Birinchi buyurtmasini olgan ayollar"], ["line", "Takroriy buyurtmalar"], ["money", "Yakunlangan buyurtmalar qiymati"], ["heart", "Foydalanuvchilar qoniqishi"]].forEach(([ic, t], i) => {
    const x = 0.6 + i * 2.47, k = 2 + i;
    card(s, x, 2.0, 2.27, 2.6, `a${k}_up_kc${i}`);
    iconCircle(s, ic, x + 0.71, 2.3, 0.85, `a${k}_up_ki${i}`, i % 2 ? C.gold : C.crimson2);
    txt(s, t, { x: x + 0.15, y: 3.35, w: 1.97, h: 1.1, align: "center", fontSize: 15, bold: true, color: C.ink, objectName: `a${k}_up_kt${i}` });
  });
  card(s, 0.6, 4.95, 12.13, 1.6, "a7_up_note", C.tint);
  txt(s, [{ text: "Halol hisob: ", options: { bold: true, color: C.crimson2 } }, { text: "platformadagi buyurtma qiymati tasdiqlangan shaxsiy daromad bilan tenglashtirilmaydi. Bandlik ro‘yxatdagi ko‘rsatkichlar bilan emas, real buyurtmalar va iqtisodiy natijalar asosida baholanadi.", options: { color: C.ink } }],
    { x: 0.9, y: 4.95, w: 11.5, h: 1.6, valign: "middle", fontSize: 16, objectName: "a7_up_notet" });
  notes(s, "Loyihaning muvaffaqiyati quyidagicha o‘lchanadi: faol xizmat ko‘rsatuvchilar, birinchi buyurtmasini olgan ayollar, takroriy buyurtmalar, yakunlangan buyurtmalar qiymati va foydalanuvchilar qoniqishi. Muhim: platformadagi buyurtma qiymati tasdiqlangan shaxsiy daromad bilan tenglashtirilmaydi.");

  // ================= MUROJAAT =================
  s = pres.addSlide({ masterName: "DARK" });
  txt(s, "Hurmatli rahbarlar!", { x: 0.8, y: 0.9, w: 11.7, h: 0.9, align: "center", valign: "middle", fontFace: HEAD, fontSize: 34, bold: true, color: C.goldSoft, objectName: "a1_fade_h" });
  txt(s, "BEGOYIMni dastlab Buxoro, Samarqand va Toshkentdagi tanlangan mahallalarda pilot tariqasida joriy etishni taklif qilamiz. Maqsadimiz — yangi hisobot tizimi emas, ayollarning real daromadi, iqtisodiy mustaqilligi va ijtimoiy himoyasiga xizmat qiladigan raqamli yechimni amaliyotga tatbiq etish.", { x: 1.2, y: 1.95, w: 10.9, h: 1.6, align: "center", fontSize: 19, color: C.white, objectName: "a2_up_p" });
  txt(s, "“Ayolga imkoniyat yaratsak, bir oilaning iqtisodiy mustaqilligiga yo‘l ochamiz.”", { x: 1.0, y: 3.8, w: 11.3, h: 1.3, align: "center", valign: "middle", fontFace: HEAD, fontSize: 28, italic: true, bold: true, color: C.goldSoft, objectName: "a3_zoom_q" });
  txt(s, "BEGOYIMni birgalikda har bir mahallaga, har bir imkoniyat izlayotgan ayolga yetkazaylik!", { x: 1.0, y: 5.45, w: 11.3, h: 0.6, align: "center", fontSize: 19, bold: true, color: "FFE0C7", objectName: "a4_fade_l" });
  notes(s, "Hurmatli rahbarlar! BEGOYIMni respublika miqyosida rivojlantirish uchun uni dastlab Buxoro, Samarqand va Toshkent hududlaridagi tanlangan mahallalarda pilot tariqasida joriy etishni taklif qilamiz. Buning uchun Oila va xotin-qizlar bo‘limlari bilan hamkorlik mexanizmini yo‘lga qo‘yish, mahallalardagi xotin-qizlar faollarini jalb etish va platformaning amaliy samaradorligini birgalikda baholashda tashkiliy ko‘mak so‘raymiz. BEGOYIMni birgalikda har bir mahallaga, har bir imkoniyat izlayotgan ayolga yetkazaylik!");

  // ================= FINAL =================
  s = pres.addSlide({ masterName: "LIGHT" });
  s.addImage({ path: A("logo.png"), x: 5.08, y: 0.55, w: 3.17, h: 2.56, objectName: "a1_zoom_logo" });
  txt(s, "BEGOYIM — har bir ayolga imkoniyat, har bir oilaga farovonlik sari qadam!", { x: 0.6, y: 3.25, w: 12.13, h: 0.7, align: "center", fontFace: HEAD, fontSize: 23, bold: true, color: C.crimson2, objectName: "a2_up_h" });
  const eq = [["Mahalla", 1.0, 1.9], ["+", 2.95, 0.4], ["Oila va xotin-qizlar bo‘limi", 3.4, 3.6], ["+", 7.05, 0.4], ["Raqamli texnologiya", 7.5, 2.8], ["=", 10.35, 0.4]];
  eq.forEach(([t, x, w], i) => {
    if (t.length > 1) s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 4.25, w, h: 0.6, rectRadius: 0.12, fill: { color: C.white }, line: { color: C.gold, width: 1.5 }, objectName: `a${3 + i}_zoom_eqb${i}` });
    txt(s, t, { x, y: 4.25, w, h: 0.6, align: "center", valign: "middle", fontSize: t.length > 1 ? 16 : 26, bold: true, color: t.length > 1 ? C.crimson2 : C.gold, objectName: `a${3 + i}_zoom_eq${i}` });
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 10.8, y: 4.15, w: 1.9, h: 0.8, rectRadius: 0.12, fill: { color: C.crimson2 }, line: { color: C.crimson2 }, objectName: "a9_zoom_res" });
  txt(s, "Ayollar bandligi va farovonligi", { x: 10.8, y: 4.15, w: 1.9, h: 0.8, align: "center", valign: "middle", fontSize: 13, bold: true, color: C.white, objectName: "a9_zoom_rest" });
  txt(s, "Mahalla tizimini kuchaytiruvchi, natijasi o‘lchanadigan, respublika bo‘ylab kengaytiriladigan ijtimoiy innovatsiya", { x: 0.6, y: 5.2, w: 12.13, h: 0.55, align: "center", fontSize: 16, bold: true, color: C.ink, objectName: "a10_up_b" });
  txt(s, "Ayoldan ayolga — imkoniyat va ko‘mak!", { x: 0.8, y: 5.95, w: 11.7, h: 0.55, align: "center", fontFace: HEAD, fontSize: 22, italic: true, color: C.crimson2, objectName: "a11_up_s" });
  notes(s, "Ishonamizki, BEGOYIM kelajakda minglab ayollarning o‘z hunari va salohiyati orqali iqtisodiy mustaqillikka erishishiga xizmat qiladigan milliy platformaga aylanishi mumkin. BEGOYIM — har bir ayolga imkoniyat, har bir oilaga farovonlik sari qadam! E’tiboringiz uchun rahmat!");

  // ================= 21. MUALLIF / RAHMAT =================
  s = pres.addSlide({ masterName: "LIGHT" });
  s.addImage({ path: A("author.jpg"), x: 0.9, y: 0.75, w: 4.75, h: 5.97, objectName: "a1_zoom_photo" });
  txt(s, "LOYIHA MUALLIFI", { x: 6.3, y: 1.3, w: 6.4, h: 0.35, fontSize: 12, bold: true, color: C.gold, charSpacing: 3, objectName: "a2_up_k" });
  txt(s, AUTHOR, { x: 6.3, y: 1.7, w: 6.4, h: 1.3, fontFace: HEAD, fontSize: 34, bold: true, color: C.ink, objectName: "a2_up_n" });
  txt(s, "BEGOYIM — ayollar bandligi va farovonligi raqamli ekotizimi g‘oyasi, konsepsiyasi va loyihasi muallifi.", { x: 6.3, y: 3.05, w: 6.4, h: 0.95, fontSize: 16, color: C.muted, objectName: "a3_up_d" });
  txt(s, "E’tiboringiz uchun rahmat!", { x: 6.3, y: 4.2, w: 6.4, h: 0.7, fontFace: HEAD, fontSize: 30, bold: true, italic: true, color: C.crimson2, objectName: "a4_zoom_t" });
  txt(s, [{ text: `© 2026 ${AUTHOR}. Barcha huquqlar himoyalangan.`, options: { bold: true, color: C.crimson2, breakLine: true } },
    { text: "BEGOYIM nomi, logotipi, konsepsiyasi va platformasi muallifning intellektual mulki hisoblanadi.", options: { color: C.muted } }],
    { x: 6.3, y: 5.3, w: 6.4, h: 1.1, fontSize: 12, objectName: "a5_fade_c" });
  notes(s, "E’tiboringiz uchun rahmat! Savollaringizga javob berishga tayyorman. Kerak bo‘lsa, platformani jonli namoyish qilaman.");

  // ================= ILOVA: SAVOLLARGA JAVOBLAR =================
  s = pres.addSlide({ masterName: "LIGHT" });
  header(s, "Ilova · ehtimoliy savollar", "Savollarga tayyor javoblar");
  const qa = [
    ["Mavjud bandlik tizimlaridan farqi?", "E’lon emas, to‘liq jarayon: mahalla tasdig‘i, AI moslashtirish, buyurtmadan baho va daromad hisobigacha; bo‘lim uchun real ko‘rsatkichlar."],
    ["Buyurtmalar qayerdan keladi?", "Mahalla va hudud aholisi, mahalliy tadbirkorlar hamda BEGOYIM Hamkor orqali tashkilotlar (maktab, bog‘cha, korxona, mehmonxona)."],
    ["Respublika bo‘ylab ishlay oladimi?", "Ha: viloyat–tuman–mahalla tuzilmasi va 14 hudud ma’lumotnomasi tayyor; pilot natijalariga qarab bosqichma-bosqich kengaytiriladi."],
    ["Maxfiylik qanday ta’minlanadi?", "Psixologik murojaat mazmuni faqat mutaxassisga ko‘rinadi (MVP’da ishlaydi); HIMOYA uchun alohida audit, rozilik va mustaqil mas’ul."],
    ["Muvaffaqiyat qanday o‘lchanadi?", "Faol ijrochilar, birinchi va takroriy buyurtmalar, yakunlangan buyurtmalar qiymati, qoniqish. Buyurtma qiymati ≠ tasdiqlangan daromad."],
  ];
  qa.forEach(([q, a], i) => {
    const col = i < 3 ? 0 : 1, row = col === 0 ? i : i - 3;
    const x = 0.6 + col * 6.17, y = 1.85 + row * 1.6, k = 2 + i;
    card(s, x, y, 5.96, 1.45, `a${k}_up_qa${i}`);
    txt(s, q, { x: x + 0.25, y: y + 0.12, w: 5.5, h: 0.4, fontSize: 15, bold: true, color: C.crimson2, objectName: `a${k}_up_q${i}` });
    txt(s, a, { x: x + 0.25, y: y + 0.52, w: 5.5, h: 0.85, fontSize: 12.5, color: C.ink, objectName: `a${k}_up_a${i}` });
  });
  notes(s, "Zaxira slayd — savol-javob vaqtida kerak bo‘lsa oching. Muhim tavsiya: bugun barcha modullarni moliyalashtirishni so‘ramang; avval bandlik, buyurtmalar, mahalla hamkorligi va natijalarni baholashga qaratilgan MVP pilotiga kelishuvga erishing. HIMOYA — ikkinchi yo‘nalish, puxta huquqiy va xavfsizlik tayyorgarligi bilan.");

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  await pres.writeFile({ fileName: OUT });
  console.log("written", OUT);
})();
