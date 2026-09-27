"use client";

import React, { useState } from "react";
import { PersonalTrend } from "@/types/trends";
import { StressAssessmentOut, AssessmentScheduleStatus, WelfareRequestOut } from "@/types/api";
import { WelfareSupportSheet } from "./WelfareSupportSheet";
import { TrendChart } from "./TrendChart";
import Link from "next/link";
import { Activity, ArrowRight, CheckCircle2, ShieldCheck } from "lucide-react";

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

  return (
    <div className="flex flex-col gap-10 pb-32 px-5 max-w-[420px] mx-auto w-full">
      {/* 1. Header Area with Readability Scrim */}
      <div className="relative -mx-5 px-5 pt-8 pb-8 -mb-4">
        <div className="absolute inset-0 bg-gradient-to-b from-[#0a110e]/70 via-[#0a110e]/40 to-transparent pointer-events-none" />
        <div className="relative z-10 flex flex-col text-left">
          <h2 className="text-[28px] font-light text-white tracking-tight">
            {getGreeting()}, <span className="font-semibold text-white capitalize">{username || "Jawan"}</span>
          </h2>
          <p className="text-[13px] text-white/70 mt-1.5 font-medium tracking-wide">
            Your operational wellbeing overview
          </p>
        </div>
      </div>

      {/* 2. Primary Wellbeing Area */}
      <div className="flex flex-col relative">
        <div className="bg-[rgba(15,35,27,0.55)] backdrop-blur-[20px] border border-white/15 rounded-[32px] p-8 shadow-2xl flex flex-col items-center justify-center text-center">
          <span className="text-[11px] uppercase font-bold tracking-[0.2em] text-white/60 mb-3">Your Wellbeing</span>
          
          {latestAssessment ? (
            <div className="flex flex-col items-center w-full">
              <div className="text-[96px] font-light text-white tracking-tighter leading-[0.9] mb-4">
                {typeof latestAssessment.risk_score === 'number' ? latestAssessment.risk_score.toFixed(1) : latestAssessment.risk_score}
                <span className="text-[28px] font-light text-white/30 ml-1">/100</span>
              </div>
              
              <div className={`text-[20px] font-semibold tracking-wider uppercase px-5 py-2 rounded-full bg-black/20 ${
                latestAssessment.stress_level === "High" ? "text-mb-danger" : 
                latestAssessment.stress_level === "Medium" ? "text-mb-saffron" : "text-mb-green"
              }`}>
                {latestAssessment.stress_level} Risk
              </div>
              
              <div className={`text-[13px] font-bold uppercase tracking-[0.15em] mt-5 ${
                latestAssessment.risk_priority === "Priority" ? "text-mb-danger" : 
                latestAssessment.risk_priority === "Preventive" ? "text-mb-saffron" : "text-mb-green"
              }`}>
                ● {latestAssessment.risk_priority}
              </div>
              
              {/* Minimalist Linear Risk Indicator */}
              <div className="flex items-center gap-4 mt-8 w-full max-w-[240px]">
                <span className="text-[10px] font-bold text-white/40 uppercase tracking-widest">Low</span>
                <div className="flex-1 h-[2px] bg-white/10 rounded-full relative flex items-center">
                   <div 
                     className={`absolute h-3.5 w-3.5 rounded-full transform -translate-x-1/2 shadow-lg transition-all duration-1000 ${
                        latestAssessment.stress_level === "High" ? "bg-mb-danger left-[85%] shadow-mb-danger/50" : 
                        latestAssessment.stress_level === "Medium" ? "bg-mb-saffron left-[55%] shadow-mb-saffron/50" : "bg-mb-green left-[25%] shadow-mb-green/50"
                     }`}
                   />
                </div>
                <span className="text-[10px] font-bold text-white/40 uppercase tracking-widest">High</span>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-4 py-8">
              <Activity className="w-12 h-12 text-white/30" />
              <p className="text-[26px] font-light text-white">No Data</p>
              <p className="text-[13px] text-white/60 max-w-[220px] leading-relaxed">Complete an assessment to establish your baseline.</p>
            </div>
          )}
        </div>
      </div>

      {/* 3. Quick Metrics */}
      <div className="grid grid-cols-3 gap-3">
        <div className="p-4 bg-[rgba(15,35,27,0.35)] backdrop-blur-[16px] rounded-[24px] border border-white/10 flex flex-col items-center text-center gap-1 shadow-lg">
          <span className="text-[10px] font-bold text-white/50 uppercase tracking-[0.15em] mb-1.5">Duty Load</span>
          <span className="text-2xl font-light text-white leading-none">48</span>
          <span className="text-[10px] text-white/40 font-medium tracking-wide mt-1">HRS/WK</span>
        </div>
        <div className="p-4 bg-[rgba(15,35,27,0.35)] backdrop-blur-[16px] rounded-[24px] border border-white/10 flex flex-col items-center text-center gap-1 shadow-lg">
          <span className="text-[10px] font-bold text-white/50 uppercase tracking-[0.15em] mb-1.5">Recovery</span>
          <span className="text-2xl font-light text-white leading-none">7.2</span>
          <span className="text-[10px] text-white/40 font-medium tracking-wide mt-1">HRS</span>
        </div>
        <div className="p-4 bg-[rgba(15,35,27,0.35)] backdrop-blur-[16px] rounded-[24px] border border-white/10 flex flex-col items-center text-center gap-1 shadow-lg">
           <span className="text-[10px] font-bold text-white/50 uppercase tracking-[0.15em] mb-1.5">Logs</span>
           <span className="text-2xl font-light text-white leading-none">{trend.last7Days?.length || 0}</span>
           <span className="text-[10px] text-white/40 font-medium tracking-wide mt-1">PAST 7D</span>
        </div>
      </div>

      {/* 4. Stress Trend */}
      <div className="flex flex-col">
         <span className="text-[11px] uppercase font-bold tracking-[0.15em] text-white/80 mb-4 ml-2">Stress Over Time</span>
         {trend.last7Days && trend.last7Days.length > 0 ? (
           <div className="w-full h-[240px] bg-[rgba(15,35,27,0.35)] backdrop-blur-[16px] border border-white/10 rounded-[32px] p-5 shadow-lg">
             <TrendChart data={trend.last7Days} />
           </div>
         ) : (
           <div className="w-full h-[240px] bg-[rgba(15,35,27,0.35)] backdrop-blur-[16px] border border-white/10 rounded-[32px] flex items-center justify-center text-[13px] font-medium text-white/50 shadow-lg">
             Not enough data
           </div>
         )}
      </div>

      {/* 5. Latest Assessment Summary */}
      <div className="flex flex-col">
        <span className="text-[11px] uppercase font-bold tracking-[0.15em] text-white/80 mb-4 ml-2">Latest Assessment</span>
        <div className="flex flex-col bg-[rgba(15,35,27,0.45)] backdrop-blur-[16px] border border-white/15 rounded-[32px] p-6 gap-5 shadow-lg">
           <div className="flex justify-between items-center text-[14px] border-b border-white/10 pb-5">
             <span className="text-white/60 font-medium">Last assessment</span>
             <span className="text-white font-semibold">
               {latestAssessment ? new Date(latestAssessment.assessment_timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : "None"}
             </span>
           </div>
           <div className="flex justify-between items-center text-[14px] border-b border-white/10 pb-5">
             <span className="text-white/60 font-medium">Next assessment</span>
             <span className="text-white font-semibold">
                {scheduleStatus?.hours_since_last_assessment != null ? `${Math.max(0, 24 - scheduleStatus.hours_since_last_assessment)}h remaining` : "Now"}
             </span>
           </div>
           <div className="flex justify-between items-center text-[14px]">
             <span className="text-white/60 font-medium">Status</span>
             {isAssessmentDue ? (
               <span className="text-mb-saffron font-bold">Due</span>
             ) : (
               <span className="text-mb-green font-bold flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4" /> Up to date</span>
             )}
           </div>
        </div>
      </div>

      {/* 6. Active Welfare Requests */}
      {welfareRequests.length > 0 && (
        <div className="flex flex-col mt-2">
          <span className="text-[11px] uppercase font-bold tracking-[0.15em] text-white/80 mb-4 ml-2">Active Welfare Requests</span>
          <div className="bg-[rgba(15,35,27,0.45)] backdrop-blur-[16px] border border-white/15 rounded-[32px] overflow-hidden shadow-lg">
            {welfareRequests.map((req, idx) => (
              <div key={req.id} className={`flex justify-between items-center text-[14px] p-5 ${idx !== welfareRequests.length - 1 ? 'border-b border-white/10' : ''}`}>
                <span className="text-white/90 font-medium line-clamp-1 flex-1 pr-4 leading-relaxed">{req.message || "Welfare request"}</span>
                <span className={`px-3 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-wider shrink-0 ${
                    req.status === "resolved" ? "bg-mb-green/20 text-mb-green border border-mb-green/30"
                      : req.status === "in_progress" ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                      : req.status === "acknowledged" ? "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                      : "bg-mb-saffron/20 text-mb-saffron border border-mb-saffron/30"
                  }`}>
                  {req.status.replace('_', ' ')}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 7. Primary Action & Welfare */}
      <div className="flex flex-col gap-4 mt-6">
         <Link 
           href="/assessment" 
           className={`w-full py-4 rounded-[28px] flex justify-center items-center gap-2 text-[15px] font-bold transition-transform active:scale-[0.98] ${
             isAssessmentDue 
               ? "bg-[#00a896] text-white shadow-[0_8px_20px_rgba(0,168,150,0.3)]" 
               : "bg-[rgba(255,255,255,0.12)] backdrop-blur-md border border-white/20 text-white hover:bg-white/20"
           }`}
         >
           {isAssessmentDue ? "Start Assessment" : "View Assessment"} <ArrowRight className="w-5 h-5" />
         </Link>
         
         <button 
           onClick={() => setShowSupportSheet(true)} 
           className="w-full py-4 text-[12px] font-bold text-white/50 hover:text-white transition-colors uppercase tracking-widest mt-2"
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
