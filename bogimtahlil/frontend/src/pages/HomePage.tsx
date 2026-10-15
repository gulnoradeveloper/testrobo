import { ArrowRight, BarChart3, Brain, FileText, History, Layers, ScanLine, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";
import { MedicalDisclaimer } from "@/components/Disclaimer";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { api } from "@/lib/api";
import { KL_DESCRIPTIONS, KL_LEVELS } from "@/lib/kl";
import { useAsync } from "@/lib/useAsync";
import { formatPercent } from "@/lib/utils";

const FEATURES = [
  { icon: ScanLine, title: "Rentgen tasvirlarini tahlil qilish", text: "Tizza bo‘g‘imining rentgen tasvirlariga avtomatik ishlov berish." },
  { icon: Brain, title: "Sun’iy intellekt yordamida baholash", text: "Osteoartritning rentgenologik darajasini bashorat qilish." },
  { icon: Layers, title: "Bo‘g‘imdagi o‘zgarishlarni ko‘rsatish", text: "Neyron tarmoq e’tibor qaratgan tasvir sohalarini rangli xaritada aks ettirish." },
  { icon: BarChart3, title: "Natijalarni tushuntirish", text: "Bashorat qilingan darajaning umumiy tavsifi va model cheklovlarini ko‘rsatish." },
  { icon: FileText, title: "Hisobot yaratish", text: "Tahlil natijalarini PDF shaklida saqlash." },
  { icon: History, title: "Tahlillarni saqlash", text: "Foydalanuvchi sessiyasidagi oldingi natijalarni vaqtinchalik ko‘rish." },
];

const STEPS = [
  "Tasvir yuklanadi.",
  "Sun’iy intellekt tasvirni qayta ishlaydi.",
  "Rentgenologik daraja baholanadi.",
  "Natijalar ko‘rsatiladi.",
  "Hisobot shakllantiriladi.",
];

const TECH = [
  ["Neyron tarmoq", "PyTorch · ResNet-18 · EfficientNet-B0"],
  ["Izohlanuvchanlik", "Grad-CAM e’tibor xaritasi"],
  ["Tasvirga ishlov berish", "OpenCV · Pillow · NumPy"],
  ["Server", "Python · FastAPI · SQLite"],
  ["Interfeys", "React · TypeScript · Tailwind CSS"],
  ["Hisobot", "ReportLab — A4 PDF"],
];

function ModelSnapshot() {
  const { data, loading, error } = useAsync(() => api.modelInfo(), []);
  if (loading) return <Spinner label="Model holati yuklanmoqda..." />;
  if (error || !data) return <p className="text-sm text-danger">{error?.message ?? "Server bilan bog‘lanib bo‘lmadi."}</p>;
  const test = data.metrics?.test;
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        {data.loaded && data.trained ? (
          <Badge variant="success">Model yuklangan</Badge>
        ) : data.loaded ? (
          <Badge variant="warning">O‘qitilmagan test modeli</Badge>
        ) : (
          <Badge variant="warning">Model tayyor emas</Badge>
        )}
        {data.version && <span className="text-xs text-muted">{data.architecture} · {data.version}</span>}
      </div>
      {test ? (
        <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[
            ["Accuracy", formatPercent(test.accuracy)],
            ["Macro F1", test.macro_f1.toFixed(3)],
            ["QWK", test.quadratic_weighted_kappa.toFixed(3)],
            ["Test tasvirlari", String(test.n_samples)],
          ].map(([k, v]) => (
            <div key={k} className="rounded-md bg-muted-bg p-3">
              <dt className="text-xs text-muted">{k}</dt>
              <dd className="text-lg font-semibold text-primary">{v}</dd>
            </div>
          ))}
        </dl>
      ) : (
        <p className="text-sm text-muted">
          {data.loaded ? "Mustaqil test metrikalari: hali baholanmagan." : data.status_message}
        </p>
      )}
      <p className="text-xs text-muted">Bu yerda faqat yuklangan modelning haqiqiy sinov natijalari ko‘rsatiladi.</p>
    </div>
  );
}

export default function HomePage() {
  return (
    <div>
      <section className="border-b border-border bg-white">
        <div className="container grid gap-10 py-12 md:py-16 lg:grid-cols-[1.25fr_1fr] lg:items-center">
          <div className="space-y-6">
            <Badge variant="outline">Ilmiy-tadqiqot platformasi · versiya 1.0</Badge>
            <div className="space-y-3">
              <h1 className="text-4xl font-bold md:text-5xl">Bo‘g‘imTahlil</h1>
              <p className="text-xl font-semibold text-accent md:text-2xl">
                Sun’iy intellekt asosida tizza bo‘g‘imi rentgen tasvirlarini tahlil qilish tizimi
              </p>
            </div>
            <p className="max-w-2xl text-base leading-relaxed text-ink md:text-lg">
              Bo‘g‘imTahlil — tizza bo‘g‘imining rentgen tasvirlarini sun’iy intellekt yordamida tahlil qilish va osteoartritga
              xos rentgenologik o‘zgarishlarni baholashga mo‘ljallangan ilmiy platforma.
            </p>
            <p className="text-sm font-medium italic text-muted">“Aniq tahlil sari aqlli qadam!”</p>
            <div className="flex flex-wrap gap-3">
              <Button asChild size="lg" variant="accent">
                <Link to="/tahlil">Tahlilni boshlash <ArrowRight /></Link>
              </Button>
              <Button asChild size="lg" variant="outline">
                <a href="#imkoniyatlar">Dastur imkoniyatlari</a>
              </Button>
            </div>
          </div>
          <Card>
            <CardContent className="space-y-4 pt-5">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-accent" />
                <h2 className="text-base font-semibold">Sun’iy intellekt modeli holati</h2>
              </div>
              <ModelSnapshot />
            </CardContent>
          </Card>
        </div>
      </section>

      <section id="imkoniyatlar" className="container scroll-mt-20 py-12">
        <h2 className="mb-6 text-2xl font-bold">Dastur imkoniyatlari</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map(({ icon: Icon, title, text }, i) => (
            <Card key={title} className="transition-shadow hover:shadow-md">
              <CardContent className="space-y-3 pt-5">
                <div className="flex items-center gap-3">
                  <span className="flex h-10 w-10 items-center justify-center rounded-md bg-accent-soft text-accent"><Icon className="h-5 w-5" /></span>
                  <span className="text-xs font-semibold text-muted">{i + 1}</span>
                </div>
                <h3 className="font-semibold text-primary">{title}</h3>
                <p className="text-sm leading-relaxed text-muted">{text}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="border-y border-border bg-white">
        <div className="container py-12">
          <h2 className="mb-6 text-2xl font-bold">Dastur qanday ishlaydi?</h2>
          <ol className="grid gap-4 md:grid-cols-5">
            {STEPS.map((s, i) => (
              <li key={s} className="relative rounded-lg border border-border bg-background p-4">
                <span className="mb-2 flex h-8 w-8 items-center justify-center rounded-full bg-primary text-sm font-bold text-white">{i + 1}</span>
                <p className="text-sm font-medium text-ink">{s}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="container grid gap-8 py-12 lg:grid-cols-[1.4fr_1fr]">
        <div>
          <h2 className="mb-2 text-2xl font-bold">Kellgren–Lawrence darajalari</h2>
          <p className="mb-5 text-sm text-muted">Model tasvirni quyidagi beshta rentgenologik darajadan biriga tasniflaydi.</p>
          <div className="overflow-hidden rounded-lg border border-border bg-white">
            {KL_LEVELS.map((k) => (
              <div key={k.grade} className="flex gap-4 border-b border-border p-4 last:border-b-0">
                <span className="flex h-10 w-14 shrink-0 items-center justify-center rounded-md text-sm font-bold text-white" style={{ background: k.color }}>
                  {k.label}
                </span>
                <div>
                  <p className="font-semibold text-primary">{k.title}</p>
                  <p className="text-sm text-muted">{KL_DESCRIPTIONS[k.grade]}</p>
                </div>
              </div>
            ))}
          </div>
          <p className="mt-2 text-xs text-muted">Manba: Kellgren J.H., Lawrence J.S. Ann Rheum Dis. 1957;16(4):494–502.</p>
        </div>
        <div className="space-y-6">
          <div>
            <h2 className="mb-4 text-2xl font-bold">Texnologiyalar</h2>
            <dl className="divide-y divide-border rounded-lg border border-border bg-white">
              {TECH.map(([k, v]) => (
                <div key={k} className="flex flex-col gap-0.5 p-3 sm:flex-row sm:justify-between">
                  <dt className="text-sm text-muted">{k}</dt>
                  <dd className="text-sm font-medium text-ink">{v}</dd>
                </div>
              ))}
            </dl>
          </div>
          <MedicalDisclaimer />
        </div>
      </section>
    </div>
  );
}
