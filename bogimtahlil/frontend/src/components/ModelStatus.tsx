import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import type { Health } from "@/lib/types";
import { cn } from "@/lib/utils";

type State = { kind: "loading" } | { kind: "ok"; h: Health } | { kind: "offline" };

/** Sarlavhadagi real model holati (/api/v1/health dan). */
export function useHealth(intervalMs = 30_000) {
  const [state, setState] = useState<State>({ kind: "loading" });
  useEffect(() => {
    let alive = true;
    const load = () =>
      api.health().then((h) => alive && setState({ kind: "ok", h })).catch(() => alive && setState({ kind: "offline" }));
    load();
    const t = setInterval(load, intervalMs);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, [intervalMs]);
  return state;
}

export function ModelStatusPill({ className }: { className?: string }) {
  const s = useHealth();
  let dot = "bg-muted", text = "Holat tekshirilmoqda...";
  if (s.kind === "offline") [dot, text] = ["bg-danger", "Server bilan aloqa yo‘q"];
  else if (s.kind === "ok" && s.h.model_loaded && s.h.model_trained) [dot, text] = ["bg-success", "Model tayyor"];
  else if (s.kind === "ok" && s.h.model_loaded) [dot, text] = ["bg-warning", "Test modeli (o‘qitilmagan)"];
  else if (s.kind === "ok") [dot, text] = ["bg-warning", "Model tayyor emas"];
  return (
    <Link
      to="/model"
      className={cn("inline-flex items-center gap-2 rounded-full border border-border bg-white px-3 py-1 text-xs font-medium text-ink hover:bg-muted-bg", className)}
      title={s.kind === "ok" ? s.h.model_status_message : undefined}
    >
      <span className={cn("h-2 w-2 rounded-full", dot)} aria-hidden />
      {text}
    </Link>
  );
}
