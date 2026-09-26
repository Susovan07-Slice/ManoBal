import { PersonalTrend } from "@/types/trends";
import { Card } from "@/components/ui/Card";
import { TrendingDown, TrendingUp, Minus } from "lucide-react";

export function TrendSummaryCard({ trend }: { trend: PersonalTrend }) {
  return (
    <Card className="flex flex-col gap-6 p-6 bg-[var(--color-glass-dark)] backdrop-blur-xl border border-[var(--color-glass-border)] shadow-2xl rounded-3xl">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-slate-400 text-xs font-bold uppercase tracking-widest mb-1">7-Day Average</h3>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-[40px] font-light text-white leading-none">{trend.averageStressIndex}</span>
            <span className="text-slate-500 text-xs font-medium uppercase tracking-wider">Risk Score</span>
          </div>
        </div>
        <div className="flex flex-col items-end">
          <span className="text-slate-400 text-xs font-bold uppercase tracking-widest mb-1">Trajectory</span>
          {trend.trendDirection === "improving" && <div className="flex items-center text-teal-400 mt-1 font-semibold text-sm"><TrendingDown className="w-4 h-4 mr-1.5" /> Improving</div>}
          {trend.trendDirection === "worsening" && <div className="flex items-center text-saffron mt-1 font-semibold text-sm"><TrendingUp className="w-4 h-4 mr-1.5" /> Worsening</div>}
          {trend.trendDirection === "stable" && <div className="flex items-center text-slate-400 mt-1 font-semibold text-sm"><Minus className="w-4 h-4 mr-1.5" /> Stable</div>}
        </div>
      </div>
      
      <div className="pt-5 border-t border-[var(--color-glass-border)] flex justify-between">
        <div>
          <span className="text-slate-400 text-[10px] font-bold uppercase tracking-widest block mb-1">Avg Sleep</span>
          <p className="text-xl font-light text-slate-200">{trend.averageSleepHours} <span className="text-xs text-slate-500">hrs</span></p>
        </div>
        <div className="text-right">
          <span className="text-slate-400 text-[10px] font-bold uppercase tracking-widest block mb-1">Last Entry</span>
          <p className="text-xl font-light text-slate-200">
            {trend.last7Days && trend.last7Days.length > 0
              ? trend.last7Days[trend.last7Days.length - 1].date.split('-').slice(1).join('/')
              : 'No records'}
          </p>
        </div>
      </div>
    </Card>
  );
}
