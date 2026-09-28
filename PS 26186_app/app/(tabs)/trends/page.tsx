"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/lib/AuthContext";
import { getAssessmentHistory } from "@/lib/assessment";
import { computePersonalTrend } from "@/lib/trends";
import { StressAssessmentOut } from "@/types/api";
import { PersonalTrend } from "@/types/trends";
import { RiskCalendarHeatmap } from "@/components/screens/RiskCalendarHeatmap";
import { TrendChart } from "@/components/screens/TrendChart";
import { TrendSummaryCard } from "@/components/screens/TrendSummaryCard";
import Link from "next/link";
import { Activity, AlertCircle, Calendar, RefreshCw, ShieldAlert, ArrowRight } from "lucide-react";

export default function TrendsRoute() {
  const { user } = useAuth();
  const [assessments, setAssessments] = useState<StressAssessmentOut[]>([]);
  const [trend, setTrend] = useState<PersonalTrend | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTrends = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const pid = user?.personnel_id || 1;
      const data = await getAssessmentHistory(pid);
      setAssessments(data);
      setTrend(computePersonalTrend(data));
    } catch (err: any) {
      console.error("Failed to load assessments:", err);
      setError(err.message || "Failed to load health trends from server.");
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchTrends();
  }, [fetchTrends]);

  if (loading) {
    return (
      <div className="flex flex-col h-full items-center justify-center p-6 text-center">
        <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-sm font-medium text-ink">Retrieving Telemetry Trends...</p>
        <span className="text-[12px] text-ink-3 mt-1 font-medium">Querying FastAPI assessment history</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col h-full items-center justify-center p-6 text-center">
        <div className="w-12 h-12 rounded-full bg-alert-bg flex items-center justify-center mb-4">
          <AlertCircle className="w-6 h-6 text-alert" />
        </div>
        <p className="text-ink font-medium mb-1">Telemetry Synchronization Failed</p>
        <p className="text-[13px] text-ink-2 mb-4 max-w-xs">{error}</p>
        <button
          onClick={fetchTrends}
          className="flex items-center gap-2 px-5 py-2.5 bg-white hover:bg-sky-50 text-brand-500 text-[13px] font-semibold rounded-full border border-sky-200 shadow-sm transition"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Retry Sync
        </button>
      </div>
    );
  }

  if (!trend || trend.last7Days.length === 0) {
    return (
      <div className="flex flex-col h-full items-center justify-center p-6 text-center">
        <div className="w-14 h-14 bg-brand-100 rounded-2xl flex items-center justify-center mb-4">
          <Activity className="w-7 h-7 text-brand-500" />
        </div>
        <p className="text-lg font-semibold text-ink mb-1">No Assessment History</p>
        <p className="text-[13px] text-ink-2 mb-6 max-w-xs">
          You haven&apos;t completed any wellness assessments yet. Take your first assessment to establish a health baseline.
        </p>
        <Link
          href="/assessment"
          className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-brand-500 to-brand-600 text-white font-semibold text-[13px] rounded-full shadow-[0_16px_40px_rgba(31,110,140,0.22)] active:scale-[.97] transition"
        >
          Begin Self-Assessment <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    );
  }

  return (
    <div className="p-4 flex flex-col gap-5 pb-44 min-w-0 animate-fade-up">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-[22px] font-bold text-ink">Personal Insights</h2>
          <p className="text-[13px] text-ink-3 mt-0.5">Real-time stress and operational telemetry tracking</p>
        </div>
        <button
          onClick={fetchTrends}
          className="w-10 h-10 bg-white/70 backdrop-blur-sm hover:bg-white text-ink-3 hover:text-ink rounded-full border border-sky-200 shadow-sm transition flex items-center justify-center"
          title="Refresh telemetry"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>
      
      {/* Summary Card */}
      <TrendSummaryCard trend={trend} />
      
      {/* Assessment Trajectory Chart */}
      <div className="animate-fade-up stagger-1">
        <div className="flex items-center justify-between mb-3">
          <h3 className="eyebrow">
            Assessment Trajectory ({trend.last7Days.length} Records)
          </h3>
        </div>
        <div className="glass-card p-5 w-full h-[220px]">
          <TrendChart data={trend.last7Days} />
        </div>
      </div>

      {/* Calendar Heatmap */}
      <div className="animate-fade-up stagger-2">
        <RiskCalendarHeatmap assessments={assessments} onRefresh={fetchTrends} />
      </div>

      {/* Assessment Log */}
      <div className="mt-2 animate-fade-up stagger-3">
        <h3 className="eyebrow mb-4">
          Assessment Log
        </h3>
        <div className="space-y-3">
          {assessments.slice(0, 5).map((a) => (
            <div
              key={a.id}
              className="bg-white rounded-[20px] shadow-[0_10px_30px_rgba(31,110,140,0.08)] border border-white/80 p-5 flex flex-col gap-3 hover:shadow-[0_10px_30px_rgba(31,110,140,0.14)] transition-all duration-200"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-full bg-brand-100 flex items-center justify-center">
                    <Calendar className="w-4 h-4 text-brand-500" />
                  </div>
                  <span className="text-[13px] font-semibold text-ink">
                    {new Date(a.assessment_timestamp).toLocaleDateString(undefined, {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </span>
                </div>
                <span
                  className={`text-[11px] font-bold uppercase tracking-wider px-3 py-1.5 rounded-full ${
                    a.stress_level === 'High'
                      ? 'bg-alert-bg text-alert'
                      : a.stress_level === 'Medium'
                      ? 'bg-warn-bg text-warn'
                      : 'bg-ok-bg text-ok'
                  }`}
                >
                  {a.stress_level}
                </span>
              </div>

              <div className="flex items-center justify-between text-[13px] pt-3 border-t border-sky-200/50">
                <span className="text-ink-3 text-[11px] font-semibold uppercase tracking-wide">
                  Score: <strong className="text-ink text-[14px] tabular-nums">
                    {typeof a.risk_score === 'number' ? a.risk_score.toFixed(1) : a.risk_score}/100
                  </strong>
                </span>
                <span className="text-ink-3 text-[11px] font-semibold uppercase tracking-wide">
                  Priority: <strong className="text-ink text-[13px]">{a.risk_priority}</strong>
                </span>
              </div>


              {a.key_factors && a.key_factors.length > 0 && (
                <div className="pt-3 border-t border-sky-200/50">
                  <span className="eyebrow block mb-2">
                    Key Factors
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {a.key_factors.slice(0, 3).map((f, i) => (
                      <span key={i} className="bg-sky-50 text-ink-2 text-[11px] font-medium px-3 py-1.5 rounded-full border border-sky-200">
                        {f}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}
