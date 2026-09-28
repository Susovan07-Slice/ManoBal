"use client";

import React, { useState, useEffect } from "react";
import { PersonalTrend } from "@/types/trends";
import { StressAssessmentOut, AssessmentScheduleStatus, WelfareRequestOut } from "@/types/api";
import { WelfareSupportSheet } from "./WelfareSupportSheet";
import { TrendChart } from "./TrendChart";
import Link from "next/link";
import { Activity, ArrowRight, CheckCircle2, Briefcase, Moon, FileText, Clock } from "lucide-react";
import { formatAssessmentDateTime, formatAssessmentCountdown } from "@/lib/utils";

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
  const [showSupportSheet, setShowSupportSheet] = useState(false);
  const [currentTime, setCurrentTime] = useState<number>(() => Date.now());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(Date.now());
    }, 15000); // 15-second tick for responsive countdown
    return () => clearInterval(timer);
  }, []);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 17) return "Good afternoon";
    return "Good evening";
  };

  const isAssessmentDue = scheduleStatus ? scheduleStatus.assessment_due : !latestAssessment;

  // Calculate ring gauge percentage (inverted: lower score = more filled in green)
  const riskScore = latestAssessment?.risk_score ?? 0;
  const ringPercentage = typeof riskScore === 'number' ? Math.min(100, Math.max(0, riskScore)) : 0;
  const circumference = 2 * Math.PI * 54; // radius = 54
  const strokeDashoffset = circumference - (ringPercentage / 100) * circumference;

  const getRingColor = () => {
    if (!latestAssessment) return "#9ca3af";
    if (latestAssessment.stress_level === "High") return "#ef4444";
    if (latestAssessment.stress_level === "Medium") return "#f59e0b";
    return "#10b981";
  };

  return (
    <div className="flex flex-col gap-6 pb-32 px-4 max-w-[420px] mx-auto w-full">
      {/* 1. Greeting — floats over wallpaper with text-shadow */}
      <div className="pt-6 pb-2">
        <h2
          className="text-[26px] font-light text-white tracking-tight"
          style={{ textShadow: "0 2px 12px rgba(0,0,0,0.4)" }}
        >
          {getGreeting()},{" "}
          <span className="font-semibold capitalize">{username || "Jawan"}</span>
        </h2>
        <p
          className="text-[13px] text-white/80 mt-1 font-medium tracking-wide"
          style={{ textShadow: "0 1px 8px rgba(0,0,0,0.3)" }}
        >
          Your operational wellbeing overview
        </p>
      </div>

      {/* 2. Hero Wellbeing Card — White Frosted Glass */}
      <div className="flex flex-col relative">
        <div className="bg-white/88 backdrop-blur-2xl border border-white/60 rounded-3xl p-7 shadow-[0_8px_40px_rgba(0,0,0,0.08)] flex flex-col items-center justify-center text-center">
          <span className="text-[10px] uppercase font-bold tracking-[0.2em] text-gray-400 mb-4">
            Your Wellbeing
          </span>

          {latestAssessment ? (
            <div className="flex flex-col items-center w-full">
              {/* Circular Ring Gauge */}
              <div className="relative w-[140px] h-[140px] mb-5">
                <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
                  {/* Background ring */}
                  <circle
                    cx="60" cy="60" r="54"
                    fill="none"
                    stroke="#f3f4f6"
                    strokeWidth="8"
                  />
                  {/* Colored progress ring */}
                  <circle
                    cx="60" cy="60" r="54"
                    fill="none"
                    stroke={getRingColor()}
                    strokeWidth="8"
                    strokeLinecap="round"
                    strokeDasharray={circumference}
                    strokeDashoffset={strokeDashoffset}
                    className="transition-all duration-1000 ease-out"
                    style={{ filter: `drop-shadow(0 0 6px ${getRingColor()}40)` }}
                  />
                </svg>
                {/* Center score */}
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-[36px] font-light text-gray-900 leading-none tracking-tight">
                    {typeof riskScore === "number" ? riskScore.toFixed(1) : riskScore}
                  </span>
                  <span className="text-[11px] text-gray-400 font-medium mt-0.5">/100</span>
                </div>
              </div>

              {/* Risk Badge + Priority */}
              <div className="flex items-center gap-2.5">
                <span
                  className={`text-[12px] font-bold uppercase tracking-wider px-4 py-1.5 rounded-full ${
                    latestAssessment.stress_level === "High"
                      ? "bg-red-100 text-red-600"
                      : latestAssessment.stress_level === "Medium"
                      ? "bg-amber-100 text-amber-600"
                      : "bg-emerald-100 text-emerald-600"
                  }`}
                >
                  {latestAssessment.stress_level} Risk
                </span>
                <span
                  className={`text-[11px] font-bold uppercase tracking-wider px-3 py-1.5 rounded-full border ${
                    latestAssessment.risk_priority === "Priority"
                      ? "bg-red-50 text-red-500 border-red-200"
                      : latestAssessment.risk_priority === "Preventive"
                      ? "bg-amber-50 text-amber-500 border-amber-200"
                      : "bg-gray-50 text-gray-500 border-gray-200"
                  }`}
                >
                  {latestAssessment.risk_priority}
                </span>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3 py-6">
              <Activity className="w-12 h-12 text-gray-300" />
              <p className="text-[22px] font-light text-gray-700">No Data</p>
              <p className="text-[13px] text-gray-400 max-w-[220px] leading-relaxed">
                Complete an assessment to establish your baseline.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* 3. Quick Metrics — White Cards with Colored Top Borders */}
      <div className="grid grid-cols-3 gap-2.5">
        <div className="p-4 bg-white/85 backdrop-blur-xl rounded-2xl border border-white/60 border-t-[3px] border-t-blue-500 shadow-[0_4px_20px_rgba(0,0,0,0.06)] flex flex-col items-center text-center gap-1">
          <Briefcase className="w-4 h-4 text-blue-500 mb-1" />
          <span className="text-[9px] font-bold text-gray-400 uppercase tracking-[0.12em]">
            Duty Load
          </span>
          <span className="text-2xl font-light text-gray-900 leading-none">48</span>
          <span className="text-[9px] text-gray-400 font-medium tracking-wide">HRS/WK</span>
        </div>
        <div className="p-4 bg-white/85 backdrop-blur-xl rounded-2xl border border-white/60 border-t-[3px] border-t-emerald-500 shadow-[0_4px_20px_rgba(0,0,0,0.06)] flex flex-col items-center text-center gap-1">
          <Moon className="w-4 h-4 text-emerald-500 mb-1" />
          <span className="text-[9px] font-bold text-gray-400 uppercase tracking-[0.12em]">
            Recovery
          </span>
          <span className="text-2xl font-light text-gray-900 leading-none">7.2</span>
          <span className="text-[9px] text-gray-400 font-medium tracking-wide">HRS</span>
        </div>
        <div className="p-4 bg-white/85 backdrop-blur-xl rounded-2xl border border-white/60 border-t-[3px] border-t-amber-500 shadow-[0_4px_20px_rgba(0,0,0,0.06)] flex flex-col items-center text-center gap-1">
          <FileText className="w-4 h-4 text-amber-500 mb-1" />
          <span className="text-[9px] font-bold text-gray-400 uppercase tracking-[0.12em]">
            Logs
          </span>
          <span className="text-2xl font-light text-gray-900 leading-none">
            {trend.last7Days?.length || 0}
          </span>
          <span className="text-[9px] text-gray-400 font-medium tracking-wide">PAST 7D</span>
        </div>
      </div>

      {/* 4. Stress Trend Chart — White Card */}
      <div className="flex flex-col">
        <span className="text-[11px] uppercase font-bold tracking-[0.15em] text-white/90 mb-3 ml-1" style={{ textShadow: "0 1px 6px rgba(0,0,0,0.3)" }}>
          Stress Over Time
        </span>
        {trend.last7Days && trend.last7Days.length > 0 ? (
          <div className="w-full h-[220px] bg-white/85 backdrop-blur-xl border border-white/60 rounded-2xl p-5 shadow-[0_4px_20px_rgba(0,0,0,0.06)]">
            <TrendChart data={trend.last7Days} />
          </div>
        ) : (
          <div className="w-full h-[220px] bg-white/85 backdrop-blur-xl border border-white/60 rounded-2xl flex items-center justify-center text-[13px] font-medium text-gray-400 shadow-[0_4px_20px_rgba(0,0,0,0.06)]">
            Not enough data
          </div>
        )}
      </div>

      {/* 5. Latest Assessment Summary — Clean White Card */}
      <div className="flex flex-col">
        <span className="text-[11px] uppercase font-bold tracking-[0.15em] text-white/90 mb-3 ml-1" style={{ textShadow: "0 1px 6px rgba(0,0,0,0.3)" }}>
          Latest Assessment
        </span>
        <div className="flex flex-col bg-white/85 backdrop-blur-xl border border-white/60 rounded-2xl p-5 gap-4 shadow-[0_4px_20px_rgba(0,0,0,0.06)]">
          <div className="flex justify-between items-center text-[13px] border-b border-gray-200 pb-4">
            <span className="text-gray-500 font-medium">Last assessment</span>
            <span className="text-gray-800 font-semibold">
              {latestAssessment
                ? formatAssessmentDateTime(latestAssessment.assessment_timestamp)
                : "None"}
            </span>
          </div>
          <div className="flex justify-between items-center text-[13px] border-b border-gray-200 pb-4">
            <span className="text-gray-500 font-medium">Next assessment</span>
            <span className={`font-semibold ${isAssessmentDue ? "text-amber-600 font-bold" : "text-gray-800"}`}>
              {formatAssessmentCountdown(scheduleStatus, currentTime)}
            </span>
          </div>
          <div className="flex justify-between items-center text-[13px]">
            <span className="text-gray-500 font-medium">Status</span>
            {isAssessmentDue ? (
              <span className="text-amber-600 font-bold text-[12px] bg-amber-50 px-3 py-1 rounded-full">Due</span>
            ) : (
              <span className="text-emerald-600 font-bold flex items-center gap-1.5 text-[12px] bg-emerald-50 px-3 py-1 rounded-full">
                <CheckCircle2 className="w-3.5 h-3.5" /> Up to date
              </span>
            )}
          </div>
        </div>
      </div>

      {/* 6. Active Welfare Requests */}
      {welfareRequests.length > 0 && (
        <div className="flex flex-col">
          <span className="text-[11px] uppercase font-bold tracking-[0.15em] text-white/90 mb-3 ml-1" style={{ textShadow: "0 1px 6px rgba(0,0,0,0.3)" }}>
            Active Welfare Requests
          </span>
          <div className="bg-white/85 backdrop-blur-xl border border-white/60 rounded-2xl overflow-hidden shadow-[0_4px_20px_rgba(0,0,0,0.06)]">
            {welfareRequests.map((req, idx) => (
              <div
                key={req.id}
                className={`flex justify-between items-center text-[13px] p-4 ${
                  idx !== welfareRequests.length - 1 ? "border-b border-gray-200" : ""
                }`}
              >
                <span className="text-gray-700 font-medium line-clamp-1 flex-1 pr-4 leading-relaxed">
                  {req.message || "Welfare request"}
                </span>
                <span
                  className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider shrink-0 ${
                    req.status === "resolved"
                      ? "bg-emerald-100 text-emerald-600"
                      : req.status === "in_progress"
                      ? "bg-purple-100 text-purple-600"
                      : req.status === "acknowledged"
                      ? "bg-blue-100 text-blue-600"
                      : "bg-amber-100 text-amber-600"
                  }`}
                >
                  {req.status.replace("_", " ")}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 7. Primary Action & Welfare */}
      <div className="flex flex-col gap-3 mt-2">
        <Link
          href="/assessment"
          className={`w-full py-3.5 rounded-2xl flex justify-center items-center gap-2 text-[14px] font-bold transition-transform active:scale-[0.98] shadow-lg ${
            isAssessmentDue
              ? "bg-gradient-to-r from-mb-accent to-emerald-500 text-white shadow-emerald-500/25"
              : "bg-white/70 backdrop-blur-md border border-white/60 text-gray-700 hover:bg-white/90 shadow-[0_4px_20px_rgba(0,0,0,0.06)]"
          }`}
        >
          {isAssessmentDue ? "Start Assessment" : "View Assessment"}{" "}
          <ArrowRight className="w-4 h-4" />
        </Link>

        <button
          onClick={() => setShowSupportSheet(true)}
          className="w-full py-3 text-[11px] font-bold text-white/50 hover:text-white/80 transition-colors uppercase tracking-widest"
          style={{ textShadow: "0 1px 4px rgba(0,0,0,0.2)" }}
        >
          Request Welfare Support
        </button>
      </div>

      <WelfareSupportSheet
        isOpen={showSupportSheet}
        onClose={() => setShowSupportSheet(false)}
        onSuccess={() => onRefresh && onRefresh()}
      />
    </div>
  );
}
