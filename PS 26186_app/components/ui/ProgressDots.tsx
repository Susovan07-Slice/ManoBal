import { cn } from "@/lib/utils";

export function ProgressDots({ current, total }: { current: number; total: number }) {
  return (
    <div className="flex items-center gap-2 py-4">
      <div className="flex items-center gap-1 flex-1">
        {Array.from({ length: total }).map((_, i) => (
          <div
            key={i}
            className={cn(
              "h-1.5 rounded-full flex-1 transition-all duration-300",
              i <= current ? "bg-brand-500" : "bg-white/70"
            )}
          />
        ))}
      </div>
      <span className="text-[13px] font-medium text-ink-3 tabular-nums">{String(current + 1).padStart(2, '0')} / {String(total).padStart(2, '0')}</span>
    </div>
  );
}


