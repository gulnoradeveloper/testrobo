import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Probability } from "@/lib/types";

export function ProbabilityChart({ data, predicted }: { data: Probability[]; predicted: number }) {
  const rows = data.map((p) => ({ name: p.label, title: p.title, value: +(p.probability * 100).toFixed(1) }));
  return (
    <div className="h-64 w-full" aria-label="Modelning darajalar bo‘yicha ehtimolliklari diagrammasi">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} margin={{ top: 20, right: 8, left: -12, bottom: 0 }}>
          <CartesianGrid vertical={false} stroke="#E1E8F0" />
          <XAxis dataKey="name" tickLine={false} axisLine={{ stroke: "#E1E8F0" }} tick={{ fill: "#172B4D", fontSize: 13, fontWeight: 600 }} />
          <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} tickLine={false} axisLine={false} tick={{ fill: "#66788A", fontSize: 12 }} />
          <Tooltip
            cursor={{ fill: "#F6F9FC" }}
            formatter={(v) => [`${v}%`, "Ehtimollik"]}
            labelFormatter={(l, p) => `${l} — ${p?.[0]?.payload?.title ?? ""}`}
            contentStyle={{ borderRadius: 8, borderColor: "#E1E8F0", fontSize: 13 }}
          />
          <Bar dataKey="value" radius={[6, 6, 0, 0]} maxBarSize={56} isAnimationActive={false}>
            {rows.map((_, i) => <Cell key={i} fill={i === predicted ? "#1877C9" : "#B9CDE2"} />)}
            <LabelList dataKey="value" position="top" formatter={(v: unknown) => `${v}%`} style={{ fill: "#172B4D", fontSize: 12, fontWeight: 600 }} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
