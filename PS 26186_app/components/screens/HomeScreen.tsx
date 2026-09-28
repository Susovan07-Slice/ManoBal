"use client";

import React, { useState } from "react";
import { PersonalTrend } from "@/types/trends";
import { StressAssessmentOut, AssessmentScheduleStatus, WelfareRequestOut } from "@/types/api";
import { WelfareSupportSheet } from "./WelfareSupportSheet";
import { TrendChart } from "./TrendChart";
import Link from "next/link";
import { Activity, ArrowRight, CheckCircle2, Briefcase, Moon, FileText } from "lucide-react";

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

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 17) return "Good afternoon";
    return "Good evening";
  };

  const isAssessmentDue = scheduleStatus ? scheduleStatus.assessment_due : !latestAssessment;

  const riskScore = latestAssessment?.risk_score ?? 0;

  return (
    <div className="flex flex-col gap-5 pb-44 px-4 max-w-md mx-auto w-full min-w-0">
      {/* 1. Greeting */}
      <div className="pt-6 pb-2">
        <h2 className="text-[26px] font-light text-ink tracking-tight">
          {getGreeting()},{" "}
          <span className="font-semibold capitalize">{username || "Jawan"}</span>
        </h2>
        <p className="text-[13px] text-ink-2 mt-1 font-medium">
          Your operational wellbeing overview
        </p>
      </div>

      {/* 2. Hero Wellbeing Card */}
      <div className="flex flex-col relative">
        <div className="glass-card p-7 flex flex-col items-center justify-center text-center animate-fade-up">
          <span className="eyebrow mb-2">
            Stress Level
          </span>

          {latestAssessment ? (
            <div className="flex flex-col items-center w-full">
              {/* Emoji Stress Scale */}
              <div className="flex flex-col w-full px-2 mt-2 mb-4">
                <div className="flex justify-between items-center relative h-14">
                  {/* Background connecting track */}
                  <div className="absolute left-[7%] right-[7%] top-1/2 h-1.5 bg-sky-100 -translate-y-1/2 rounded-full z-0" />
                  
                  {(() => {
                    const score = typeof riskScore === "number" ? riskScore : 0;
                    // 0-100 mapped to 0-6 index
                    let activeIdx = 0;
                    if (score > 14) activeIdx = 1;
                    if (score > 28) activeIdx = 2;
                    if (score > 42) activeIdx = 3;
                    if (score > 57) activeIdx = 4;
                    if (score > 71) activeIdx = 5;
                    if (score > 85) activeIdx = 6;
                    
                    const emojis = [
                      { face: '😌', label: 'Very Calm' },
                      { face: '🙂', label: 'Calm' },
                      { face: '😐', label: 'Slightly' },
                      { face: '😕', label: 'Moderate' },
                      { face: '😟', label: 'Stressed' },
                      { face: '😰', label: 'Highly' },
                      { face: '😫', label: 'Extreme' }
                    ];

                    return emojis.map((item, idx) => {
                      const isActive = idx === activeIdx;
                      return (
                        <div key={idx} className="relative flex flex-col items-center z-10">
                          <div 
                            className={`flex items-center justify-center transition-all duration-300 ${
                              isActive 
                                ? 'w-11 h-11 bg-white shadow-[0_4px_12px_rgba(31,110,140,0.2)] border-2 border-brand-500 rounded-full scale-110 z-20' 
                                : 'w-8 h-8 bg-white/80 border border-white rounded-full scale-100 opacity-60'
                            }`}
                          >
                            <span className={`text-[22px] leading-none ${isActive ? '' : 'grayscale-[40%]'}`}>
                              {item.face}
                            </span>
                          </div>
                          {isActive && (
                            <span className="absolute -bottom-5 text-[10px] font-bold text-brand-600 whitespace-nowrap animate-fade-up">
                              {item.label}
                            </span>
                          )}
                        </div>
                      );
                    });
                  })()}
                </div>
              </div>

              {/* Risk Badge + Priority */}
              <div className="flex items-center gap-2.5">
                <span
                  className={`text-[12px] font-bold uppercase tracking-wider px-4 py-1.5 rounded-full ${
                    latestAssessment.stress_level === "High"
                      ? "bg-alert-bg text-alert"
                      : latestAssessment.stress_level === "Medium"
                      ? "bg-warn-bg text-warn"
                      : "bg-ok-bg text-ok"
                  }`}
                >
                  {latestAssessment.stress_level} Risk
                </span>
                <span
                  className={`text-[12px] font-bold uppercase tracking-wider px-4 py-1.5 rounded-full border ${
                    latestAssessment.risk_priority === "Priority"
                      ? "bg-alert-bg text-alert border-alert/20"
                      : latestAssessment.risk_priority === "Preventive"
                      ? "bg-warn-bg text-warn border-warn/20"
                      : "bg-brand-100 text-brand-600 border-brand-500/20"
                  }`}
                >
                  {latestAssessment.risk_priority}
                </span>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3 py-6">
              <Activity className="w-12 h-12 text-ink-3" />
              <p className="text-[22px] font-light text-ink">No Data</p>
              <p className="text-[13px] text-ink-3 max-w-[220px] leading-relaxed">
                Complete an assessment to establish your baseline.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* 3. Quick Metrics */}
      <div className="grid grid-cols-3 gap-2.5 animate-fade-up stagger-1">
        <div className="p-4 bg-white rounded-[20px] shadow-[0_10px_30px_rgba(31,110,140,0.08)] flex flex-col items-center text-center gap-1">
          <div className="w-9 h-9 rounded-full flex items-center justify-center mb-1 bg-brand-100">
            <Briefcase className="w-4 h-4 text-brand-500" />
          </div>
          <span className="text-[10px] font-semibold text-ink-3 uppercase tracking-wide">
            Duty Load
          </span>
          <span className="text-2xl font-semibold text-ink leading-none tabular-nums">48</span>
          <span className="text-[10px] text-ink-3 font-medium">HRS/WK</span>
        </div>
        <div className="p-4 bg-white rounded-[20px] shadow-[0_10px_30px_rgba(31,110,140,0.08)] flex flex-col items-center text-center gap-1">
          <div className="w-9 h-9 rounded-full flex items-center justify-center mb-1 bg-ok-bg">
            <Moon className="w-4 h-4 text-ok" />
          </div>
          <span className="text-[10px] font-semibold text-ink-3 uppercase tracking-wide">
            Recovery
          </span>
          <span className="text-2xl font-semibold text-ink leading-none tabular-nums">7.2</span>
          <span className="text-[10px] text-ink-3 font-medium">HRS</span>
        </div>
        <div className="p-4 bg-white rounded-[20px] shadow-[0_10px_30px_rgba(31,110,140,0.08)] flex flex-col items-center text-center gap-1">
          <div className="w-9 h-9 rounded-full flex items-center justify-center mb-1 bg-warn-bg">
            <FileText className="w-4 h-4 text-warn" />
          </div>
          <span className="text-[10px] font-semibold text-ink-3 uppercase tracking-wide">
            Logs
          </span>
          <span className="text-2xl font-semibold text-ink leading-none tabular-nums">
            {trend.last7Days?.length || 0}
          </span>
          <span className="text-[10px] text-ink-3 font-medium">PAST 7D</span>
        </div>
      </div>

      {/* 4. Stress Trend Chart */}
      <div className="flex flex-col">
        <span className="eyebrow mb-3 ml-1">
          Stress Over Time
        </span>
        {trend.last7Days && trend.last7Days.length > 0 ? (
          <div className="w-full h-[220px] glass-card p-5 animate-fade-up stagger-2">
            <TrendChart data={trend.last7Days} />
          </div>
        ) : (
          <div className="w-full h-[220px] glass-card p-5 animate-fade-up stagger-2 flex items-center justify-center text-[13px] font-medium text-ink-3">
            Not enough data
          </div>
        )}
      </div>

      {/* 5. Latest Assessment Summary */}
      <div className="flex flex-col">
        <span className="eyebrow mb-3 ml-1">
          Latest Assessment
        </span>
        <div className="flex flex-col glass-card p-5 gap-4 animate-fade-up stagger-3">
          <div className="flex justify-between items-center text-[13px] border-b border-sky-200/50 pb-4">
            <span className="text-ink-3 font-medium">Last assessment</span>
            <span className="text-ink font-semibold">
              {latestAssessment
                ? new Date(latestAssessment.assessment_timestamp).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })
                : "None"}
            </span>
          </div>
          <div className="flex justify-between items-center text-[13px] border-b border-sky-200/50 pb-4">
            <span className="text-ink-3 font-medium">Next assessment</span>
            <span className="text-ink font-semibold">
              {scheduleStatus?.hours_since_last_assessment != null
                ? `${Math.max(0, 24 - scheduleStatus.hours_since_last_assessment)}h remaining`
                : "Now"}
            </span>
          </div>
          <div className="flex justify-between items-center text-[13px]">
            <span className="text-ink-3 font-medium">Status</span>
            {isAssessmentDue ? (
              <span className="text-warn font-bold bg-warn-bg px-3 py-1 rounded-full">Due</span>
            ) : (
              <span className="text-ok font-bold bg-ok-bg px-3 py-1 rounded-full flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5" /> Up to date
              </span>
            )}
          </div>
        </div>
      </div>

      {/* 6. Active Welfare Requests */}
      {welfareRequests.length > 0 && (
        <div className="flex flex-col">
          <span className="eyebrow mb-3 ml-1">
            Active Welfare Requests
          </span>
          <div className="glass-card overflow-hidden animate-fade-up stagger-4">
            {welfareRequests.map((req, idx) => (
              <div
                key={req.id}
                className={`flex justify-between items-center text-[13px] p-4 ${
                  idx !== welfareRequests.length - 1 ? "border-b border-sky-200/50" : ""
                }`}
              >
                <span className="text-ink font-medium line-clamp-1 flex-1 pr-4 leading-relaxed">
                  {req.message || "Welfare request"}
                </span>
                <span
                  className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider shrink-0 ${
                    req.status === "resolved"
                      ? "bg-ok-bg text-ok"
                      : req.status === "in_progress"
                      ? "bg-brand-100 text-brand-600"
                      : req.status === "acknowledged"
                      ? "bg-brand-100 text-brand-500"
                      : "bg-warn-bg text-warn"
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
          className={
            isAssessmentDue
              ? "w-full h-[52px] rounded-full flex justify-center items-center gap-2 text-[14px] font-bold bg-gradient-to-r from-brand-500 to-brand-600 text-white shadow-[0_16px_40px_rgba(31,110,140,0.22)] active:scale-[.97] transition-all"
              : "w-full h-[52px] rounded-full flex justify-center items-center gap-2 text-[14px] font-bold bg-white/70 backdrop-blur-md border border-sky-200 text-ink hover:bg-white shadow-[0_10px_30px_rgba(31,110,140,0.08)]"
          }
        >
          {isAssessmentDue ? "Start Assessment" : "View Assessment"}{" "}
          <ArrowRight className="w-4 h-4" />
        </Link>

        <button
          onClick={() => setShowSupportSheet(true)}
          className="w-full py-3 text-ink-3 hover:text-ink-2 font-semibold text-[12px] uppercase tracking-widest transition-colors"
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
