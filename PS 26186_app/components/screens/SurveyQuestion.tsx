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
        <h3 className="text-mb-accent text-sm font-medium uppercase tracking-wider mb-3">{question.category}</h3>
        <p className="text-xl font-medium text-mb-text-primary leading-snug">{question.promptSummary}</p>
      </div>
      
      <div className="flex flex-col gap-3 mt-2">
        {OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => onAnswer(opt.value)}
            className={cn(
              "p-4 rounded-2xl flex items-center justify-between transition-colors border text-left min-h-[64px]",
              value === opt.value
                ? "bg-mb-accent/10 border-mb-accent text-mb-accent"
                : "bg-mb-glass-strong backdrop-blur-md border-mb-glass-border text-mb-text-secondary hover:bg-slate-800/50"
            )}
          >
            <span className="text-base font-medium">{opt.label}</span>
            <div className={cn(
              "w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0",
              value === opt.value ? "border-mb-accent" : "border-slate-600"
            )}>
              {value === opt.value && <div className="w-2.5 h-2.5 bg-mb-accent rounded-full" />}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}


