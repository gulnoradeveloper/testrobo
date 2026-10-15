import { ArrowLeft, Clock, Cpu, FileDown, History, Plus } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { GradCamPanel } from "@/components/GradCamPanel";
import { ImageViewer } from "@/components/ImageViewer";
import { PageHeader } from "@/components/PageHeader";
import { ProbabilityChart } from "@/components/ProbabilityChart";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { api, apiUrl } from "@/lib/api";
import { KL_LEVELS } from "@/lib/kl";
import { useAsync } from "@/lib/useAsync";
import { formatDateTime, formatMs, formatPercent } from "@/lib/utils";

export default function ResultPage() {
  const { id = "" } = useParams();
  const { data: a, error, loading } = useAsync(() => api.get(id), [id]);

  if (loading) return <div className="container py-16"><Spinner label="Natija yuklanmoqda..." /></div>;
  if (error || !a)
    return (
      <div className="container space-y-4 py-16">
        <Alert variant="danger" title={error?.message ?? "Tahlil natijasi topilmadi."}>
          Natija o‘chirilgan, saqlash muddati tugagan yoki boshqa sessiyaga tegishli bo‘lishi mumkin.
        </Alert>
        <Button asChild variant="outline"><Link to="/tarix"><ArrowLeft /> Tahlillar tarixiga o‘tish</Link></Button>
      </div>
    );

  const k = a.prediction.kl_grade;
  const level = KL_LEVELS[k];
  const trained = a.model.training_status === "trained";

  return (
    <div className="container space-y-6 pb-12">
      <PageHeader
        title="Rentgen tahlili natijalari"
        description={<>Tahlil raqami: <b className="text-ink">{a.number}</b> · {formatDateTime(a.created_at)}</>}
        actions={
          <>
            <Button asChild variant="accent"><a href={apiUrl(a.report_url)} download><FileDown /> PDF hisobotni yuklab olish</a></Button>
            <Button asChild variant="outline"><Link to="/tahlil"><Plus /> Yangi tahlil</Link></Button>
            <Button asChild variant="ghost"><Link to="/tarix"><History /> Tahlillar tarixiga o‘tish</Link></Button>
          </>
        }
      />

      {!trained && (
        <Alert variant="danger" title="O‘qitilmagan test modeli">
          Ushbu natija o‘qitilmagan (tasodifiy vaznli) test checkpointi orqali olingan va faqat dasturning texnik ishlashini tekshirish
          uchun. U tibbiy yoki ilmiy ma’noga ega emas.
        </Alert>
      )}

      <div className="grid gap-6 lg:grid-cols-[1.15fr_1fr]">
        <Card>
          <CardHeader><CardTitle>Rentgen tasviri</CardTitle></CardHeader>
          <CardContent>
            <ImageViewer src={apiUrl(a.image.url)} alt="Tahlil qilingan rentgen tasviri" width={a.image.width} height={a.image.height} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Sun’iy intellekt bahosi</CardTitle>
            <CardDescription>Dastlabki avtomatlashtirilgan tahlil natijasi — tashxis emas</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="rounded-lg border border-border bg-background p-5">
              <p className="text-sm text-muted">Bashorat qilingan daraja:</p>
              <div className="mt-1 flex items-center gap-3">
                <span className="rounded-md px-3 py-1 text-3xl font-bold text-white" style={{ background: level.color }}>{a.prediction.label}</span>
                <span className="text-lg font-semibold text-primary">{a.prediction.title}</span>
              </div>
              <p className="mt-2 text-sm text-muted">Model ehtimolligi: <b className="text-ink">{formatPercent(a.probabilities[k].probability)}</b></p>
            </div>
            <div>
              <h3 className="mb-1 text-sm font-semibold text-primary">Modelning darajalar bo‘yicha ehtimolliklari</h3>
              <ProbabilityChart data={a.probabilities} predicted={k} />
              <p className="mt-1 text-xs leading-relaxed text-muted">{a.probability_note}</p>
            </div>
            <dl className="grid grid-cols-1 gap-2 text-sm sm:grid-cols-2">
              <div className="flex items-center gap-2 rounded-md bg-muted-bg p-2.5"><Cpu className="h-4 w-4 text-accent" />
                <span><span className="text-muted">Model:</span> {a.model.architecture} · {a.model.version}</span></div>
              <div className="flex items-center gap-2 rounded-md bg-muted-bg p-2.5"><Clock className="h-4 w-4 text-accent" />
                <span><span className="text-muted">Hisoblash vaqti:</span> {formatMs(a.processing_time_ms)}</span></div>
            </dl>
            <div className="flex flex-wrap gap-2 text-xs">
              {Object.entries(a.timing).map(([key, v]) => (
                <Badge key={key} variant="outline">
                  {{ preprocess_ms: "Ishlov berish", inference_ms: "Neyron tarmoq", gradcam_ms: "Grad-CAM", total_ms: "Jami" }[key] ?? key}: {formatMs(v)}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Sun’iy intellekt e’tibor qaratgan sohalar</CardTitle>
          <CardDescription>Grad-CAM usuli bilan bashorat qilingan sinf ({a.prediction.label}) uchun hisoblangan vizual izoh</CardDescription>
        </CardHeader>
        <CardContent><GradCamPanel a={a} /></CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Tahlil natijasining izohi</CardTitle></CardHeader>
        <CardContent className="space-y-5 text-sm leading-relaxed">
          <div>
            <h3 className="font-semibold text-primary">{a.prediction.label} — {a.prediction.title}</h3>
            <p className="mt-1">{a.prediction.description}</p>
            <p className="mt-1 text-xs text-muted">
              Manba: {a.prediction.reference} Bu daraja uchun umumiy ta’rif; model aynan shu tasvirda sanab o‘tilgan belgilarni alohida
              aniqlaganini bildirmaydi.
            </p>
          </div>
          <div>
            <h3 className="font-semibold text-primary">Natijani talqin qilishdagi cheklovlar</h3>
            <ul className="mt-2 list-disc space-y-1 pl-5">{a.limitations.map((l) => <li key={l}>{l}</li>)}</ul>
          </div>
          <Alert variant="info">{a.specialist_advice}</Alert>
          <Alert variant="warning" title="Tibbiy ogohlantirish">{a.disclaimer}</Alert>
          <p className="text-xs text-muted">Saqlash muddati: {formatDateTime(a.expires_at)} gacha — so‘ngra natija va tasvirlar avtomatik o‘chiriladi.</p>
        </CardContent>
      </Card>
    </div>
  );
}
