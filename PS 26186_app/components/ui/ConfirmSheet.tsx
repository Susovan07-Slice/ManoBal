import { cn } from "@/lib/utils";
import { Button } from "./Button";

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
    <div className="absolute inset-0 z-50 flex flex-col justify-end bg-black/60 backdrop-blur-sm animate-in fade-in">
      <div className="bg-[#1C2530] w-full rounded-t-3xl p-6 shadow-2xl border-t border-slate-700 animate-in slide-in-from-bottom-full pb-safe">
        {title && <h2 className="text-xl font-semibold mb-2 text-slate-100">{title}</h2>}
        <p className="text-slate-300 mb-8">{message}</p>
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
