import { PersonalTrend } from "@/types/trends";
import { Card } from "@/components/ui/Card";
import { TrendingDown, TrendingUp, Minus } from "lucide-react";

export function TrendSummaryCard({ trend }: { trend: PersonalTrend }) {
  return (
    <Card className="flex flex-col gap-5 p-6 bg-white/85 backdrop-blur-xl border border-white/60 shadow-[0_8px_40px_rgba(0,0,0,0.08)] rounded-2xl">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-gray-500 text-[11px] font-bold uppercase tracking-widest mb-1">7-Day Average</h3>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-5xl font-light text-gray-900 leading-none">{trend.averageStressIndex}</span>
            <span className="text-gray-400 text-sm font-medium uppercase tracking-wider">Risk Score</span>
          </div>
        </div>
        <div className="flex flex-col items-end">
          <span className="text-gray-500 text-[11px] font-bold uppercase tracking-widest mb-1">Trajectory</span>
          {trend.trendDirection === "improving" && <div className="flex items-center text-emerald-600 mt-1 font-semibold text-sm"><TrendingDown className="w-4 h-4 mr-1.5" /> Improving</div>}
          {trend.trendDirection === "worsening" && <div className="flex items-center text-amber-600 mt-1 font-semibold text-sm"><TrendingUp className="w-4 h-4 mr-1.5" /> Worsening</div>}
          {trend.trendDirection === "stable" && <div className="flex items-center text-gray-500 mt-1 font-semibold text-sm"><Minus className="w-4 h-4 mr-1.5" /> Stable</div>}
        </div>
      </div>
      
      <div className="pt-5 border-t border-gray-200 flex justify-between">
        <div>
          <span className="text-gray-500 text-[10px] font-bold uppercase tracking-widest block mb-1">Avg Sleep</span>
          <p className="text-2xl font-light text-gray-800">{trend.averageSleepHours} <span className="text-sm text-gray-400">hrs</span></p>
        </div>
        <div className="text-right">
          <span className="text-gray-500 text-[10px] font-bold uppercase tracking-widest block mb-1">Last Entry</span>
          <p className="text-2xl font-light text-gray-800">
            {trend.last7Days && trend.last7Days.length > 0
              ? trend.last7Days[trend.last7Days.length - 1].date.split('-').slice(1).join('/')
              : 'No records'}
          </p>
        </div>
      </div>
    </Card>
  );
}
