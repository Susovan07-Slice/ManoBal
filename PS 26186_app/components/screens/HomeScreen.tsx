"use client";

import React, { useState } from "react";
import { PersonalTrend } from "@/types/trends";
import { StressAssessmentOut, AssessmentScheduleStatus, WelfareRequestOut } from "@/types/api";
import { TrendSummaryCard } from "./TrendSummaryCard";
import { WelfareSupportSheet } from "./WelfareSupportSheet";
import Link from "next/link";
import {
  ClipboardList,
  HeartPulse,
  Activity,
  ArrowRight,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Calendar,
  Sparkles,
  ShieldCheck,
  LifeBuoy,
  Plus,
  Send,
  MessageSquare,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { apiClient } from "@/lib/api";

export function HomeScreen({
  scheduleStatus,
  latestAssessment,
  trend,
  username,
  welfareRequests = [],
  onRefresh,
}: {
  scheduleStatus: AssessmentScheduleStatus | null;
  latestAssessment: StressAssessmentOut | null;
  trend: PersonalTrend;
  username?: string;
  welfareRequests?: WelfareRequestOut[];
  onRefresh?: () => void;
}) {
  const [updatingRecId, setUpdatingRecId] = useState<number | null>(null);
  const [showSupportSheet, setShowSupportSheet] = useState(false);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good Morning";
    if (hour < 17) return "Good Afternoon";
    return "Good Evening";
  };

  const handleCompleteRec = async (recId: number) => {
    setUpdatingRecId(recId);
    try {
      await apiClient(`/recommendations/${recId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status: "completed" }),
      });
      if (onRefresh) onRefresh();
    } catch (err: any) {
      alert(`Could not update recommendation: ${err?.message || "Error"}`);
    } finally {
      setUpdatingRecId(null);
    }
  };

  const handleWelfareSuccess = (newReq: WelfareRequestOut) => {
    if (onRefresh) onRefresh();
  };

  const isAssessmentDue = scheduleStatus ? scheduleStatus.assessment_due : !latestAssessment;

  return (
    <div className="flex flex-col gap-5 animate-in fade-in duration-500 pb-20">
      {/* 1. Greeting & User Context */}
      <div className="flex justify-between items-start">
        <div>
          <span className="text-[11px] uppercase font-mono tracking-widest text-teal-400 font-semibold block">
            Operational Welfare Portal
          </span>
          <h2 className="text-xl font-bold text-slate-100">
            {getGreeting()},{" "}
            <span className="text-teal-400 capitalize">{username || "Jawan"}</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            ManoBal continuous stress risk & duty wellness monitoring
          </p>
        </div>
      </div>

      {/* 2. Today's Assessment Status Card (Section 13) */}
      <div>
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center justify-between">
          <span>Today&apos;s Assessment</span>
          {scheduleStatus?.last_assessment_at && (
            <span className="text-[10px] text-slate-400 font-mono flex items-center gap-1">
              <Clock className="w-3 h-3 text-teal-400" />
              {scheduleStatus.hours_since_last_assessment !== null && (
                <span>{scheduleStatus.hours_since_last_assessment}h ago</span>
              )}
            </span>
          )}
        </h3>

        {isAssessmentDue ? (
          /* Assessment is Due */
          <Card className="p-4 bg-gradient-to-r from-amber-950/40 via-slate-900 to-slate-900 border-l-4 border-l-amber-500 border-amber-500/30 rounded-xl space-y-3 shadow-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-amber-400 font-mono text-xs uppercase font-semibold">
                <AlertTriangle className="w-4 h-4" />
                <span>Daily Assessment Due</span>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-amber-500/20 text-amber-300 border border-amber-500/40">
                Action Required
              </span>
            </div>

            <div>
              <p className="text-sm font-semibold text-slate-100">
                {!scheduleStatus?.has_assessment
                  ? "Welcome! Complete your initial daily assessment."
                  : "Your daily stress & duty assessment is now due."}
              </p>
              <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                {!scheduleStatus?.has_assessment
                  ? "Please submit your baseline operational duty, rest, and wellbeing indicators."
                  : "More than 24 hours have elapsed since your last recorded assessment. Log today's telemetry."}
              </p>
            </div>

            <div className="pt-1">
              <Link
                href="/assessment"
                className="inline-flex items-center space-x-2 px-4 py-2.5 bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-400 hover:to-emerald-400 text-slate-950 font-bold text-xs rounded-xl shadow-md transition-all active:scale-95"
              >
                <ClipboardList className="w-4 h-4" />
                <span>{!scheduleStatus?.has_assessment ? "Start Initial Assessment" : "Complete Today's Assessment"}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </Card>
        ) : (
          /* Assessment is Completed (< 24 hours) */
          <Card className="p-4 bg-slate-900/70 border-l-4 border-l-emerald-500 border-slate-800 rounded-xl space-y-2.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-emerald-400 font-mono text-xs font-semibold uppercase">
                <CheckCircle2 className="w-4 h-4" />
                <span>✓ Completed</span>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                Up to Date
              </span>
            </div>

            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400">Last Assessment:</span>
              <span className="font-mono text-slate-200 font-medium">
                {latestAssessment?.assessment_timestamp
                  ? new Date(latestAssessment.assessment_timestamp).toLocaleString(undefined, {
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })
                  : "Recorded today"}
              </span>
            </div>

            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400">Next Scheduled Assessment:</span>
              <span className="font-mono text-teal-400 font-medium">
                {scheduleStatus?.next_assessment_due_at
                  ? new Date(scheduleStatus.next_assessment_due_at).toLocaleTimeString(undefined, {
                      hour: "2-digit",
                      minute: "2-digit",
                    }) + " (24h schedule)"
                  : "Tomorrow"}
              </span>
            </div>

            <div className="pt-2 border-t border-slate-800 flex justify-between items-center">
              <span className="text-[11px] text-slate-400 italic">
                Telemetry synchronized with commander portal
              </span>
              <Link
                href="/assessment"
                className="text-[11px] text-teal-400 hover:text-teal-300 font-semibold flex items-center gap-1"
              >
                <span>Re-assess</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          </Card>
        )}
      </div>

      {/* 3. Single Authoritative Risk Score Card (Section 4 & 13) */}
      <div>
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
          Current AI Stress Risk Result
        </h3>
        {latestAssessment ? (
          <Card className="p-4 space-y-3 bg-[#1C2530] border-slate-700/80 shadow-md">
            <div className="flex justify-between items-start">
              <div>
                <span className="text-[10px] uppercase font-mono tracking-widest text-slate-400 block">
                  Stress Level
                </span>
                <span
                  className={`text-2xl font-black ${
                    latestAssessment.stress_level === "High"
                      ? "text-rose-400"
                      : latestAssessment.stress_level === "Medium"
                      ? "text-amber-400"
                      : "text-emerald-400"
                  }`}
                >
                  {latestAssessment.stress_level} Stress
                </span>
              </div>
              <div className="text-right">
                <span className="text-[10px] uppercase font-mono tracking-widest text-slate-400 block">
                  Continuous Risk Score
                </span>
                <span className="text-3xl font-black font-mono text-slate-100">
                  {typeof latestAssessment.risk_score === 'number'
                    ? latestAssessment.risk_score.toFixed(1)
                    : latestAssessment.risk_score}
                  <span className="text-xs text-slate-400 font-normal"> / 100</span>
                </span>
              </div>
            </div>


            <div className="flex items-center justify-between text-xs pt-2 border-t border-slate-700/60">
              <span className="text-slate-400">Operational Priority:</span>
              <span
                className={`font-mono font-bold uppercase px-2.5 py-0.5 rounded text-[11px] ${
                  latestAssessment.risk_priority === "Priority"
                    ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                    : latestAssessment.risk_priority === "Preventive"
                    ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                    : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                }`}
              >
                {latestAssessment.risk_priority}
              </span>
            </div>

            {/* TreeSHAP Contributing Factors */}
            {latestAssessment.key_factors && latestAssessment.key_factors.length > 0 && (
              <div className="pt-2 border-t border-slate-700/40 text-xs">
                <span className="text-[10px] uppercase font-mono text-slate-400 tracking-wider block mb-1">
                  Primary Associated Factors:
                </span>
                <div className="flex flex-wrap gap-1">
                  {latestAssessment.key_factors.slice(0, 3).map((factor, idx) => (
                    <span
                      key={idx}
                      className="bg-slate-900/60 text-slate-300 text-[11px] px-2 py-0.5 rounded border border-slate-800"
                    >
                      {factor}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 font-mono border-t border-slate-700/40">
              <span>
                Timestamp:{" "}
                {new Date(latestAssessment.assessment_timestamp).toLocaleDateString(undefined, {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                })}
              </span>
              <Link
                href="/trends"
                className="text-teal-400 hover:underline flex items-center gap-1 font-sans"
              >
                View History <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          </Card>
        ) : (
          <Card className="p-4 bg-[#1C2530] border-slate-700/80 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Activity className="w-6 h-6 text-teal-400 shrink-0" />
              <div>
                <p className="text-sm font-semibold text-slate-200">No Assessment Recorded</p>
                <p className="text-xs text-slate-400">Complete initial assessment to evaluate stress risk</p>
              </div>
            </div>
            <Link
              href="/assessment"
              className="px-3 py-1.5 bg-teal-500 text-slate-950 font-bold text-xs rounded-lg hover:bg-teal-400 transition-colors"
            >
              Assess Now
            </Link>
          </Card>
        )}
      </div>

      {/* 4. Jawan-Initiated Welfare Support Requests (Phase 23) */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <LifeBuoy className="w-3.5 h-3.5 text-teal-400" />
            <span>My Welfare Support ({welfareRequests.length})</span>
          </h3>
          <button
            onClick={() => setShowSupportSheet(true)}
            className="text-[11px] font-bold text-teal-400 hover:text-teal-300 flex items-center gap-1 bg-teal-500/10 hover:bg-teal-500/20 px-2.5 py-1 rounded-lg border border-teal-500/30 transition active:scale-95"
          >
            <Plus className="w-3 h-3" />
            <span>Request Support</span>
          </button>
        </div>

        {welfareRequests.length === 0 ? (
          <Card className="p-4 bg-[#1C2530] border-slate-700/80 space-y-2">
            <div className="flex items-center space-x-2 text-teal-400 text-xs font-semibold">
              <HeartPulse className="w-4 h-4" />
              <span>Need Welfare Support?</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              If you would like your welfare officer to review your duty pacing, leave schedule, or personal situation, you can submit a voluntary support request.
            </p>
            <div className="pt-1">
              <button
                onClick={() => setShowSupportSheet(true)}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-xs rounded-lg transition"
              >
                <span>Request Welfare Support</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </Card>
        ) : (
          <div className="space-y-2.5">
            {welfareRequests.map((req) => (
              <Card key={req.id} className="p-3.5 bg-slate-900/70 border-slate-800 space-y-2">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-mono text-[11px] uppercase font-bold text-teal-300">
                    {req.category}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                      req.status === "resolved"
                        ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                        : req.status === "in_progress"
                        ? "bg-purple-500/20 text-purple-300 border border-purple-500/40"
                        : req.status === "acknowledged"
                        ? "bg-blue-500/20 text-blue-300 border border-blue-500/40"
                        : "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                    }`}
                  >
                    {req.status === "in_progress" ? "In Progress" : req.status}
                  </span>
                </div>

                {req.message && (
                  <p className="text-xs text-slate-200 italic bg-slate-950/40 p-2 rounded border border-slate-800/60">
                    &ldquo;{req.message}&rdquo;
                  </p>
                )}

                <div className="flex justify-between items-center text-[10px] text-slate-400 pt-1 font-mono">
                  <span>
                    Submitted:{" "}
                    {new Date(req.created_at).toLocaleDateString(undefined, {
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                  <span className={req.urgency === "High" ? "text-rose-400 font-bold" : "text-slate-300"}>
                    Urgency: {req.urgency}
                  </span>
                </div>

                {/* Status-specific helpful banner for the Jawan */}
                {req.status === "resolved" && (
                  <div className="text-[11px] text-emerald-300 bg-emerald-500/10 p-2 rounded-lg border border-emerald-500/20 flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-emerald-400" />
                    <span>Your welfare request has been resolved.</span>
                  </div>
                )}
                {req.status === "acknowledged" && (
                  <div className="text-[11px] text-blue-300 bg-blue-500/10 p-2 rounded-lg border border-blue-500/20 flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 shrink-0 text-blue-400" />
                    <span>Welfare Officer has acknowledged your request.</span>
                  </div>
                )}
                {req.status === "in_progress" && (
                  <div className="text-[11px] text-purple-300 bg-purple-500/10 p-2 rounded-lg border border-purple-500/20 flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5 shrink-0 text-purple-400" />
                    <span>Review in progress by welfare counselor.</span>
                  </div>
                )}
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* 5. 7-Day Telemetry Trend Summary */}
      <TrendSummaryCard trend={trend} />

      {/* 6. AI Welfare Recommendations (Section 16) */}
      {latestAssessment?.recommendations && latestAssessment.recommendations.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <HeartPulse className="w-3.5 h-3.5 text-teal-400" />
              <span>AI Welfare Interventions ({latestAssessment.recommendations.length})</span>
            </h3>
            <span className="text-[10px] text-teal-400 font-mono">Automated Decision Support</span>
          </div>

          <div className="space-y-2">
            {latestAssessment.recommendations.map((rec) => (
              <Card key={rec.id} className="p-3 bg-slate-900/60 border-slate-800 space-y-1.5">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-mono text-[10px] uppercase font-bold text-teal-400">
                    {rec.recommendation_type}
                  </span>
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold uppercase ${
                      rec.status === "completed"
                        ? "bg-emerald-500/20 text-emerald-300"
                        : rec.status === "acknowledged"
                        ? "bg-blue-500/20 text-blue-300"
                        : "bg-amber-500/20 text-amber-300"
                    }`}
                  >
                    {rec.status}
                  </span>
                </div>
                <p className="text-xs text-slate-200 leading-relaxed">{rec.recommendation_text}</p>
                {rec.status !== "completed" && (
                  <div className="pt-1 flex justify-end">
                    <button
                      disabled={updatingRecId === rec.id}
                      onClick={() => handleCompleteRec(rec.id)}
                      className="text-[11px] font-semibold text-teal-400 hover:text-teal-300 disabled:opacity-50"
                    >
                      {updatingRecId === rec.id ? "Updating..." : "Mark Completed ✓"}
                    </button>
                  </div>
                )}
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* 7. Quick Action: Standardized Assessment */}
      <div>
        <Link href="/assessment" className="block">
          <Card className="flex items-center justify-between p-4 hover:bg-slate-800/60 transition-colors cursor-pointer border-l-4 border-l-transparent">
            <div className="flex items-center gap-3.5">
              <div className="w-10 h-10 bg-slate-800 rounded-xl flex items-center justify-center">
                <ClipboardList className="w-5 h-5 text-teal-400" />
              </div>
              <div>
                <p className="font-semibold text-sm text-slate-100">Daily Assessment</p>
                <p className="text-xs text-slate-400">Operational duty, rest & wellness evaluation</p>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-slate-400" />
          </Card>
        </Link>
      </div>

      {/* Welfare Support Request Modal / Sheet */}
      <WelfareSupportSheet
        isOpen={showSupportSheet}
        onClose={() => setShowSupportSheet(false)}
        onSuccess={handleWelfareSuccess}
      />
    </div>
  );
}
