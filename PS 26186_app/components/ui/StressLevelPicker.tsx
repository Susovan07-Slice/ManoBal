import { cn } from "@/lib/utils";

interface StressLevelPickerProps {
  value: number;
  onChange: (v: number) => void;
  className?: string;
}

const STRESS_LEVELS = [
  { level: 1, label: "Very Calm", emoji: "😌" },
  { level: 2, label: "Calm", emoji: "🙂" },
  { level: 3, label: "Slightly Stressed", emoji: "😐" },
  { level: 4, label: "Moderate", emoji: "😕" },
  { level: 5, label: "Stressed", emoji: "😟" },
  { level: 6, label: "Highly Stressed", emoji: "😨" },
  { level: 7, label: "Extremely Stressed", emoji: "😫" },
];

export function StressLevelPicker({ value, onChange, className }: StressLevelPickerProps) {
  return (
    <div className={cn("flex flex-col gap-3 py-2", className)}>
      <div className="flex justify-between items-center px-1 mb-1">
        <span className="text-ink-2 font-semibold text-[13px] uppercase tracking-wide">Stress Level</span>
        {value > 0 && (
          <span className="text-brand-500 font-bold text-sm">
            {STRESS_LEVELS.find(s => s.level === value)?.label}
          </span>
        )}
      </div>
      
      <div className="flex justify-between items-center gap-1.5 p-2 bg-white/60 backdrop-blur-md rounded-[20px] border border-sky-200/60 shadow-sm overflow-hidden">
        {STRESS_LEVELS.map((item) => {
          const isSelected = value === item.level;
          return (
            <button
              key={item.level}
              type="button"
              onClick={() => onChange(item.level)}
              title={item.label}
              className={cn(
                "flex-1 flex flex-col items-center justify-center py-2 px-1 rounded-[14px] transition-all duration-200",
                isSelected
                  ? "bg-brand-100 border border-brand-500/30 shadow-[0_4px_12px_rgba(42,155,200,0.15)] scale-[1.05]"
                  : "bg-transparent border border-transparent hover:bg-white/80"
              )}
            >
              <span className={cn(
                "text-[26px] leading-none transition-transform duration-200",
                isSelected ? "scale-110 drop-shadow-sm" : "opacity-75 grayscale-[30%] scale-95"
              )}>
                {item.emoji}
              </span>
            </button>
          );
        })}
      </div>
      <div className="flex justify-between px-2 text-[11px] text-ink-3 font-medium">
        <span>Very Calm</span>
        <span>Extremely Stressed</span>
      </div>
    </div>
  );
}
