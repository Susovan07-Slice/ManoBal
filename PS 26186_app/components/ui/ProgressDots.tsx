import { cn } from "@/lib/utils";

export function ProgressDots({ current, total }: { current: number; total: number }) {
  return (
    <div className="flex items-center justify-center gap-1.5 py-4">
      {Array.from({ length: total }).map((_, i) => (
        <div
          key={i}
          className={cn(
            "h-2 rounded-full transition-all duration-300",
            i === current ? "w-6 bg-mb-accent" : i < current ? "w-2 bg-teal-800" : "w-2 bg-slate-800"
          )}
        />
      ))}
    </div>
  );
}


