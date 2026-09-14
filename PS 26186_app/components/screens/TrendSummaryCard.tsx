import { PersonalTrend } from "@/types/trends";
import { Card } from "@/components/ui/Card";
import { TrendingDown, TrendingUp, Minus } from "lucide-react";

export function TrendSummaryCard({ trend }: { trend: PersonalTrend }) {
  return (
    <Card className="flex flex-col gap-4">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider">7-Day Average</h3>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-3xl font-bold text-slate-100">{trend.averageStressIndex}</span>
            <span className="text-slate-500 text-sm">/ 100 Stress</span>
          </div>
        </div>
        <div className="flex flex-col items-end">
          <span className="text-slate-400 text-sm font-medium uppercase tracking-wider">Trend</span>
          {trend.trendDirection === "improving" && <div className="flex items-center text-teal-400 mt-1"><TrendingDown className="w-5 h-5 mr-1" /> Improving</div>}
          {trend.trendDirection === "worsening" && <div className="flex items-center text-red-400 mt-1"><TrendingUp className="w-5 h-5 mr-1" /> Worsening</div>}
          {trend.trendDirection === "stable" && <div className="flex items-center text-slate-400 mt-1"><Minus className="w-5 h-5 mr-1" /> Stable</div>}
        </div>
      </div>
      
      <div className="pt-4 border-t border-slate-700/50 flex justify-between">
        <div>
          <span className="text-slate-400 text-xs uppercase tracking-wider block mb-1">Avg Sleep</span>
          <p className="text-lg font-medium text-slate-200">{trend.averageSleepHours} hrs</p>
        </div>
        <div className="text-right">
          <span className="text-slate-400 text-xs uppercase tracking-wider block mb-1">Last Entry</span>
          <p className="text-lg font-medium text-slate-200">
            {trend.last7Days[trend.last7Days.length - 1].date.split('-').slice(1).join('/')}
          </p>
        </div>
      </div>
    </Card>
  );
}
