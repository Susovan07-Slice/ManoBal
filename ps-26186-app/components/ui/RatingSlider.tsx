import { cn } from "@/lib/utils";

interface RatingSliderProps {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
  type?: "hours" | "scale";
}

export function RatingSlider({ label, value, onChange, min = 1, max = 5, type = "scale" }: RatingSliderProps) {
  const options = Array.from({ length: max - min + 1 }, (_, i) => min + i);
  
  if (type === "hours") {
     return (
       <div className="flex flex-col gap-3 py-2">
        <div className="flex justify-between items-center px-1">
           <span className="text-ink-2 font-medium text-[13px]">{label}</span>
           <span className="text-brand-500 font-bold text-2xl tabular-nums">{value} hrs</span>
         </div>
           <input 
             type="range" 
             min={0} max={16} step={0.5} 
             value={value} 
             onChange={(e) => onChange(parseFloat(e.target.value))}
             className="w-full"
           />
       </div>
     )
  }

  return (
    <div className="flex flex-col gap-3 py-2">
      <div className="flex justify-between items-center px-1">
        <span className="text-ink-2 font-medium text-[13px]">{label}</span>
        <span className="text-brand-500 font-bold text-2xl tabular-nums">{value > 0 ? value : '-'}</span>
      </div>
      <div className="flex justify-between gap-2">
        {options.map((opt) => (
          <button
            key={opt}
            onClick={() => onChange(opt)}
            className={cn(
              "rounded-2xl border h-14 flex-1 text-lg font-medium transition-all duration-200",
              value === opt 
                ? "bg-brand-100 text-brand-600 border-brand-500 shadow-[0_4px_16px_rgba(42,155,200,0.15)] scale-[1.02]" 
                : "bg-white/70 text-ink-2 border-sky-200 hover:bg-white hover:text-ink"
            )}
          >
            {opt}
          </button>
        ))}
      </div>
    </div>
  );
}


