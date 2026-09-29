import { cn } from "@/lib/utils";
import { Button } from "./Button";
import { X } from "lucide-react";

interface ConfirmSheetProps {
  open: boolean;
  title?: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
  confirmLabel?: string;
  cancelLabel?: string;
  isDanger?: boolean;
}

export function ConfirmSheet({
  open,
  title,
  message,
  onConfirm,
  onCancel,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  isDanger = false
}: ConfirmSheetProps) {
  if (!open) return null;

  return (
    <div className="absolute inset-0 z-[60] flex flex-col justify-end bg-black/40 backdrop-blur-sm animate-in fade-in">
      <div className="relative bg-white w-full rounded-t-[28px] p-6 shadow-[0_-16px_40px_rgba(31,110,140,0.15)] border-t border-white/60 animate-in slide-in-from-bottom-full pb-8">
        <div className="w-10 h-1 bg-ink-3/30 rounded-full mx-auto mb-4" />
        <button
          onClick={onCancel}
          className="absolute top-5 right-5 p-2 text-ink-3 hover:text-ink bg-sky-50 hover:bg-sky-100 rounded-full transition-colors z-10"
          aria-label="Close"
        >
          <X className="w-5 h-5" />
        </button>
        {title && <h2 className="text-xl font-semibold mb-2 text-ink pr-8">{title}</h2>}
        <p className="text-ink-2 mb-8">{message}</p>
        <div className="flex flex-col gap-3">
          <Button variant={isDanger ? "danger" : "primary"} onClick={onConfirm}>
            {confirmLabel}
          </Button>
          <Button variant="ghost" onClick={onCancel}>
            {cancelLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
