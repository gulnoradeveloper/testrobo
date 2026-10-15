import { Eye, FileDown, Inbox, Plus, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { Alert } from "@/components/ui/alert";
import { ConfirmDialog } from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input, NativeSelect } from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { api, apiUrl, toApiError } from "@/lib/api";
import { KL_LEVELS } from "@/lib/kl";
import type { AnalysisListItem } from "@/lib/types";
import { useAsync } from "@/lib/useAsync";
import { formatDateTime } from "@/lib/utils";

export const DELETE_CONFIRM = "Ushbu tahlil va unga tegishli saqlangan ma’lumotlarni o‘chirishni tasdiqlaysizmi?";

function localDate(iso: string) {
  const d = new Date(iso);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function GradeChip({ i }: { i: AnalysisListItem }) {
  return (
    <span className="inline-flex items-center gap-2">
      <span className="rounded px-1.5 py-0.5 text-xs font-bold text-white" style={{ background: KL_LEVELS[i.kl_grade].color }}>{i.label}</span>
      <span className="text-ink">{i.title}</span>
    </span>
  );
}

export default function HistoryPage() {
  const [grade, setGrade] = useState("");
  const [sort, setSort] = useState("newest");
  const [date, setDate] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);
  const { data, error, loading, setData } = useAsync(
    () => api.list({ grade: grade === "" ? undefined : Number(grade), sort }),
    [grade, sort],
  );
  const items = useMemo(() => (data?.items ?? []).filter((i) => !date || localDate(i.created_at) === date), [data, date]);

  const remove = async (id: string) => {
    setActionError(null);
    try {
      await api.remove(id);
      setData((d) => (d ? { items: d.items.filter((x) => x.id !== id), total: d.total - 1 } : d));
    } catch (e) {
      setActionError(toApiError(e).message);
    }
  };

  const actions = (i: AnalysisListItem) => (
    <div className="flex flex-wrap gap-1.5">
      <Button asChild size="sm" variant="outline"><Link to={`/natija/${i.id}`}><Eye /> Batafsil</Link></Button>
      <Button asChild size="sm" variant="ghost"><a href={apiUrl(i.report_url)} download><FileDown /> PDF</a></Button>
      <ConfirmDialog
        trigger={<Button size="sm" variant="danger-outline" aria-label={`${i.number} tahlilini o‘chirish`}><Trash2 /> Tahlilni o‘chirish</Button>}
        title="Tahlilni o‘chirish"
        description={DELETE_CONFIRM}
        confirmText="O‘chirish"
        onConfirm={() => remove(i.id)}
      />
    </div>
  );

  return (
    <div className="container pb-12">
      <PageHeader
        title="Tahlillar tarixi"
        description="Joriy brauzer sessiyasida bajarilgan tahlillar. Boshqa foydalanuvchilar ularni ko‘ra olmaydi; ma’lumotlar 24 soatdan so‘ng avtomatik o‘chiriladi."
        actions={<Button asChild variant="accent"><Link to="/tahlil"><Plus /> Yangi tahlil</Link></Button>}
      />

      <Card className="mb-5">
        <CardContent className="grid gap-3 pt-5 sm:grid-cols-3">
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium text-muted">Sana bo‘yicha</span>
            <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium text-muted">KL darajasi bo‘yicha</span>
            <NativeSelect value={grade} onChange={(e) => setGrade(e.target.value)}>
              <option value="">Barcha darajalar</option>
              {KL_LEVELS.map((k) => <option key={k.grade} value={k.grade}>{k.label} — {k.title}</option>)}
            </NativeSelect>
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium text-muted">Saralash</span>
            <NativeSelect value={sort} onChange={(e) => setSort(e.target.value)}>
              <option value="newest">So‘nggi tahlillar avval</option>
              <option value="oldest">Eski tahlillar avval</option>
              <option value="grade_asc">Daraja: KL0 → KL4</option>
              <option value="grade_desc">Daraja: KL4 → KL0</option>
            </NativeSelect>
          </label>
        </CardContent>
      </Card>

      {actionError && <Alert variant="danger" className="mb-4">{actionError}</Alert>}
      {loading ? (
        <Spinner label="Tarix yuklanmoqda..." />
      ) : error ? (
        <Alert variant="danger">{error.message}</Alert>
      ) : items.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
            <Inbox className="h-10 w-10 text-muted" />
            <p className="font-semibold text-primary">Tahlillar topilmadi</p>
            <p className="text-sm text-muted">{data?.total ? "Tanlangan filtrlar bo‘yicha natija yo‘q." : "Bu sessiyada hali tahlil bajarilmagan."}</p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="hidden overflow-x-auto rounded-lg border border-border bg-white shadow-card md:block">
            <table className="w-full text-left text-sm">
              <thead className="bg-background text-xs uppercase tracking-wide text-muted">
                <tr>
                  {["Tahlil raqami", "Sana", "Tasvir identifikatori", "Bashorat qilingan daraja", "Model versiyasi", "Amallar"].map((h) => (
                    <th key={h} className="px-4 py-3 font-semibold">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {items.map((i) => (
                  <tr key={i.id} className="border-t border-border align-middle hover:bg-background/60">
                    <td className="px-4 py-3 font-semibold text-primary">{i.number}</td>
                    <td className="whitespace-nowrap px-4 py-3">{formatDateTime(i.created_at)}</td>
                    <td className="px-4 py-3 font-mono text-xs text-muted">{i.image_id}</td>
                    <td className="px-4 py-3"><GradeChip i={i} /></td>
                    <td className="px-4 py-3 text-muted">{i.model_version}</td>
                    <td className="px-4 py-3">{actions(i)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="space-y-3 md:hidden">
            {items.map((i) => (
              <Card key={i.id}>
                <CardContent className="space-y-2 pt-4 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-primary">{i.number}</span>
                    <span className="text-xs text-muted">{formatDateTime(i.created_at)}</span>
                  </div>
                  <GradeChip i={i} />
                  <p className="text-xs text-muted">Tasvir: <span className="font-mono">{i.image_id}</span> · Model: {i.model_version}</p>
                  {actions(i)}
                </CardContent>
              </Card>
            ))}
          </div>
          <p className="mt-3 text-xs text-muted">Jami: {items.length} ta tahlil</p>
        </>
      )}
    </div>
  );
}
