import { PersonalTrend } from "@/types/trends";
import { Card } from "@/components/ui/Card";
import { TrendingDown, TrendingUp, Minus } from "lucide-react";

export function TrendSummaryCard({ trend }: { trend: PersonalTrend }) {
  return (
    <Card className="glass-card p-6 animate-fade-up">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="eyebrow mb-1">7-Day Average</h3>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-5xl font-semibold text-ink leading-none tabular-nums">{trend.averageStressIndex}</span>
            <span className="text-ink-3 text-sm font-medium">Risk Score</span>
          </div>
        </div>
        <div className="flex flex-col items-end">
          <span className="eyebrow mb-1">Trajectory</span>
          {trend.trendDirection === "improving" && <div className="flex items-center text-ok font-semibold text-sm mt-1"><TrendingDown className="w-4 h-4 mr-1.5" /> Improving</div>}
          {trend.trendDirection === "worsening" && <div className="flex items-center text-warn font-semibold text-sm mt-1"><TrendingUp className="w-4 h-4 mr-1.5" /> Worsening</div>}
          {trend.trendDirection === "stable" && <div className="flex items-center text-ink-3 font-semibold text-sm mt-1"><Minus className="w-4 h-4 mr-1.5" /> Stable</div>}
        </div>
      </div>
      
      <div className="pt-5 border-t border-sky-200/50 flex justify-between mt-5">
        <div>
          <span className="eyebrow block mb-1">Avg Sleep</span>
          <p className="text-2xl font-semibold text-ink">{trend.averageSleepHours} <span className="text-sm text-ink-3">hrs</span></p>
        </div>
        <div className="text-right">
          <span className="eyebrow block mb-1">Last Entry</span>
          <p className="text-2xl font-semibold text-ink">
            {trend.last7Days && trend.last7Days.length > 0
              ? trend.last7Days[trend.last7Days.length - 1].date.split('-').slice(1).join('/')
              : 'No records'}
          </p>
        </div>
      </div>
    </Card>
  );
}
