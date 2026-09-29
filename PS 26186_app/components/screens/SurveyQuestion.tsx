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
    <div className="flex flex-col gap-6 animate-fade-up">
      <div>
        <h3 className="eyebrow mb-3">{question.category}</h3>
        <p className="text-xl font-semibold text-ink leading-snug">{question.promptSummary}</p>
      </div>
      
      <div className="flex flex-col gap-3 mt-2">
        {OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => onAnswer(opt.value)}
            className={cn(
              "p-4 rounded-2xl flex items-center justify-between transition-all border text-left min-h-[56px]",
              value === opt.value
                ? "bg-brand-100 border-brand-500 text-brand-600"
                : "bg-white/70 backdrop-blur-sm border-sky-200 text-ink-2 hover:bg-white hover:text-ink"
            )}
          >
            <span className="text-[15px] font-medium">{opt.label}</span>
            <div className={cn(
              "w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0",
              value === opt.value ? "border-brand-500" : "border-ink-3"
            )}>
              {value === opt.value && <div className="w-2.5 h-2.5 bg-brand-500 rounded-full" />}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
