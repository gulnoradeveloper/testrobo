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
  txt(s, "Ayollar bandligi va farovonligi raqamli ekotizimi", { x: 6.6, y: 1.6, w: 6.1, h: 1.3, fontFace: HEAD, fontSize: 32, bold: true, color: C.ink, objectName: "a2_up_title" });
  txt(s, "Ayoldan ayolga — imkoniyat va ko‘mak.", { x: 6.6, y: 3.05, w: 6.1, h: 0.6, fontFace: HEAD, fontSize: 24, italic: true, color: C.crimson2, objectName: "a3_up_slogan" });
  txt(s, [
    { text: "Loyiha muallifi: ", options: { color: C.muted } },
    { text: AUTHOR, options: { bold: true, color: C.ink } },
  ], { x: 6.6, y: 4.2, w: 6.1, h: 0.45, fontSize: 18, objectName: "a4_fade_author" });
  txt(s, "Ko‘nikmani — xizmatga, xizmatni — daromadga aylantiramiz", { x: 6.6, y: 4.75, w: 6.1, h: 0.45, fontSize: 16, color: C.muted, objectName: "a4_fade_tagline" });
  notes(s, "Assalomu alaykum, hurmatli hokimiyat va Oila va xotin-qizlar bo‘limi vakillari! Bugun sizlarga BEGOYIM — ayollar bandligi va farovonligi raqamli ekotizimi loyihasini taqdim etaman. Loyihaning asosiy g‘oyasi: ayollarning mavjud ko‘nikmalarini daromadga aylantirish.");

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

  // ================= 4. MUAMMO BO'LIMI =================
  s = pres.addSlide({ masterName: "DARK" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 4.4, y: 1.7, w: 4.55, h: 0.6, rectRadius: 0.3, fill: { color: "FFFFFF", transparency: 88 }, line: { color: "F6E7C8", width: 1 }, objectName: "a1_fade_qpill" });
  txt(s, "① Qanday muammoni hal qiladi?", { x: 4.4, y: 1.7, w: 4.55, h: 0.6, align: "center", valign: "middle", fontSize: 18, bold: true, color: C.goldSoft, objectName: "a1_fade_qtext" });
  txt(s, [{ text: "Bugun hunarli ayollar oldida", options: { color: C.white, breakLine: true } }, { text: "6 ta to‘siq bor", options: { color: C.goldSoft } }],
    { x: 0.8, y: 2.7, w: 11.7, h: 2.2, align: "center", valign: "middle", fontFace: HEAD, fontSize: 48, bold: true, objectName: "a2_zoom_big" });
  notes(s, "Birinchi savol: bu loyiha qanday muammoni hal qiladi? Biz hunarli ayollar oldidagi oltita asosiy to‘siqni aniqladik.");

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

  // ================= 9. UYDAN TURIB =================
  s = pres.addSlide({ masterName: "LIGHT" });
  header(s, "Ish o‘rni faqat korxonada yaratilmaydi", "Uyidan chiqmagan holda ham — xizmat va daromad");
  [["house", "O‘z uyidan xizmat ko‘rsatadi"], ["mobile", "Platforma orqali buyurtma oladi"], ["money", "Oilaviy daromadini oshiradi"]].forEach(([ic, t], i) => {
    iconCircle(s, ic, 0.6, 2.2 + i * 1.25, 0.85, `a${2 + i}_left_r${i}`);
    txt(s, t, { x: 1.7, y: 2.2 + i * 1.25, w: 4.6, h: 0.85, valign: "middle", fontSize: 21, bold: true, color: C.ink, objectName: `a${2 + i}_left_rt${i}` });
  });
  for (const [i, [f, x, y, w, h]] of [["pishiriq_big.jpg", 6.7, 1.9, 3.0, 2.3], ["milliy-kiyim.jpg", 9.85, 1.9, 2.88, 2.3], ["bola_big.jpg", 6.7, 4.35, 2.2, 2.3], ["masofaviy.jpg", 9.05, 4.35, 3.68, 2.3]].entries())
    await photo(s, V("photos/" + f), x, y, w, h, `a${5 + i}_zoom_ph${i}`);
  notes(s, "Ish o‘rni faqat korxonada yaratilmaydi. Ayol uyidan chiqmagan holda xizmat ko‘rsatadi, buyurtma oladi va oilaviy daromadini oshiradi — farzandlar va ro‘zg‘or yonida.");

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
  txt(s, "Mahalla imkoniyatga ega ayollarni aniqlaydi, BEGOYIM esa ularni mijozlar bilan bog‘laydi.", { x: 1.9, y: 5.6, w: 9.6, h: 0.95, valign: "middle", fontSize: 18, color: "FFE9CF", objectName: "a5_up_boxt" });
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

  // ================= 16. PILOT KO'RSATKICHLAR =================
  s = pres.addSlide({ masterName: "DARK" });
  header(s, "Pilot bosqich", "Taklif etilayotgan maqsadli ko‘rsatkichlar", true);
  [["5", "ta", "pilot mahalla"], ["500", "nafar", "jalb etiladigan ayol"], ["200", "nafar", "xizmat joylashtiruvchi ayol"], ["100", "nafar", "birinchi buyurtmasini olishi maqsad qilingan ayol"]].forEach(([n, u, l], i) => {
    const x = 0.6 + i * 3.08, k = 2 + i;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 2.0, w: 2.88, h: 2.9, rectRadius: 0.15, fill: { color: "FFFFFF", transparency: 90 }, line: { color: C.gold, width: 1 }, objectName: `a${k}_zoom_sbox${i}` });
    txt(s, n, { x, y: 2.15, w: 2.88, h: 1.15, align: "center", valign: "middle", fontFace: HEAD, fontSize: 60, bold: true, color: C.goldSoft, objectName: `a${k}_zoom_sn${i}` });
    txt(s, u, { x, y: 3.3, w: 2.88, h: 0.4, align: "center", fontSize: 18, bold: true, color: C.white, objectName: `a${k}_zoom_su${i}` });
    txt(s, l, { x: x + 0.2, y: 3.75, w: 2.48, h: 1.0, align: "center", fontSize: 14, color: "FFE0C7", objectName: `a${k}_zoom_sl${i}` });
  });
  txt(s, "ⓘ Bu erishilgan natija emas — dastlabki pilot bosqich uchun maqsad. Yakuniy ko‘rsatkichlar pilot hududlar, byudjet va hamkorlar imkoniyatlari asosida belgilanadi.", { x: 0.6, y: 5.15, w: 12.13, h: 0.65, align: "center", fontSize: 14, color: "FFE0C7", objectName: "a6_fade_note" });
  txt(s, "“Bir ayol — bir imkoniyat. Bir mahalla — yuzlab yangi istiqbollar.”", { x: 0.6, y: 5.9, w: 12.13, h: 0.6, align: "center", fontFace: HEAD, fontSize: 22, italic: true, color: C.goldSoft, objectName: "a7_fade_quote" });
  notes(s, "Pilot bosqich uchun taklif etilayotgan maqsadlar: 5 ta pilot mahalla, 500 nafar jalb etiladigan ayol, 200 nafar xizmat joylashtiruvchi va 100 nafar birinchi buyurtmasini olishi maqsad qilingan ayol. Bu erishilgan natija emas — maqsad; yakuniy raqamlar hudud, byudjet va hamkorlar bilan kelishiladi.");

  // ================= 17. HAMKORLIK MODELI =================
  s = pres.addSlide({ masterName: "LIGHT" });
  header(s, "③ Nima uchun qo‘llab-quvvatlashimiz kerak?", "Aniq hamkorlik modeli");
  [["people", "Mahalla", "Hunarli va ish izlayotgan ayollarni aniqlash, ularni platformaga jalb etish."],
   ["bank", "Oila va xotin-qizlar bo‘limi", "Pilot hududni belgilash, tashkiliy ko‘mak va hamkorlarni birlashtirish."],
   ["heart", "Xotin-qizlar faollari", "Ayollarga platformadan foydalanishda amaliy yordam berish."],
   ["laptop", "BEGOYIM jamoasi", "Platformani ishlab chiqish, o‘qitish, texnik xizmat va tahlil."],
   ["store", "Mahalliy tadbirkorlar", "Xizmatlarga buyurtma berish, hamkorlik va mentorlik."]].forEach(([ic, h, p], i) => {
    const row = i < 3 ? 0 : 1, col = row === 0 ? i : i - 3;
    const x = row === 0 ? 0.6 + col * 4.1 : 2.65 + col * 4.1, y = row === 0 ? 1.9 : 4.35, k = 2 + i;
    card(s, x, y, 3.9, 2.2, `a${k}_up_p${i}`);
    iconCircle(s, ic, x + 0.25, y + 0.25, 0.65, `a${k}_up_pi${i}`);
    txt(s, h, { x: x + 1.05, y: y + 0.25, w: 2.7, h: 0.65, valign: "middle", fontSize: 16, bold: true, color: C.crimson2, objectName: `a${k}_up_ph${i}` });
    txt(s, p, { x: x + 0.25, y: y + 1.05, w: 3.45, h: 1.0, fontSize: 14, color: C.muted, objectName: `a${k}_up_pp${i}` });
  });
  notes(s, "Uchinchi savol: nima uchun qo‘llab-quvvatlash kerak? Chunki aniq hamkorlik modeli bor: mahalla ayollarni aniqlaydi, Oila va xotin-qizlar bo‘limi pilot hududni belgilaydi va tashkiliy ko‘mak beradi, faollar ayollarga yordam beradi, BEGOYIM jamoasi texnik tomonni ta’minlaydi, tadbirkorlar buyurtma va mentorlik beradi.");

  // ================= 18. TAKLIF / YO'L XARITASI =================
  s = pres.addSlide({ masterName: "LIGHT" });
  header(s, "Taklif", "Pilot bosqichni birgalikda boshlaymiz");
  [["flag", "Pilot mahallalarni belgilash", "Hudud va mas’ullarni tasdiqlash"],
   ["people", "Ayollarni aniqlash va o‘qitish", "Mahalla orqali ro‘yxat, platformadan foydalanish bo‘yicha o‘quv"],
   ["laptop", "Platformani ishga tushirish", "Xizmatlar joylanadi, buyurtmalar qabul qilinadi"],
   ["line", "Natijani tahlil va kengaytirish", "Dashboard ko‘rsatkichlari asosida keyingi hududlar"]].forEach(([ic, h, p], i) => {
    const x = 0.6 + i * 3.08, k = 2 + i;
    iconCircle(s, ic, x + 1.04, 1.95, 0.8, `a${k}_up_ri${i}`, i === 3 ? C.gold : C.crimson2);
    if (i < 3) s.addImage({ data: I.arrow.g, x: x + 2.55, y: 2.2, w: 0.45, h: 0.32, objectName: `a${k}_up_ra${i}` });
    txt(s, `${i + 1}-bosqich`, { x, y: 2.85, w: 2.88, h: 0.35, align: "center", fontSize: 12, bold: true, color: C.gold, objectName: `a${k}_up_rs${i}` });
    txt(s, h, { x, y: 3.2, w: 2.88, h: 0.65, align: "center", fontSize: 16, bold: true, color: C.ink, objectName: `a${k}_up_rh${i}` });
    txt(s, p, { x: x + 0.1, y: 3.85, w: 2.68, h: 0.85, align: "center", fontSize: 13, color: C.muted, objectName: `a${k}_up_rp${i}` });
  });
  card(s, 0.6, 4.95, 12.13, 1.75, "a6_up_ask", C.tint);
  txt(s, "Sizdan so‘raymiz", { x: 0.9, y: 5.08, w: 11.5, h: 0.4, fontFace: HEAD, fontSize: 18, bold: true, color: C.crimson2, objectName: "a6_up_askh" });
  txt(s, [
    { text: "Pilot hudud va mahallalarni ajratish", options: { bullet: true, breakLine: true } },
    { text: "Mahalla va Oila va xotin-qizlar bo‘limi mas’ullarini biriktirish", options: { bullet: true, breakLine: true } },
    { text: "Hamkorlar (tadbirkorlar, faollar)ni jalb etishda tashkiliy ko‘mak", options: { bullet: true } },
  ], { x: 0.9, y: 5.5, w: 11.5, h: 1.1, fontSize: 15, color: C.ink, paraSpaceAfter: 3, objectName: "a7_fade_asklist" });
  notes(s, "Taklifimiz: pilot bosqichni birgalikda boshlash. To‘rt bosqich: pilot mahallalarni belgilash, ayollarni aniqlash va o‘qitish, platformani ishga tushirish, natijalarni tahlil qilib kengaytirish. Sizdan so‘raymiz: pilot hudud ajratish, mas’ullarni biriktirish va hamkorlarni jalb etishda ko‘mak.");

  // ================= 19. MUROJAAT =================
  s = pres.addSlide({ masterName: "DARK" });
  txt(s, "Hurmatli mahalla hamda Oila va xotin-qizlar bo‘limi vakillari!", { x: 0.8, y: 0.9, w: 11.7, h: 1.0, align: "center", valign: "middle", fontFace: HEAD, fontSize: 30, bold: true, color: C.goldSoft, objectName: "a1_fade_h" });
  txt(s, "Keling, har bir mahallada o‘z hunari bilan daromad topishni istagan ayollarni aniqlaylik, ularni yagona raqamli platformada birlashtiraylik va bandlikni real natijaga aylantiraylik.", { x: 1.4, y: 2.1, w: 10.5, h: 1.4, align: "center", fontSize: 20, color: C.white, objectName: "a2_up_p" });
  txt(s, "“Ayolga imkoniyat yaratsak, bir oilaning iqtisodiy mustaqilligiga yo‘l ochamiz.”", { x: 1.0, y: 3.8, w: 11.3, h: 1.4, align: "center", valign: "middle", fontFace: HEAD, fontSize: 30, italic: true, bold: true, color: C.goldSoft, objectName: "a3_zoom_q" });
  txt(s, "Bugungi birinchi buyurtma — ertaga oila uchun barqaror daromad manbai.", { x: 1.0, y: 5.5, w: 11.3, h: 0.6, align: "center", fontSize: 18, color: "FFE0C7", objectName: "a4_fade_l" });
  notes(s, "Hurmatli vakillar! Keling, har bir mahallada hunari bilan daromad topishni istagan ayollarni aniqlaylik, yagona platformada birlashtiraylik va bandlikni real natijaga aylantiraylik. Ayolga imkoniyat yaratsak — bir oilaning iqtisodiy mustaqilligiga yo‘l ochamiz.");

  // ================= 20. FINAL =================
  s = pres.addSlide({ masterName: "LIGHT" });
  s.addImage({ path: A("logo.png"), x: 5.08, y: 0.55, w: 3.17, h: 2.56, objectName: "a1_zoom_logo" });
  txt(s, "Har bir mahallada imkoniyat, har bir ayolga daromad sari yo‘l!", { x: 0.8, y: 3.25, w: 11.7, h: 0.7, align: "center", fontFace: HEAD, fontSize: 28, bold: true, color: C.crimson2, objectName: "a2_up_h" });
  const eq = [["Mahalla", 1.0, 1.9], ["+", 2.95, 0.4], ["Oila va xotin-qizlar bo‘limi", 3.4, 3.6], ["+", 7.05, 0.4], ["Raqamli texnologiya", 7.5, 2.8], ["=", 10.35, 0.4]];
  eq.forEach(([t, x, w], i) => {
    if (t.length > 1) s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 4.25, w, h: 0.6, rectRadius: 0.12, fill: { color: C.white }, line: { color: C.gold, width: 1.5 }, objectName: `a${3 + i}_zoom_eqb${i}` });
    txt(s, t, { x, y: 4.25, w, h: 0.6, align: "center", valign: "middle", fontSize: t.length > 1 ? 16 : 26, bold: true, color: t.length > 1 ? C.crimson2 : C.gold, objectName: `a${3 + i}_zoom_eq${i}` });
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 10.8, y: 4.15, w: 1.9, h: 0.8, rectRadius: 0.12, fill: { color: C.crimson2 }, line: { color: C.crimson2 }, objectName: "a9_zoom_res" });
  txt(s, "Ayollar bandligi va farovonligi", { x: 10.8, y: 4.15, w: 1.9, h: 0.8, align: "center", valign: "middle", fontSize: 13, bold: true, color: C.white, objectName: "a9_zoom_rest" });
  txt(s, "BEGOYIM — har bir mahalladan boshlanadigan imkoniyat!", { x: 0.8, y: 5.25, w: 11.7, h: 0.55, align: "center", fontFace: HEAD, fontSize: 22, bold: true, color: C.ink, objectName: "a10_up_b" });
  txt(s, "Ayoldan ayolga — imkoniyat va ko‘mak!", { x: 0.8, y: 5.9, w: 11.7, h: 0.55, align: "center", fontFace: HEAD, fontSize: 22, italic: true, color: C.crimson2, objectName: "a11_up_s" });
  notes(s, "Xulosa: Mahalla + Oila va xotin-qizlar bo‘limi + raqamli texnologiya = ayollar bandligi va farovonligi. BEGOYIM — har bir mahalladan boshlanadigan imkoniyat.");

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

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  await pres.writeFile({ fileName: OUT });
  console.log("written", OUT);
})();
