"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/lib/AuthContext";
import { getAssessmentHistory } from "@/lib/assessment";
import { computePersonalTrend } from "@/lib/trends";
import { StressAssessmentOut } from "@/types/api";
import { PersonalTrend } from "@/types/trends";
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
      <div className="flex flex-col h-full items-center justify-center text-slate-400 p-6 text-center">
        <div className="w-8 h-8 border-2 border-teal-500 border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-sm font-medium text-slate-300">Retrieving Telemetry Trends...</p>
        <span className="text-xs text-slate-500 mt-1 font-mono">Querying FastAPI assessment history</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col h-full items-center justify-center text-slate-400 p-6 text-center">
        <div className="w-12 h-12 rounded-full bg-rose-500/10 text-rose-400 flex items-center justify-center mb-4">
          <AlertCircle className="w-6 h-6" />
        </div>
        <p className="text-slate-200 font-medium mb-1">Telemetry Synchronization Failed</p>
        <p className="text-xs text-slate-400 mb-4 max-w-xs">{error}</p>
        <button
          onClick={fetchTrends}
          className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-teal-400 text-xs font-semibold rounded-lg transition"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Retry Sync
        </button>
      </div>
    );
  }

  if (!trend || trend.last7Days.length === 0) {
    return (
      <div className="flex flex-col h-full items-center justify-center text-slate-400 p-6 text-center">
        <div className="w-14 h-14 bg-slate-800/80 rounded-2xl flex items-center justify-center mb-4 border border-slate-700">
          <Activity className="w-7 h-7 text-teal-400" />
        </div>
        <p className="text-lg font-semibold text-slate-100 mb-1">No Assessment History</p>
        <p className="text-xs text-slate-400 mb-6 max-w-xs">
          You haven&apos;t completed any wellness assessments yet. Take your first assessment to establish a health baseline.
        </p>
        <Link
          href="/assessment"
          className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-teal-500 to-emerald-600 text-slate-950 font-semibold text-xs rounded-xl shadow-lg shadow-teal-500/20 active:scale-95 transition"
        >
          Begin Self-Assessment <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    );
  }

  return (
    <div className="p-4 flex flex-col gap-6 animate-in fade-in duration-500 pb-20">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-100">Personal Insights</h2>
          <p className="text-xs text-slate-400 mt-0.5">Real-time stress and operational telemetry tracking</p>
        </div>
        <button
          onClick={fetchTrends}
          className="p-2 bg-slate-800/60 hover:bg-slate-800 text-slate-400 hover:text-teal-400 rounded-lg border border-slate-700/60 transition"
          title="Refresh telemetry"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>
      
      <TrendSummaryCard trend={trend} />
      
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Assessment Trajectory ({trend.last7Days.length} Records)
          </h3>
          <span className="text-[10px] text-teal-400/80 font-mono">Real Backend Data</span>
        </div>
        <TrendChart data={trend.last7Days} />
      </div>

      {/* Historical Assessment Log */}
      <div>
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
          Assessment Log
        </h3>
        <div className="space-y-2.5">
          {assessments.slice(0, 5).map((a) => (
            <div
              key={a.id}
              className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-3.5 flex flex-col gap-2 hover:border-slate-700 transition"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Calendar className="w-3.5 h-3.5 text-slate-400" />
                  <span className="text-xs font-mono text-slate-300">
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
                  className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full ${
                    a.stress_level === 'High'
                      ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                      : a.stress_level === 'Medium'
                      ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                      : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                  }`}
                >
                  {a.stress_level} Stress
                </span>
              </div>

              <div className="flex items-center justify-between text-xs pt-1 border-t border-slate-800/50">
                <span className="text-slate-400">
                  Risk Score: <strong className="text-slate-200">{Math.round(a.risk_score)}/100</strong>
                </span>
                <span className="text-slate-400">
                  Priority: <strong className="text-slate-200">{a.risk_priority}</strong>
                </span>
              </div>

              {a.key_factors && a.key_factors.length > 0 && (
                <div className="text-[11px] text-slate-400 pt-1">
                  <span className="text-slate-500 block text-[10px] uppercase tracking-wide">
                    Factors associated with this model prediction:
                  </span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {a.key_factors.slice(0, 3).map((f, i) => (
                      <span key={i} className="bg-slate-800 text-slate-300 text-[10px] px-2 py-0.5 rounded">
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

      {/* Prototype Notice */}
      <div className="p-3 bg-slate-900/40 border border-slate-800/60 rounded-xl flex items-start gap-2.5">
        <ShieldAlert className="w-4 h-4 text-teal-500/70 shrink-0 mt-0.5" />
        <p className="text-[11px] text-slate-400 leading-relaxed">
          <strong>Prototype Notice:</strong> Predictions are decision-support indicators and are not medical diagnoses or disciplinary decisions.
        </p>
      </div>
    </div>
  );
}
