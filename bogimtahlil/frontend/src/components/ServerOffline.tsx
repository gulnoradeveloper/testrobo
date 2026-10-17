import { RefreshCw, ServerCrash } from "lucide-react";
import { Button } from "./ui/button";

/** Server javob bermaganda (tarmoq xatosi) — model holatidan alohida ko‘rsatiladi. */
export function ServerOffline({ onRetry }: { onRetry?: () => void }) {
  return (
    <div role="alert" className="rounded-lg border border-danger/30 bg-danger-soft p-5">
      <div className="flex gap-3">
        <ServerCrash className="mt-0.5 h-6 w-6 shrink-0 text-danger" />
        <div className="space-y-2 text-sm leading-relaxed text-ink">
          <p className="text-base font-semibold text-primary">Server bilan bog‘lanib bo‘lmadi.</p>
          <p>Sahifa ochilgan, lekin server so‘rovlarga javob bermayapti. Odatda sabab quyidagilardan biri:</p>
          <ul className="list-disc space-y-1 pl-5">
            <li><b>BOGIMTAHLIL.bat</b> oynasi yopilgan — uni qayta ishga tushiring va oynani ochiq qoldiring.</li>
            <li>Server to‘xtagan — oynadagi xabarni yoki <code>logs\server.log</code> faylini tekshiring.</li>
            <li>Server boshqa portda ishga tushgan — oynada yozilgan manzilni oching.</li>
          </ul>
          {onRetry && (
            <Button variant="outline" size="sm" onClick={onRetry} className="mt-1"><RefreshCw /> Qayta urinish</Button>
          )}
        </div>
      </div>
    </div>
  );
}
