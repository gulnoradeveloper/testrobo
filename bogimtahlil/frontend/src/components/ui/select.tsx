import * as React from "react";
import { cn } from "@/lib/utils";

/** Mahalliy <select> — mobil qurilmalarda tizim tanlagichi ochiladi. */
export const NativeSelect = React.forwardRef<HTMLSelectElement, React.SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, ...props }, ref) => (
    <select
      ref={ref}
      className={cn("h-10 rounded-md border border-border bg-white px-3 text-sm text-ink focus-visible:ring-2 focus-visible:ring-accent", className)}
      {...props}
    />
  ),
);
NativeSelect.displayName = "NativeSelect";

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn("h-10 rounded-md border border-border bg-white px-3 text-sm text-ink focus-visible:ring-2 focus-visible:ring-accent", className)}
      {...props}
    />
  ),
);
Input.displayName = "Input";
