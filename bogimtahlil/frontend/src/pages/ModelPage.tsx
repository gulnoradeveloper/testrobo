import { AlertTriangle, BarChart3, Database, FlaskConical, GitCompare, Grid3x3, IdCard, LineChart as LineIcon } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import {
  Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { MedicalDisclaimer } from "@/components/Disclaimer";
import { PageHeader } from "@/components/PageHeader";
import { ServerOffline } from "@/components/ServerOffline";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { api, toApiError, type ApiError } from "@/lib/api";
import { KL_LEVELS } from "@/lib/kl";
import type { Experiments, MetricSet, ModelInfo, TrainingRun } from "@/lib/types";
import { formatPercent } from "@/lib/utils";

export const NA = "Natija mavjud emas";
/** Eski nom — boshqa joylarda ishlatilgan bo‘lishi mumkin. */
export const NOT_EVALUATED = NA;
const CLASSES = ["KL0", "KL1", "KL2", "KL3", "KL4"];
const SPLIT_TITLES: Record<string, string> = { train: "O‘qitish", val: "Tekshiruv", test: "Sinov" };
const TICK = { fill: "#66788A", fontSize: 12 };

function Na({ className = "" }: { className?: string }) {
  return <span className={`text-sm font-medium text-muted ${className}`}>{NA}</span>;
}

function Section({ icon: Icon, title, description, children }: {
  icon: typeof IdCard; title: string; description?: string; children: React.ReactNode;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2"><Icon className="h-4 w-4 text-accent" /> {title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

function Row({ k, v }: { k: string; v: React.ReactNode }) {
  const empty = v === null || v === undefined || v === "";
  return (
    <div className="flex flex-col gap-0.5 border-b border-border py-2.5 last:border-b-0 sm:flex-row sm:justify-between sm:gap-6">
      <dt className="text-sm text-muted">{k}</dt>
      <dd className="break-all text-sm font-medium text-ink sm:text-right">{empty ? <Na /> : v}</dd>
    </div>
  );
}

function Tile({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="rounded-lg border border-border bg-background p-4">
      <p className="text-xs text-muted">{label}</p>
      {value ? <p className="text-2xl font-bold text-primary">{value}</p> : <Na className="mt-1 block" />}
    </div>
  );
}

const pct = (v?: number | null) => (typeof v === "number" ? formatPercent(v) : null);
const num = (v?: number | null) => (typeof v === "number" ? v.toFixed(3) : null);

function StatusBadge({ info }: { info: ModelInfo }) {
  if (info.loaded && info.trained) return <Badge variant="success">Model ishlamoqda</Badge>;
  if (info.loaded) return <Badge variant="danger">O‘qitilmagan test modeli</Badge>;
  if (info.status_code === "MODEL_NOT_FOUND") return <Badge variant="warning">Model hali o‘qitilmagan</Badge>;
  return <Badge variant="warning">Model yuklanmadi</Badge>;
}

function Passport({ info }: { info: ModelInfo }) {
  return (
    <Section icon={IdCard} title="Model pasporti">
      <dl>
        <Row k="Holati" v={<StatusBadge info={info} />} />
        <Row k="Model nomi" v={info.name} />
        <Row k="Arxitektura" v={info.architecture} />
        <Row k="Model versiyasi" v={info.version} />
        <Row k="Checkpoint SHA-256" v={info.checkpoint_sha256 && <span className="font-mono text-xs">{info.checkpoint_sha256}</span>} />
        <Row k="Kirish o‘lchami" v={info.preprocess ? `${String(info.preprocess.input_size)} × ${String(info.preprocess.input_size)} piksel` : null} />
        <Row k="Baholanadigan darajalar" v={info.class_names.join(", ")} />
        <Row k="Ehtimolliklar kalibrlanishi" v={info.loaded ? (info.calibration_evaluated ? "Baholangan" : "Baholanmagan") : null} />
      </dl>
    </Section>
  );
}

function DatasetSection({ e, info }: { e: Experiments; info: ModelInfo }) {
  const d = e.dataset;
  const splits = d.splits ?? {};
  const chart = Object.entries(splits).map(([s, v]) => ({ name: SPLIT_TITLES[s] ?? s, ...v.classes }));
  return (
    <Section icon={Database} title="Ma’lumotlar to‘plami" description="Manba: data/splits/dataset_report.json va model metama’lumotlari">
      <dl>
        <Row k="Nomi" v={d.name ?? (info.dataset.name as string | undefined)} />
        <Row k="Tasvirlar soni" v={d.images?.toLocaleString("uz")} />
        <Row k="Bemorlar soni" v={d.patients?.toLocaleString("uz")} />
        <Row k="Ajratish qoidasi" v={d.split_rule} />
        <Row k="Guruhlar orasida kesishgan bemorlar" v={d.available ? String(d.patients_in_multiple_splits ?? 0) : null} />
      </dl>
      {d.available && chart.length > 0 ? (
        <div className="mt-5 grid gap-6">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-xs text-muted">
                <tr><th className="py-1.5 text-left">Guruh</th><th>Tasvir</th><th>Bemor</th>{CLASSES.map((c) => <th key={c}>{c}</th>)}</tr>
              </thead>
              <tbody>
                {Object.entries(splits).map(([s, v]) => (
                  <tr key={s} className="border-t border-border text-center">
                    <td className="py-1.5 text-left font-semibold text-primary">{SPLIT_TITLES[s] ?? s}</td>
                    <td>{v.images}</td><td>{v.patients}</td>
                    {CLASSES.map((c) => <td key={c}>{v.classes?.[c] ?? 0}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="h-56" aria-label="KL0–KL4 taqsimoti diagrammasi">
            <ResponsiveContainer>
              <BarChart data={chart} margin={{ left: -8, top: 4 }}>
                <CartesianGrid vertical={false} stroke="#E1E8F0" />
                <XAxis dataKey="name" tick={TICK} tickLine={false} />
                <YAxis tick={TICK} tickLine={false} axisLine={false} />
                <Tooltip />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                {KL_LEVELS.map((k) => <Bar key={k.label} dataKey={k.label} stackId="kl" fill={k.color} isAnimationActive={false} />)}
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      ) : (
        <p className="mt-4 text-sm text-muted">KL0–KL4 taqsimoti: {NA}. Dataset hali tayyorlanmagan (docs/MODEL_OQITISH.md).</p>
      )}
    </Section>
  );
}

function TrainingChart({ run }: { run: TrainingRun }) {
  if (!run.history.length) return <div className="rounded-md border border-dashed border-border p-6 text-center"><Na /></div>;
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div className="h-52" aria-label={`${run.title}: xatolik grafigi`}>
        <p className="mb-1 text-xs font-semibold text-muted">Xatolik (loss)</p>
        <ResponsiveContainer>
          <LineChart data={run.history} margin={{ left: -12, right: 8 }}>
            <CartesianGrid stroke="#E1E8F0" vertical={false} />
            <XAxis dataKey="epoch" tick={TICK} tickLine={false} />
            <YAxis tick={TICK} tickLine={false} axisLine={false} />
            <Tooltip />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Line dataKey="train_loss" name="O‘qitish" stroke="#123A63" dot={false} strokeWidth={2} isAnimationActive={false} />
            <Line dataKey="val_loss" name="Tekshiruv" stroke="#1877C9" dot={false} strokeWidth={2} strokeDasharray="5 3" isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="h-52" aria-label={`${run.title}: tekshiruv metrikalari grafigi`}>
        <p className="mb-1 text-xs font-semibold text-muted">Tekshiruv to‘plamidagi ko‘rsatkichlar</p>
        <ResponsiveContainer>
          <LineChart data={run.history} margin={{ left: -12, right: 8 }}>
            <CartesianGrid stroke="#E1E8F0" vertical={false} />
            <XAxis dataKey="epoch" tick={TICK} tickLine={false} />
            <YAxis domain={[0, 1]} tick={TICK} tickLine={false} axisLine={false} />
            <Tooltip />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Line dataKey="val_accuracy" name="Accuracy" stroke="#168A61" dot={false} strokeWidth={2} isAnimationActive={false} />
            <Line dataKey="val_macro_f1" name="Macro F1" stroke="#1877C9" dot={false} strokeWidth={2} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function TrainingSection({ e }: { e: Experiments }) {
  return (
    <Section icon={LineIcon} title="O‘qitish jarayoni" description="Manba: experiments/<arxitektura>/history.csv — har bir epoch natijasi">
      <div className="space-y-6">
        {Object.entries(e.training).map(([arch, run]) => (
          <div key={arch}>
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <h3 className="font-semibold text-primary">{run.title}</h3>
              {run.available ? (
                <span className="text-xs text-muted">
                  Eng yaxshi epoch: {run.best_epoch ?? "—"} / {run.epochs_run ?? "—"}
                  {run.training_minutes != null && ` · ${run.training_minutes} daqiqa`}
                  {run.pretrained != null && ` · transfer learning: ${run.pretrained ? "ha" : "yo‘q"}`}
                </span>
              ) : <Badge variant="outline">o‘qitilmagan</Badge>}
            </div>
            <TrainingChart run={run} />
          </div>
        ))}
      </div>
    </Section>
  );
}

function PerformanceSection({ e }: { e: Experiments }) {
  const t = e.test.available ? (e.test as MetricSet) : null;
  const recall = CLASSES.map((c) => ({ name: c, value: t?.recall?.[c] != null ? +(t.recall[c] * 100).toFixed(1) : 0 }));
  return (
    <Section icon={BarChart3} title="Model samaradorligi" description="Mustaqil sinov (test) to‘plami — model tanlashda ishlatilmagan">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Tile label="Accuracy" value={pct(t?.accuracy)} />
        <Tile label="Balanced Accuracy" value={pct(t?.balanced_accuracy)} />
        <Tile label="Macro F1" value={num(t?.macro_f1)} />
        <Tile label="Quadratic Weighted Kappa" value={num(t?.quadratic_weighted_kappa)} />
      </div>
      {t ? (
        <div className="mt-5">
          <p className="mb-1 text-sm font-semibold text-primary">Darajalar bo‘yicha sezgirlik (Recall)</p>
          <div className="h-52">
            <ResponsiveContainer>
              <BarChart data={recall} margin={{ left: -12, top: 8 }}>
                <CartesianGrid vertical={false} stroke="#E1E8F0" />
                <XAxis dataKey="name" tick={TICK} tickLine={false} />
                <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} tick={TICK} tickLine={false} axisLine={false} />
                <Tooltip formatter={(v) => [`${v}%`, "Recall"]} />
                <Bar dataKey="value" fill="#1877C9" radius={[6, 6, 0, 0]} isAnimationActive={false} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-1 text-xs text-muted">
            Test: {t.n_samples ?? "—"} ta tasvir{t.n_patients ? `, ${t.n_patients} ta bemor` : ""}.
            {t.early_grade_error_rate != null && ` KL0–KL2 orasidagi o‘zaro xatolar: ${formatPercent(t.early_grade_error_rate)}.`}
          </p>
        </div>
      ) : (
        <p className="mt-3 text-sm text-muted">Mustaqil test natijalari faqat model o‘qitilib, `evaluate.py --split test` bajarilgandan so‘ng paydo bo‘ladi.</p>
      )}
    </Section>
  );
}

function ComparisonSection({ e }: { e: Experiments }) {
  const runs = Object.entries(e.training);
  const keys: [keyof MetricSet, string][] = [["accuracy", "Accuracy"], ["balanced_accuracy", "Balanced Acc."], ["macro_f1", "Macro F1"], ["quadratic_weighted_kappa", "QWK"]];
  const chart = keys.map(([k, label]) => ({
    name: label,
    ...Object.fromEntries(runs.map(([, r]) => [r.title, r.validation ? +((r.validation[k] as number) * 100).toFixed(1) : 0])),
  }));
  const any = runs.some(([, r]) => r.validation);
  return (
    <Section icon={GitCompare} title="ResNet-18 va EfficientNet-B0 qiyosi" description="Tekshiruv (validation) to‘plami — eng yaxshi model shu bo‘yicha tanlanadi">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[520px] text-sm">
          <thead className="text-xs text-muted">
            <tr><th className="py-1.5 text-left">Model</th>{keys.map(([, l]) => <th key={l}>{l}</th>)}<th>Holat</th></tr>
          </thead>
          <tbody>
            {runs.map(([arch, r]) => (
              <tr key={arch} className="border-t border-border text-center">
                <td className="py-2 text-left font-semibold text-primary">{r.title}</td>
                {keys.map(([k]) => (
                  <td key={k}>{r.validation ? (k === "macro_f1" || k === "quadratic_weighted_kappa" ? num(r.validation[k] as number) : pct(r.validation[k] as number)) : <Na />}</td>
                ))}
                <td>{e.comparison.selected === arch ? <Badge variant="success">Tanlangan</Badge> : r.validation ? "—" : <Na />}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {any && (
        <div className="mt-5 h-56">
          <ResponsiveContainer>
            <BarChart data={chart} margin={{ left: -12, top: 8 }}>
              <CartesianGrid vertical={false} stroke="#E1E8F0" />
              <XAxis dataKey="name" tick={TICK} tickLine={false} />
              <YAxis domain={[0, 100]} tick={TICK} tickLine={false} axisLine={false} />
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="ResNet-18" fill="#123A63" radius={[4, 4, 0, 0]} isAnimationActive={false} />
              <Bar dataKey="EfficientNet-B0" fill="#1877C9" radius={[4, 4, 0, 0]} isAnimationActive={false} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
      <p className="mt-3 text-xs text-muted">
        {e.comparison.available ? `${e.comparison.reason}. Qoida: ${e.comparison.rule}.` : `Tanlov: ${NA} — modellar hali o‘qitilmagan.`}
      </p>
    </Section>
  );
}

function ConfusionSection({ e }: { e: Experiments }) {
  const cm = e.test.available ? e.test.confusion_matrix : null;
  return (
    <Section icon={Grid3x3} title="Tasniflash xatoliklari jadvali" description="Confusion matrix — mustaqil sinov to‘plami (qator: haqiqiy daraja, ustun: bashorat)">
      {cm ? (
        <div className="overflow-x-auto">
          <table className="mx-auto text-center text-xs">
            <thead>
              <tr><th className="p-1.5 text-muted">Haqiqiy ↓ / Bashorat →</th>{CLASSES.map((c) => <th key={c} className="p-1.5 font-semibold text-primary">{c}</th>)}</tr>
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
                        <td key={j} className="h-14 w-20 border border-white" style={{ background: `rgba(24,119,201,${0.08 + r * 0.85})`, color: r > 0.5 ? "#fff" : "#172B4D" }}>
                          <div className="text-sm font-semibold">{v}</div><div className="opacity-80">{formatPercent(r, 0)}</div>
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="rounded-md border border-dashed border-border p-6 text-center"><Na /></div>
      )}
    </Section>
  );
}

export default function ModelPage() {
  const [info, setInfo] = useState<ModelInfo | null>(null);
  const [exp, setExp] = useState<Experiments | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    Promise.all([api.modelInfo(), api.experiments()])
      .then(([i, e]) => { setInfo(i); setExp(e); })
      .catch((err) => setError(toApiError(err)))
      .finally(() => setLoading(false));
  }, []);
  useEffect(load, [load]);

  return (
    <div className="container space-y-6 pb-12">
      <PageHeader
        title="Sun’iy intellekt modeli haqida"
        description="Model pasporti, ma’lumotlar to‘plami, o‘qitish jarayoni va mustaqil sinov natijalari — barcha qiymatlar model metama’lumotlari va tajriba fayllaridan olinadi."
      />
      {loading && <Spinner label="Model ma’lumotlari yuklanmoqda..." />}
      {error && (error.code === "NETWORK" ? <ServerOffline onRetry={load} /> : (
        <Alert variant="danger" title="Ma’lumotlarni olishda xatolik">
          {error.message} (kod: {error.code}{error.status ? `, HTTP ${error.status}` : ""})
          <div className="mt-2"><Button size="sm" variant="outline" onClick={load}>Qayta urinish</Button></div>
        </Alert>
      ))}
      {info && exp && !error && (
        <>
          {!info.loaded ? (
            <Alert variant="warning" title={info.status_code === "MODEL_NOT_FOUND" ? "Model hali o‘qitilmagan" : "Sun’iy intellekt modeli hozircha tahlil qilish uchun tayyor emas."}>
              {info.status_code === "MODEL_NOT_FOUND"
                ? "artifacts/model.pt fayli mavjud emas. Model o‘qitilib, eksport qilingach bu sahifa avtomatik to‘ldiriladi. Quyidagi bo‘limlarda mavjud bo‘lmagan natijalar o‘rniga “Natija mavjud emas” ko‘rsatiladi."
                : `${info.status_message} (holat kodi: ${info.status_code})`}
            </Alert>
          ) : !info.trained ? (
            <Alert variant="danger" title="O‘qitilmagan test modeli yuklangan">{info.status_message}</Alert>
          ) : (
            <Alert variant="success">{info.status_message}</Alert>
          )}
          <div className="grid gap-6 xl:grid-cols-2">
            <Passport info={info} />
            <DatasetSection e={exp} info={info} />
          </div>
          <TrainingSection e={exp} />
          <PerformanceSection e={exp} />
          <ComparisonSection e={exp} />
          <ConfusionSection e={exp} />
          <Section icon={AlertTriangle} title="Model cheklovlari">
            <ul className="list-disc space-y-1.5 pl-5 text-sm leading-relaxed">{info.limitations.map((l) => <li key={l}>{l}</li>)}</ul>
          </Section>
          <MedicalDisclaimer />
          <p className="flex items-center gap-2 text-xs text-muted"><FlaskConical className="h-3.5 w-3.5" /> Statistik qiymatlar faqat haqiqiy tajriba natijalaridan olinadi; mavjud bo‘lmaganlari uchun “{NA}” ko‘rsatiladi.</p>
        </>
      )}
    </div>
  );
}
