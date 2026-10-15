import { cn } from "@/lib/utils";

/** value berilmasa — noaniq (indeterminate) holat: haqiqiy foiz ma’lum bo‘lmaganda ishlatiladi. */
export function Progress({ value, className }: { value?: number; className?: string }) {
  return (
    <div
      className={cn("relative h-2 w-full overflow-hidden rounded-full bg-border", className)}
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={value}
    >
      {value === undefined ? (
        <div className="absolute inset-y-0 w-1/3 animate-[indeterminate_1.2s_ease-in-out_infinite] rounded-full bg-accent" />
      ) : (
        <div className="h-full rounded-full bg-accent transition-all" style={{ width: `${value}%` }} />
      )}
      <style>{`@keyframes indeterminate{0%{left:-35%}100%{left:100%}}`}</style>
    </div>
  );
}
