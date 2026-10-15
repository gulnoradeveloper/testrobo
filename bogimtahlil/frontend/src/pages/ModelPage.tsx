import { AlertTriangle, Database, Layers } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { PageHeader } from "@/components/PageHeader";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { api } from "@/lib/api";
import type { EvalMetrics } from "@/lib/types";
import { useAsync } from "@/lib/useAsync";
import { formatPercent } from "@/lib/utils";

export const NOT_EVALUATED = "Hali baholanmagan";
const CLASSES = ["KL0", "KL1", "KL2", "KL3", "KL4"];

function Row({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5 border-b border-border py-2.5 last:border-b-0 sm:flex-row sm:justify-between sm:gap-6">
      <dt className="text-sm text-muted">{k}</dt>
      <dd className="break-all text-sm font-medium text-ink sm:text-right">{v ?? NOT_EVALUATED}</dd>
    </div>
  );
}

function Metric({ label, value }: { label: string; value?: string }) {
  return (
    <div className="rounded-lg border border-border bg-background p-4">
      <p className="text-xs text-muted">{label}</p>
      <p className={value ? "text-2xl font-bold text-primary" : "text-sm font-medium text-muted"}>{value ?? NOT_EVALUATED}</p>
    </div>
  );
}

function ConfusionMatrix({ cm }: { cm: number[][] }) {
  return (
    <div className="overflow-x-auto">
      <table className="text-center text-xs">
        <thead>
          <tr>
            <th className="p-1.5 text-muted">Haqiqiy ↓ / Bashorat →</th>
            {CLASSES.map((c) => <th key={c} className="p-1.5 font-semibold text-primary">{c}</th>)}
          </tr>
        </thead>
        <tbody>
          {cm.map((row, i) => {
            const total = row.reduce((s, x) => s + x, 0) || 1;
            return (
              <tr key={i}>
                <th className="p-1.5 font-semibold text-primary">{CLASSES[i]}</th>
                {row.map((v, j) => {
                  const r = v / total;
                  return (
                    <td key={j} className="h-12 w-16 border border-white" style={{ background: `rgba(24,119,201,${0.08 + r * 0.85})`, color: r > 0.5 ? "#fff" : "#172B4D" }}>
                      <div className="font-semibold">{v}</div>
                      <div className="opacity-80">{formatPercent(r, 0)}</div>
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function Performance({ m }: { m?: EvalMetrics }) {
  const recall = CLASSES.map((c) => ({ name: c, value: m ? +(m.per_class[c].recall * 100).toFixed(1) : 0 }));
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        <Metric label="Umumiy aniqlik (Accuracy)" value={m && formatPercent(m.accuracy)} />
        <Metric label="Muvozanatlangan aniqlik" value={m && formatPercent(m.balanced_accuracy)} />
        <Metric label="Macro F1" value={m?.macro_f1.toFixed(3)} />
        <Metric label="Macro sezgirlik (Recall)" value={m && formatPercent(m.macro_recall)} />
        <Metric label="Quadratic Weighted Kappa" value={m?.quadratic_weighted_kappa.toFixed(3)} />
      </div>
      {m ? (
        <div className="grid gap-6 lg:grid-cols-2">
          <div>
            <h3 className="mb-2 text-sm font-semibold text-primary">Darajalar bo‘yicha sezgirlik (Recall)</h3>
            <div className="h-56">
              <ResponsiveContainer>
                <BarChart data={recall} margin={{ left: -12, top: 8 }}>
                  <CartesianGrid vertical={false} stroke="#E1E8F0" />
                  <XAxis dataKey="name" tickLine={false} />
                  <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} tickLine={false} axisLine={false} />
                  <Tooltip formatter={(v) => [`${v}%`, "Recall"]} />
                  <Bar dataKey="value" fill="#1877C9" radius={[6, 6, 0, 0]} isAnimationActive={false} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <table className="mt-3 w-full text-sm">
              <thead className="text-xs text-muted"><tr><th className="text-left">Daraja</th><th>Precision</th><th>Recall</th><th>F1</th><th>Soni</th></tr></thead>
              <tbody>
                {CLASSES.map((c) => (
                  <tr key={c} className="border-t border-border text-center">
                    <td className="py-1.5 text-left font-semibold text-primary">{c}</td>
                    <td>{m.per_class[c].precision.toFixed(3)}</td><td>{m.per_class[c].recall.toFixed(3)}</td>
                    <td>{m.per_class[c].f1.toFixed(3)}</td><td>{m.per_class[c].support}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div>
            <h3 className="mb-2 text-sm font-semibold text-primary">Tasniflash xatoliklari jadvali (Confusion Matrix)</h3>
            <ConfusionMatrix cm={m.confusion_matrix} />
            {m.early_grade_confusion && (
              <p className="mt-3 text-xs leading-relaxed text-muted">
                KL0–KL2 orasidagi o‘zaro xatolar ulushi: <b className="text-ink">{formatPercent(m.early_grade_confusion.error_rate_within_kl0_kl2)}</b>.
                Umumiy aniqlik yuqori bo‘lishi erta o‘zgarishlarni ishonchli aniqlashni avtomatik isbotlamaydi.
              </p>
            )}
            <p className="mt-2 text-xs text-muted">Test to‘plami hajmi: {m.n_samples} ta tasvir</p>
          </div>
        </div>
      ) : (
        <Alert variant="info">
          Mustaqil test to‘plamidagi metrikalar mavjud emas. Ular faqat haqiqiy eksperimentdan so‘ng (ai/scripts/evaluate.py) checkpointga
          yoziladi va shu yerda avtomatik ko‘rsatiladi.
        </Alert>
      )}
    </div>
  );
}

export default function ModelPage() {
  const { data, error, loading } = useAsync(() => api.modelInfo(), []);
  return (
    <div className="container space-y-6 pb-12">
      <PageHeader title="Sun’iy intellekt modeli haqida" description="Serverga yuklangan neyron tarmoq, uning o‘qitish manbasi va mustaqil sinov natijalari." />
      {loading && <Spinner />}
      {error && <Alert variant="danger">{error.message}</Alert>}
      {data && (
        <>
          {!data.loaded ? (
            <Alert variant="warning" title="Sun’iy intellekt modeli hozircha tahlil qilish uchun tayyor emas.">
              Holat kodi: <code>{data.status_code}</code>. O‘qitilgan checkpoint <code>artifacts/model.pt</code> manziliga joylashtirilgach va server
              qayta ishga tushirilgach, tahlil funksiyasi ishga tushadi. Modelni o‘qitish tartibi README va docs/ katalogida keltirilgan.
            </Alert>
          ) : !data.trained ? (
            <Alert variant="danger" title="O‘qitilmagan test modeli yuklangan">{data.status_message}</Alert>
          ) : (
            <Alert variant="success">{data.status_message}</Alert>
          )}

          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader><CardTitle className="flex items-center gap-2"><Layers className="h-4 w-4 text-accent" /> Model tavsifi</CardTitle></CardHeader>
              <CardContent>
                <dl>
                  <Row k="Model nomi" v={data.name} />
                  <Row k="Arxitektura" v={data.architecture} />
                  <Row k="Model versiyasi" v={data.version} />
                  <Row k="Checkpoint SHA-256" v={data.checkpoint_sha256 && <span className="font-mono text-xs">{data.checkpoint_sha256}</span>} />
                  <Row k="Kirish o‘lchami" v={data.preprocess ? `${String(data.preprocess.input_size)} × ${String(data.preprocess.input_size)}, kesilmasdan (letterbox)` : null} />
                  <Row k="Preprocess versiyasi" v={data.preprocess ? String(data.preprocess.version) : null} />
                  <Row k="Ehtimolliklar kalibrlanishi" v={data.calibration_evaluated ? "Baholangan" : "Baholanmagan"} />
                </dl>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle className="flex items-center gap-2"><Database className="h-4 w-4 text-accent" /> O‘qitish ma’lumotlari</CardTitle></CardHeader>
              <CardContent>
                <dl>
                  <Row k="Ma’lumotlar manbasi" v={(data.dataset.name as string) || null} />
                  <Row k="Foydalanish sharti" v={(data.dataset.license as string) || null} />
                  <Row k="Train / validation / test" v={data.dataset.n_train ? `${data.dataset.n_train} / ${data.dataset.n_val} / ${data.dataset.n_test ?? "—"}` : null} />
                  <Row k="Eng yaxshi epoch (validation)" v={data.training.best_epoch ? String(data.training.best_epoch) : null} />
                </dl>
                <div className="mt-4">
                  <p className="mb-2 text-sm text-muted">Baholanadigan darajalar</p>
                  <div className="flex flex-wrap gap-2">
                    {data.class_names.map((c) => <Badge key={c} variant="default">{c} — {data.class_titles[c]}</Badge>)}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Model samaradorligi</CardTitle>
              <CardDescription>Mustaqil (model tanlashda ishlatilmagan) test to‘plamidagi natijalar</CardDescription>
            </CardHeader>
            <CardContent><Performance m={data.metrics?.test} /></CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="flex items-center gap-2"><AlertTriangle className="h-4 w-4 text-warning" /> Model cheklovlari</CardTitle></CardHeader>
            <CardContent>
              <ul className="list-disc space-y-1.5 pl-5 text-sm leading-relaxed">{data.limitations.map((l) => <li key={l}>{l}</li>)}</ul>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
