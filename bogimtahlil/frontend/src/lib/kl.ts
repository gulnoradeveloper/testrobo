/** KL darajalari: o‘zbekcha nomlar (TT 8-bo‘lim) va vizual toifa ranglari.
 * Ranglar faqat darajalarni ajratib ko‘rsatish uchun — klinik xavf bahosi emas. */
export const KL_LEVELS = [
  { grade: 0, label: "KL0", title: "Aniq rentgenologik belgilar yo‘q", short: "Belgilar yo‘q", color: "#5B8DB8" },
  { grade: 1, label: "KL1", title: "Shubhali o‘zgarishlar", short: "Shubhali", color: "#4A7FB0" },
  { grade: 2, label: "KL2", title: "Yengil o‘zgarishlar", short: "Yengil", color: "#2F6CA6" },
  { grade: 3, label: "KL3", title: "O‘rtacha o‘zgarishlar", short: "O‘rtacha", color: "#1F5791" },
  { grade: 4, label: "KL4", title: "Og‘ir o‘zgarishlar", short: "Og‘ir", color: "#123A63" },
] as const;

export const KL_DESCRIPTIONS: Record<number, string> = {
  0: "Osteoartritga xos rentgenologik belgilar aniqlanmaydi.",
  1: "Bo‘g‘im yorig‘ining shubhali torayishi va osteofit lablanishi ehtimoli.",
  2: "Aniq osteofitlar va bo‘g‘im yorig‘i torayishi ehtimoli.",
  3: "Bir nechta o‘rtacha osteofitlar, bo‘g‘im yorig‘ining aniq torayishi, subxondral skleroz.",
  4: "Yirik osteofitlar, bo‘g‘im yorig‘ining keskin torayishi, kuchli skleroz va deformatsiya.",
};
