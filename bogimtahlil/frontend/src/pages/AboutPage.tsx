import { PageHeader } from "@/components/PageHeader";
import { MedicalDisclaimer } from "@/components/Disclaimer";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const PIPELINE = [
  "Rentgen tasvirini yuklash",
  "Tasvirning texnik yaroqliligini tekshirish (format, hajm, yaxlitlik, o‘lcham)",
  "Dastlabki ishlov berish: kulrang format, kesmasdan 224×224, me’yorlashtirish",
  "O‘qitilgan neyron tarmoq (ResNet-18 yoki EfficientNet-B0) orqali KL0–KL4 bashorati",
  "Grad-CAM yordamida e’tibor xaritasini yaratish",
  "Natijalarni izohlash va PDF hisobot tayyorlash",
];

export default function AboutPage() {
  return (
    <div className="container space-y-6 pb-12">
      <PageHeader title="Dastur haqida" description="Bo‘g‘imTahlil 1.0 — “Aniq tahlil sari aqlli qadam!”" />
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Maqsad</CardTitle></CardHeader>
          <CardContent className="space-y-3 text-sm leading-relaxed">
            <p>
              Tizza bo‘g‘imining rentgen tasvirlarini sun’iy intellekt yordamida avtomatik tahlil qilish, osteoartritga xos rentgenologik
              o‘zgarishlarni Kellgren–Lawrence tasnifi asosida baholash va natijalarni qulay shaklda taqdim etish.
            </p>
            <p>Dasturdan foydalanish maqsadi: ilmiy tadqiqot, dastlabki avtomatlashtirilgan tasvir tahlili va bitiruv malakaviy ishining amaliy natijasi.</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Ishlash zanjiri</CardTitle></CardHeader>
          <CardContent>
            <ol className="space-y-2 text-sm">
              {PIPELINE.map((p, i) => (
                <li key={p} className="flex gap-3"><span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-accent-soft text-xs font-bold text-primary">{i + 1}</span>{p}</li>
              ))}
            </ol>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Maxfiylik va xavfsizlik</CardTitle></CardHeader>
          <CardContent>
            <ul className="list-disc space-y-1.5 pl-5 text-sm leading-relaxed">
              <li>Ro‘yxatdan o‘tish talab qilinmaydi; tahlillar anonim brauzer sessiyasiga bog‘lanadi.</li>
              <li>Bemorning ismi, telefon raqami, pasport ma’lumoti va asl fayl nomi saqlanmaydi.</li>
              <li>Tasvir metama’lumotlari (EXIF) qayta kodlash orqali olib tashlanadi.</li>
              <li>Boshqa sessiya tahlillariga kirish taqiqlangan.</li>
              <li>Tasvirlar, xaritalar va hisobotlar 24 soatdan so‘ng avtomatik o‘chiriladi; istalgan payt qo‘lda o‘chirish mumkin.</li>
              <li>Yuklangan fayllar serverda format, hajm va yaxlitlik bo‘yicha tekshiriladi.</li>
            </ul>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Texnologiyalar</CardTitle></CardHeader>
          <CardContent className="text-sm leading-relaxed">
            <p><b>Interfeys:</b> React, TypeScript, Vite, Tailwind CSS, shadcn/ui, Lucide, Recharts, Axios, React Router.</p>
            <p className="mt-2"><b>Server:</b> Python, FastAPI, Uvicorn, Pydantic, SQLAlchemy, Alembic, SQLite.</p>
            <p className="mt-2"><b>Sun’iy intellekt:</b> PyTorch, torchvision (ResNet-18, EfficientNet-B0), OpenCV, Pillow, NumPy, pandas, scikit-learn, Grad-CAM.</p>
            <p className="mt-2"><b>Hujjatlar va sinov:</b> ReportLab, Matplotlib, pytest, Vitest, Docker.</p>
          </CardContent>
        </Card>
      </div>
      <MedicalDisclaimer />
    </div>
  );
}
