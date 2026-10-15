import * as AD from "@radix-ui/react-alert-dialog";
import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "./button";

export function ConfirmDialog({
  trigger, title, description, confirmText, cancelText = "Bekor qilish", onConfirm,
}: {
  trigger: React.ReactNode;
  title: string;
  description: string;
  confirmText: string;
  cancelText?: string;
  onConfirm: () => void;
}) {
  return (
    <AD.Root>
      <AD.Trigger asChild>{trigger}</AD.Trigger>
      <AD.Portal>
        <AD.Overlay className="fixed inset-0 z-50 bg-[#0b1d33]/50 data-[state=open]:animate-in data-[state=open]:fade-in-0" />
        <AD.Content
          className={cn(
            "fixed left-1/2 top-1/2 z-50 w-[calc(100%-2rem)] max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border border-border bg-white p-6 shadow-xl",
            "data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95",
          )}
        >
          <AD.Title className="text-lg font-semibold text-primary">{title}</AD.Title>
          <AD.Description className="mt-2 text-sm leading-relaxed text-ink">{description}</AD.Description>
          <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            <AD.Cancel asChild><Button variant="outline">{cancelText}</Button></AD.Cancel>
            <AD.Action asChild><Button variant="danger" onClick={onConfirm}>{confirmText}</Button></AD.Action>
          </div>
        </AD.Content>
      </AD.Portal>
    </AD.Root>
  );
}
