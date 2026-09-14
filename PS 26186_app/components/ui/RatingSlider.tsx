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
         <div className="flex justify-between items-center">
           <span className="text-slate-200 font-medium">{label}</span>
           <span className="text-teal-400 font-bold text-lg">{value} hrs</span>
         </div>
         <input 
           type="range" 
           min={0} max={16} step={0.5} 
           value={value} 
           onChange={(e) => onChange(parseFloat(e.target.value))}
           className="w-full h-3 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-teal-500"
         />
       </div>
     )
  }

  return (
    <div className="flex flex-col gap-3 py-2">
      <div className="flex justify-between items-center">
        <span className="text-slate-200 font-medium">{label}</span>
        <span className="text-teal-400 font-bold">{value > 0 ? value : '-'}</span>
      </div>
      <div className="flex justify-between gap-2">
        {options.map((opt) => (
          <button
            key={opt}
            onClick={() => onChange(opt)}
            className={cn(
              "flex-1 h-14 rounded-xl flex items-center justify-center text-lg font-medium transition-colors border",
              value === opt 
                ? "bg-teal-500 text-slate-900 border-teal-500" 
                : "bg-[#1C2530] text-slate-400 border-slate-700 hover:bg-slate-800"
            )}
          >
            {opt}
          </button>
        ))}
      </div>
    </div>
  );
}
