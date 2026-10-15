export function LogoMark({ className = "h-9 w-9" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden>
      <rect width="32" height="32" rx="8" fill="#123A63" />
      <path d="M11 4v8.5c0 1.6 1.2 2.6 2.6 2.6h4.8c1.4 0 2.6-1 2.6-2.6V4" fill="none" stroke="#fff" strokeWidth="2.4" strokeLinecap="round" />
      <path d="M11 28v-7.5c0-1.6 1.2-2.6 2.6-2.6h4.8c1.4 0 2.6 1 2.6 2.6V28" fill="none" stroke="#7DB8EC" strokeWidth="2.4" strokeLinecap="round" />
    </svg>
  );
}

export function Logo() {
  return (
    <span className="flex items-center gap-2.5">
      <LogoMark />
      <span className="leading-tight">
        <span className="block text-[17px] font-bold text-primary">Bo‘g‘imTahlil</span>
        <span className="block text-[11px] font-medium uppercase tracking-wider text-muted">JointAI · 1.0</span>
      </span>
    </span>
  );
}
