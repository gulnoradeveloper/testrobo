import { useState } from "react";
import { apiUrl } from "@/lib/api";
import type { Analysis } from "@/lib/types";
import { Alert } from "./ui/alert";
import { Slider } from "./ui/slider";

function Frame({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <figure className="space-y-2">
      <div className="checker relative flex aspect-square items-center justify-center overflow-hidden rounded-lg">{children}</div>
      <figcaption className="text-center text-sm font-medium text-ink">{label}</figcaption>
    </figure>
  );
}

export function GradCamPanel({ a }: { a: Analysis }) {
  const [opacity, setOpacity] = useState(55);
  const img = apiUrl(a.image.url);
  if (!a.heatmap.available || !a.heatmap.heatmap_url) {
    return <Alert variant="danger">{a.heatmap.error ?? "Faollik xaritasi mavjud emas."}</Alert>;
  }
  const heat = apiUrl(a.heatmap.heatmap_url);
  return (
    <div className="space-y-5">
      <div className="grid gap-4 md:grid-cols-3">
        <Frame label="Asl rentgen tasviri">
          <img src={img} alt="Asl rentgen tasviri" className="max-h-full max-w-full object-contain" />
        </Frame>
        <Frame label="Rangli faollik xaritasi">
          <img src={heat} alt="Grad-CAM faollik xaritasi" className="max-h-full max-w-full object-contain" />
        </Frame>
        <Frame label="Birlashtirilgan tasvir">
          {/* Ikkala tasvir bir xil o‘lchamda va object-contain bilan joylashadi — piksellar ustma-ust tushadi */}
          <img src={img} alt="Asl tasvir ustida faollik xaritasi" className="absolute inset-0 h-full w-full object-contain" />
          <img src={heat} alt="" aria-hidden className="absolute inset-0 h-full w-full object-contain" style={{ opacity: opacity / 100 }} />
        </Frame>
      </div>
      <div className="flex flex-col gap-3 rounded-md border border-border p-4 sm:flex-row sm:items-center">
        <label className="shrink-0 text-sm font-medium text-ink" id="opacity-label">Rangli xarita shaffofligi</label>
        <Slider value={[opacity]} min={0} max={100} step={5} onValueChange={(v) => setOpacity(v[0])} thumbLabel="Rangli xarita shaffofligi" aria-labelledby="opacity-label" />
        <span className="w-12 shrink-0 text-right text-sm tabular-nums text-muted">{opacity}%</span>
      </div>
      <div className="flex flex-wrap items-center gap-3 text-xs text-muted">
        <span>Past faollik</span>
        <span className="h-2.5 w-40 rounded-full" style={{ background: "linear-gradient(90deg,#00008f,#0050ff,#00dfff,#7fff7f,#ffdf00,#ff4f00,#8f0000)" }} />
        <span>Yuqori faollik</span>
      </div>
      <Alert variant="info">{a.heatmap.note}</Alert>
    </div>
  );
}
