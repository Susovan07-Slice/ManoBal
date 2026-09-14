"use client";

import { useEffect, useState } from "react";
import { getPersonalTrend } from "@/lib/mock-data";
import { PersonalTrend } from "@/types/trends";
import { TrendChart } from "@/components/screens/TrendChart";
import { TrendSummaryCard } from "@/components/screens/TrendSummaryCard";

export default function TrendsRoute() {
  const [trend, setTrend] = useState<PersonalTrend | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPersonalTrend().then((data) => {
      setTrend(data);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col h-full items-center justify-center text-slate-400 p-4">
        <div className="w-8 h-8 border-2 border-teal-500 border-t-transparent rounded-full animate-spin mb-4" />
        <p>Loading trends...</p>
      </div>
    );
  }

  if (!trend || trend.last7Days.length === 0) {
    return (
      <div className="flex flex-col h-full items-center justify-center text-slate-400 p-4 text-center">
        <div className="w-12 h-12 bg-slate-800 rounded-full flex items-center justify-center mb-4">
          <span className="text-slate-500">?</span>
        </div>
        <p className="text-lg text-slate-200 mb-2">No Data</p>
        <p className="text-sm">Not enough data to display trends.</p>
      </div>
    );
  }

  return (
    <div className="p-4 flex flex-col gap-6 animate-in fade-in duration-500 pb-20">
      <h2 className="text-xl font-semibold text-slate-100">Personal Insights</h2>
      
      <TrendSummaryCard trend={trend} />
      
      <div>
        <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-4">7-Day History</h3>
        <TrendChart data={trend.last7Days} />
      </div>
    </div>
  );
}
