import { cva, type VariantProps } from "class-variance-authority";
import { AlertTriangle, CheckCircle2, Info, XCircle } from "lucide-react";
import * as React from "react";
import { cn } from "@/lib/utils";

const alertVariants = cva("flex gap-3 rounded-lg border p-4 text-sm [&>svg]:mt-0.5 [&>svg]:size-5 [&>svg]:shrink-0", {
  variants: {
    variant: {
      info: "border-accent/20 bg-accent-soft text-ink [&>svg]:text-accent",
      warning: "border-warning/30 bg-warning-soft text-ink [&>svg]:text-warning",
      danger: "border-danger/30 bg-danger-soft text-ink [&>svg]:text-danger",
      success: "border-success/30 bg-success-soft text-ink [&>svg]:text-success",
    },
  },
  defaultVariants: { variant: "info" },
});

const icons = { info: Info, warning: AlertTriangle, danger: XCircle, success: CheckCircle2 };

export function Alert({
  className, variant = "info", title, children, ...props
}: React.HTMLAttributes<HTMLDivElement> & VariantProps<typeof alertVariants> & { title?: string }) {
  const Icon = icons[variant ?? "info"];
  return (
    <div role={variant === "danger" ? "alert" : "status"} className={cn(alertVariants({ variant }), className)} {...props}>
      <Icon aria-hidden />
      <div className="space-y-1">
        {title && <p className="font-semibold text-primary">{title}</p>}
        <div className="leading-relaxed">{children}</div>
      </div>
    </div>
  );
}
