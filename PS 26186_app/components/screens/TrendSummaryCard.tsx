import { PersonalTrend } from "@/types/trends";
import { Card } from "@/components/ui/Card";
import { TrendingDown, TrendingUp, Minus } from "lucide-react";

export function TrendSummaryCard({ trend }: { trend: PersonalTrend }) {
  return (
    <Card className="flex flex-col gap-6 p-6 bg-mb-glass-strong backdrop-blur-xl border border-mb-glass-border shadow-[0_8px_30px_rgba(0,0,0,0.12)] rounded-3xl">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-mb-text-secondary text-xs font-bold uppercase tracking-widest mb-1">7-Day Average</h3>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-[40px] font-light text-mb-text-primary leading-none">{trend.averageStressIndex}</span>
            <span className="text-mb-text-muted text-xs font-medium uppercase tracking-wider">Risk Score</span>
          </div>
        </div>
        <div className="flex flex-col items-end">
          <span className="text-mb-text-secondary text-xs font-bold uppercase tracking-widest mb-1">Trajectory</span>
          {trend.trendDirection === "improving" && <div className="flex items-center text-mb-accent mt-1 font-semibold text-sm"><TrendingDown className="w-4 h-4 mr-1.5" /> Improving</div>}
          {trend.trendDirection === "worsening" && <div className="flex items-center text-mb-saffron mt-1 font-semibold text-sm"><TrendingUp className="w-4 h-4 mr-1.5" /> Worsening</div>}
          {trend.trendDirection === "stable" && <div className="flex items-center text-mb-text-secondary mt-1 font-semibold text-sm"><Minus className="w-4 h-4 mr-1.5" /> Stable</div>}
        </div>
      </div>
      
      <div className="pt-5 border-t border-mb-glass-border flex justify-between">
        <div>
          <span className="text-mb-text-secondary text-[10px] font-bold uppercase tracking-widest block mb-1">Avg Sleep</span>
          <p className="text-xl font-light text-mb-text-secondary">{trend.averageSleepHours} <span className="text-xs text-mb-text-muted">hrs</span></p>
        </div>
        <div className="text-right">
          <span className="text-mb-text-secondary text-[10px] font-bold uppercase tracking-widest block mb-1">Last Entry</span>
          <p className="text-xl font-light text-mb-text-secondary">
            {trend.last7Days && trend.last7Days.length > 0
              ? trend.last7Days[trend.last7Days.length - 1].date.split('-').slice(1).join('/')
              : 'No records'}
          </p>
        </div>
      </div>
    </Card>
  );
}


