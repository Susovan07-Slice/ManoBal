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
           <span className="text-offwhite font-medium">{label}</span>
           <span className="text-teal-400 font-bold text-lg tracking-wide">{value} hrs</span>
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
        <span className="text-offwhite font-medium">{label}</span>
        <span className="text-teal-400 font-bold tracking-wide">{value > 0 ? value : '-'}</span>
      </div>
      <div className="flex justify-between gap-2">
        {options.map((opt) => (
          <button
            key={opt}
            onClick={() => onChange(opt)}
            className={cn(
              "flex-1 h-14 rounded-2xl flex items-center justify-center text-lg font-medium transition-all duration-300 border",
              value === opt 
                ? "bg-teal-600 text-offwhite border-teal-500 shadow-lg shadow-teal-500/20 transform scale-[1.02]" 
                : "bg-[var(--color-glass-dark)] text-slate-400 border-[var(--color-glass-border)] hover:bg-white/10 hover:text-slate-200"
            )}
          >
            {opt}
          </button>
        ))}
      </div>
    </div>
  );
}
