import { Brain, History, Home, Info, Menu, ScanLine, X } from "lucide-react";
import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import { Logo } from "./Logo";
import { ModelStatusPill } from "./ModelStatus";

export const NAV = [
  { to: "/", label: "Bosh sahifa", icon: Home, end: true },
  { to: "/tahlil", label: "Rentgen tahlili", icon: ScanLine },
  { to: "/tarix", label: "Tahlillar tarixi", icon: History },
  { to: "/model", label: "Sun’iy intellekt modeli", icon: Brain },
  { to: "/haqida", label: "Dastur haqida", icon: Info },
];

function NavItems({ onClick, mobile }: { onClick?: () => void; mobile?: boolean }) {
  return (
    <>
      {NAV.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          onClick={onClick}
          className={({ isActive }) =>
            cn(
              "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
              mobile ? "text-base" : "",
              isActive ? "bg-accent-soft text-primary" : "text-muted hover:bg-muted-bg hover:text-primary",
            )
          }
        >
          <Icon className="h-4 w-4" aria-hidden />
          {label}
        </NavLink>
      ))}
    </>
  );
}

export function Layout() {
  const [open, setOpen] = useState(false);
  const loc = useLocation();
  useEffect(() => {
    setOpen(false);
    window.scrollTo(0, 0);
  }, [loc.pathname]);

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-40 border-b border-border bg-white/95 backdrop-blur">
        <div className="container flex h-16 items-center justify-between gap-4">
          <NavLink to="/" aria-label="Bo‘g‘imTahlil — bosh sahifa"><Logo /></NavLink>
          <nav className="hidden items-center gap-1 lg:flex" aria-label="Asosiy menyu"><NavItems /></nav>
          <div className="flex items-center gap-2">
            <ModelStatusPill className="hidden sm:inline-flex" />
            <button
              className="inline-flex h-10 w-10 items-center justify-center rounded-md text-primary hover:bg-muted-bg lg:hidden"
              onClick={() => setOpen((v) => !v)}
              aria-expanded={open}
              aria-label={open ? "Menyuni yopish" : "Menyuni ochish"}
            >
              {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>
        {open && (
          <nav className="container flex flex-col gap-1 border-t border-border pb-4 pt-2 lg:hidden" aria-label="Mobil menyu">
            <NavItems mobile onClick={() => setOpen(false)} />
            <ModelStatusPill className="mt-2 self-start sm:hidden" />
          </nav>
        )}
      </header>

      <main className="flex-1 animate-fade-in" key={loc.pathname}>
        <Outlet />
      </main>

      <footer className="border-t border-border bg-white">
        <div className="container flex flex-col gap-2 py-6 text-xs text-muted md:flex-row md:items-center md:justify-between">
          <p>
            <span className="font-semibold text-primary">Bo‘g‘imTahlil 1.0</span> — “Aniq tahlil sari aqlli qadam!”
          </p>
          <p className="max-w-2xl md:text-right">
            Ilmiy-tadqiqot prototipi. Natijalar shifokor tashxisi o‘rnini bosmaydi va davolashni belgilash uchun ishlatilmaydi.
          </p>
        </div>
      </footer>
    </div>
  );
}
