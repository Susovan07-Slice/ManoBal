import { SurveyQuestion as SurveyQuestionType } from "@/types/survey";
import { cn } from "@/lib/utils";

const OPTIONS = [
  { value: 0, label: "Not at all" },
  { value: 1, label: "Several days" },
  { value: 2, label: "More than half the days" },
  { value: 3, label: "Nearly every day" },
];

export function SurveyQuestion({
  question,
  value,
  onAnswer
}: {
  question: SurveyQuestionType;
  value: number | null;
  onAnswer: (v: number) => void;
}) {
  return (
    <div className="flex flex-col gap-6 animate-in slide-in-from-right-8 fade-in duration-300">
      <div>
        <h3 className="text-teal-400 text-sm font-medium uppercase tracking-wider mb-3">{question.category}</h3>
        <p className="text-xl font-medium text-slate-100 leading-snug">{question.promptSummary}</p>
      </div>
      
      <div className="flex flex-col gap-3 mt-2">
        {OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => onAnswer(opt.value)}
            className={cn(
              "p-4 rounded-2xl flex items-center justify-between transition-colors border text-left min-h-[64px]",
              value === opt.value
                ? "bg-teal-500/10 border-teal-500 text-teal-400"
                : "bg-[#1C2530] border-slate-700 text-slate-300 hover:bg-slate-800"
            )}
          >
            <span className="text-base font-medium">{opt.label}</span>
            <div className={cn(
              "w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0",
              value === opt.value ? "border-teal-500" : "border-slate-600"
            )}>
              {value === opt.value && <div className="w-2.5 h-2.5 bg-teal-500 rounded-full" />}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
