/** Bo‘g‘imTahlil logotipi (public/logo-mark.webp — emblema, public/logo.webp — to‘liq logotip). */
export function LogoMark({ className = "h-10 w-auto" }: { className?: string }) {
  return <img src="/logo-mark.webp" alt="" aria-hidden className={className} width={320} height={255} />;
}

export function LogoFull({ className = "w-full max-w-sm" }: { className?: string }) {
  return <img src="/logo.webp" alt="Bo‘g‘imTahlil logotipi" className={className} width={640} height={573} />;
}

export function Logo({ inverted = false }: { inverted?: boolean }) {
  return (
    <span className="flex items-center gap-2.5">
      <LogoMark className="h-11 w-auto" />
      <span className="leading-tight">
        <span className={`block text-[18px] font-extrabold tracking-tight ${inverted ? "text-white" : "text-primary"}`}>
          Bo‘g‘im<span className="text-accent">Tahlil</span>
        </span>
        <span className={`block text-[10.5px] font-semibold uppercase tracking-[0.14em] ${inverted ? "text-white/60" : "text-muted"}`}>
          Sun’iy intellekt · 1.0
        </span>
      </span>
    </span>
  );
}
