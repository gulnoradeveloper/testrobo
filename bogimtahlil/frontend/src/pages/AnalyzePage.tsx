import { CheckCircle2, ImagePlus, Loader2, RefreshCw, Sparkles, Trash2, UploadCloud } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { MedicalDisclaimer } from "@/components/Disclaimer";
import { useHealth } from "@/components/ModelStatus";
import { PageHeader } from "@/components/PageHeader";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Progress } from "@/components/ui/progress";
import { api, MESSAGES, toApiError } from "@/lib/api";
import { cn, formatBytes } from "@/lib/utils";

export const MAX_BYTES = 20 * 1024 * 1024;
const ACCEPT = ["image/jpeg", "image/png"];
const EXT = /\.(jpe?g|png)$/i;

/** Brauzer tomonidagi dastlabki tekshiruv. Asosiy (ishonchli) tekshiruv serverda bajariladi. */
export function precheckFile(f: File): string | null {
  if (!EXT.test(f.name) || (f.type && !ACCEPT.includes(f.type))) return "Fayl formati qo‘llab-quvvatlanmaydi.";
  if (f.size > MAX_BYTES) return "Fayl hajmi belgilangan chegaradan oshgan.";
  if (f.size === 0) return "Tasvirni o‘qib bo‘lmadi.";
  return null;
}

type Phase =
  | { kind: "idle" }
  | { kind: "uploading"; percent: number }
  | { kind: "processing" }
  | { kind: "done" }
  | { kind: "error"; message: string };

export default function AnalyzePage() {
  const nav = useNavigate();
  const health = useHealth(60_000);
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [dims, setDims] = useState<{ w: number; h: number } | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [drag, setDrag] = useState(false);
  const [phase, setPhase] = useState<Phase>({ kind: "idle" });

  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);

  const pick = useCallback((f: File | undefined | null) => {
    if (!f) return;
    const err = precheckFile(f);
    if (err) {
      setPhase({ kind: "error", message: err });
      return;
    }
    const url = URL.createObjectURL(f);
    const img = new Image();
    img.onload = () => {
      setDims({ w: img.naturalWidth, h: img.naturalHeight });
      setFile(f);
      setPreview(url);
      setPhase({ kind: "idle" });
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      setPhase({ kind: "error", message: "Tasvirni o‘qib bo‘lmadi." });
    };
    img.src = url;
  }, []);

  const clear = () => {
    setFile(null);
    setPreview(null);
    setDims(null);
    setPhase({ kind: "idle" });
    if (inputRef.current) inputRef.current.value = "";
  };

  const busy = phase.kind === "uploading" || phase.kind === "processing";
  const modelReady = health.kind === "ok" && health.h.model_loaded;
  const modelUnknown = health.kind === "loading";

  const submit = async () => {
    if (busy) return; // takroriy bosishni bloklash
    if (!file) {
      setPhase({ kind: "error", message: "Fayl tanlanmagan." });
      return;
    }
    setPhase({ kind: "uploading", percent: 0 });
    try {
      const res = await api.analyze(file, (p) => setPhase(p >= 100 ? { kind: "processing" } : { kind: "uploading", percent: p }));
      setPhase({ kind: "done" });
      setTimeout(() => nav(`/natija/${res.id}`), 400);
    } catch (e) {
      setPhase({ kind: "error", message: toApiError(e).message });
    }
  };

  return (
    <div className="container pb-12">
      <PageHeader
        title="Rentgen tasvirini tahlil qilish"
        description="Bitta tizza bo‘g‘imining frontal rentgen tasvirini yuklang. Tasvir serverda tekshiriladi, qayta ishlanadi va o‘qitilgan neyron tarmoq yordamida baholanadi."
      />

      {health.kind === "offline" && <Alert variant="danger" className="mb-5">{MESSAGES.network}</Alert>}
      {health.kind === "ok" && !health.h.model_loaded && (
        <Alert variant="warning" className="mb-5" title={MESSAGES.modelNotReady}>
          Tahlil funksiyasi o‘qitilgan model serverga o‘rnatilgunga qadar cheklangan holatda. Dastur tasodifiy yoki namunaviy natija
          ko‘rsatmaydi. <Link to="/model" className="font-semibold text-accent underline">Model holati</Link>
        </Alert>
      )}
      {health.kind === "ok" && health.h.model_loaded && !health.h.model_trained && (
        <Alert variant="danger" className="mb-5" title="Serverda o‘qitilmagan test modeli yuklangan">
          Bu rejim faqat dasturni texnik sinash uchun. Bunday model bashoratlari tibbiy yoki ilmiy ma’noga ega emas.
        </Alert>
      )}

      <div className="grid gap-6 lg:grid-cols-[1.3fr_1fr]">
        <Card>
          <CardHeader><CardTitle>Tasvirni yuklash</CardTitle></CardHeader>
          <CardContent>
            <input
              ref={inputRef}
              type="file"
              accept=".jpg,.jpeg,.png,image/jpeg,image/png"
              className="sr-only"
              aria-label="Rentgen tasviri fayli"
              onChange={(e) => pick(e.target.files?.[0])}
              disabled={busy}
            />
            {!preview ? (
              <div
                role="button"
                tabIndex={0}
                onClick={() => inputRef.current?.click()}
                onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && inputRef.current?.click()}
                onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
                onDragLeave={() => setDrag(false)}
                onDrop={(e) => { e.preventDefault(); setDrag(false); pick(e.dataTransfer.files?.[0]); }}
                className={cn(
                  "flex min-h-[340px] cursor-pointer flex-col items-center justify-center gap-4 rounded-lg border-2 border-dashed p-8 text-center transition-colors",
                  drag ? "border-accent bg-accent-soft" : "border-border bg-background hover:border-accent/60",
                )}
              >
                <span className="flex h-14 w-14 items-center justify-center rounded-full bg-accent-soft text-accent"><UploadCloud className="h-7 w-7" /></span>
                <div className="space-y-1">
                  <p className="font-semibold text-primary">Faylni shu yerga sudrab joylashtiring</p>
                  <p className="text-sm text-muted">yoki kompyuteringizdan tanlang · JPG, JPEG, PNG · 20 MB gacha</p>
                </div>
                <Button type="button" variant="outline" onClick={(e) => { e.stopPropagation(); inputRef.current?.click(); }}>
                  <ImagePlus /> Tasvirni tanlash
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="checker flex max-h-[520px] min-h-[340px] items-center justify-center overflow-hidden rounded-lg">
                  <img src={preview} alt="Yuklangan rentgen tasviri" className="max-h-[520px] w-auto object-contain" />
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button variant="outline" onClick={() => inputRef.current?.click()} disabled={busy}><RefreshCw /> Tasvirni almashtirish</Button>
                  <Button variant="danger-outline" onClick={clear} disabled={busy}><Trash2 /> Tasvirni olib tashlash</Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="space-y-5">
          <Card>
            <CardHeader><CardTitle>Tahlil haqida ma’lumot</CardTitle></CardHeader>
            <CardContent className="space-y-4 text-sm">
              <dl className="divide-y divide-border rounded-md border border-border">
                {[
                  ["Yuklangan fayl nomi", file?.name ?? "—"],
                  ["Fayl hajmi", file ? formatBytes(file.size) : "—"],
                  ["Tasvir o‘lchamlari", dims ? `${dims.w} × ${dims.h} piksel` : "—"],
                  ["Formatlar", "JPG, JPEG, PNG · maksimal 20 MB"],
                  ["Qo‘llab-quvvatlanadigan proyeksiya", "Bitta tizzaning standart frontal (PA/AP) rentgen tasviri"],
                ].map(([k, v]) => (
                  <div key={k} className="flex flex-col gap-0.5 px-3 py-2 sm:flex-row sm:justify-between sm:gap-4">
                    <dt className="text-muted">{k}</dt>
                    <dd className="break-all font-medium text-ink sm:text-right">{v}</dd>
                  </div>
                ))}
              </dl>
              <p className="leading-relaxed text-muted">
                Tasvir serverda format va yaxlitlik bo‘yicha tekshiriladi, kulrang formatga o‘tkaziladi, kesilmasdan 224×224 o‘lchamga
                moslashtiriladi va neyron tarmoqqa uzatiladi. Natijada KL0–KL4 darajalari bo‘yicha model ehtimolliklari va Grad-CAM
                xaritasi hosil qilinadi.
              </p>
              <Alert variant="info" title="Muhim cheklov">
                Dastur rentgen proyeksiyasini va anatomik sohani avtomatik aniqlamaydi. DICOM, MRT, KT, lateral proyeksiya va ikki tizza
                birga tushgan tasvirlar qo‘llab-quvvatlanmaydi. Ma’lumotlardan foydalanishga ruxsatingiz bo‘lgan, anonimlashtirilgan
                tasvirlarni yuklang; tasvirlar 24 soatdan so‘ng avtomatik o‘chiriladi.
              </Alert>
              <label className="flex cursor-pointer items-start gap-3 rounded-md border border-border p-3">
                <Checkbox checked={confirmed} onCheckedChange={(v) => setConfirmed(v === true)} disabled={busy} />
                <span className="leading-relaxed">
                  Tasdiqlayman: yuklangan fayl <b>bitta tizza bo‘g‘imining frontal rentgen tasviri</b> va undan foydalanishga ruxsatim bor.
                </span>
              </label>
            </CardContent>
          </Card>

          <MedicalDisclaimer />

          <div className="space-y-3">
            <Button
              size="lg"
              variant="accent"
              className="w-full"
              onClick={submit}
              disabled={busy || !file || !confirmed || (!modelReady && !modelUnknown)}
            >
              {busy ? <Loader2 className="animate-spin" /> : <Sparkles />}
              Sun’iy intellekt yordamida tahlil qilish
            </Button>
            {!file && <p className="text-center text-xs text-muted">Avval rentgen tasvirini tanlang.</p>}
            {file && !confirmed && <p className="text-center text-xs text-muted">Tasvir turini tasdiqlang.</p>}
            {phase.kind === "uploading" && (
              <div className="space-y-1.5" aria-live="polite">
                <p className="text-sm text-ink">Tasvir yuklanmoqda... {phase.percent}%</p>
                <Progress value={phase.percent} />
              </div>
            )}
            {phase.kind === "processing" && (
              <div className="space-y-1.5" aria-live="polite">
                <p className="text-sm text-ink">Tahlil bajarilmoqda...</p>
                <Progress />
              </div>
            )}
            {phase.kind === "done" && (
              <p className="flex items-center gap-2 text-sm font-semibold text-success" aria-live="polite">
                <CheckCircle2 className="h-4 w-4" /> Tahlil yakunlandi.
              </p>
            )}
            {phase.kind === "error" && <Alert variant="danger">{phase.message}</Alert>}
          </div>
        </div>
      </div>
    </div>
  );
}
