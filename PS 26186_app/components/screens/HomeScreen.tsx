"use client";

import React, { useState } from "react";
import { PersonalTrend } from "@/types/trends";
import { StressAssessmentOut, AssessmentScheduleStatus, WelfareRequestOut } from "@/types/api";
import { WelfareSupportSheet } from "./WelfareSupportSheet";
import { TrendChart } from "./TrendChart";
import Link from "next/link";
import { Activity, ArrowRight, CheckCircle2, ShieldCheck } from "lucide-react";
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
  const [showSupportSheet, setShowSupportSheet] = useState(false);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 17) return "Good afternoon";
    return "Good evening";
  };

  const isAssessmentDue = scheduleStatus ? scheduleStatus.assessment_due : !latestAssessment;

  return (
    <div className="flex flex-col gap-14 animate-in fade-in duration-700 pb-32 pt-10 px-5 max-w-md mx-auto">
      {/* 1. Header Area */}
      <div className="flex flex-col text-left">
        <h2 className="text-2xl font-light text-mb-text-primary tracking-tight">
          {getGreeting()}, <span className="font-medium capitalize text-mb-text-primary">{username || "Jawan"}</span>
        </h2>
        <p className="text-xs text-mb-text-secondary mt-2 font-medium tracking-wide">
          Your operational wellbeing overview
        </p>
      </div>

      {/* 2. Primary Wellbeing Area */}
      <div className="flex flex-col">
        <span className="text-[10px] uppercase font-bold tracking-widest text-mb-text-muted mb-6">Your Wellbeing</span>
        {latestAssessment ? (
          <div className="flex flex-col gap-3">
            <div className="text-[80px] font-light text-mb-text-primary tracking-tighter leading-none mb-1">
              {typeof latestAssessment.risk_score === 'number' ? latestAssessment.risk_score.toFixed(1) : latestAssessment.risk_score}
            </div>
            <div className={`text-xl font-medium tracking-wide uppercase ${
              latestAssessment.stress_level === "High" ? "text-mb-saffron" : 
              latestAssessment.stress_level === "Medium" ? "text-mb-saffron" : "text-mb-green"
            }`}>
              {latestAssessment.stress_level} Risk
            </div>
            <div className={`text-xs font-bold uppercase tracking-widest ${
              latestAssessment.risk_priority === "Priority" ? "text-mb-saffron" : 
              latestAssessment.risk_priority === "Preventive" ? "text-mb-saffron" : "text-mb-green"
            }`}>
              â— {latestAssessment.risk_priority}
            </div>
            
            {/* Minimalist Linear Risk Indicator */}
            <div className="flex items-center gap-4 mt-6">
              <span className="text-[9px] font-bold text-mb-text-muted uppercase tracking-widest">Low</span>
              <div className="flex-1 h-[1px] bg-slate-600/50 relative flex items-center">
                 <div 
                   className={`absolute h-2 w-2 rounded-full transform -translate-x-1/2 ${
                      latestAssessment.stress_level === "High" ? "bg-mb-saffron left-[85%] shadow-[0_0_10px_var(--color-saffron)]" : 
                      latestAssessment.stress_level === "Medium" ? "bg-mb-saffron left-[55%] shadow-[0_0_10px_#fbbf24]" : "bg-mb-green left-[25%] shadow-[0_0_10px_#34d399]"
                   }`}
                 />
              </div>
              <span className="text-[9px] font-bold text-mb-text-muted uppercase tracking-widest">High</span>
            </div>
            <span className="text-[10px] text-mb-text-muted font-medium italic mt-3 block">Based on your latest assessment</span>
          </div>
        ) : (
          <div className="flex flex-col gap-2 py-4">
            <Activity className="w-8 h-8 text-mb-accent opacity-80" />
            <p className="text-xl font-light text-mb-text-primary mt-2">No Data</p>
            <p className="text-xs text-mb-text-secondary">Complete an assessment to establish your baseline.</p>
          </div>
        )}
      </div>

      {/* 3. Quick Metrics */}
      <div className="grid grid-cols-3 gap-3">
        <div className="p-4 bg-mb-glass-strong backdrop-blur-xl rounded-[20px] border border-mb-glass-border flex flex-col items-start gap-1">
          <span className="text-[9px] font-bold text-mb-text-muted uppercase tracking-widest mb-1">Duty Load</span>
          <span className="text-lg font-light text-mb-text-primary">48 <span className="text-[10px] text-mb-text-muted font-medium">hrs/wk</span></span>
        </div>
        <div className="p-4 bg-mb-glass-strong backdrop-blur-xl rounded-[20px] border border-mb-glass-border flex flex-col items-start gap-1">
          <span className="text-[9px] font-bold text-mb-text-muted uppercase tracking-widest mb-1">Recovery</span>
          <span className="text-lg font-light text-mb-text-primary">7.2 <span className="text-[10px] text-mb-text-muted font-medium">hrs</span></span>
        </div>
        <div className="p-4 bg-mb-glass-strong backdrop-blur-xl rounded-[20px] border border-mb-glass-border flex flex-col items-start gap-1">
           <span className="text-[9px] font-bold text-mb-text-muted uppercase tracking-widest mb-1">Logs</span>
           <span className="text-lg font-light text-mb-text-primary">{trend.last7Days?.length || 0} <span className="text-[10px] text-mb-text-muted font-medium">past 7d</span></span>
        </div>
      </div>

      {/* 4. Stress Trend */}
      <div className="flex flex-col">
         <span className="text-[10px] uppercase font-bold tracking-widest text-mb-text-muted mb-4">Stress Over Time</span>
         {trend.last7Days && trend.last7Days.length > 0 ? (
           <div className="-mx-1">
             <TrendChart data={trend.last7Days} />
           </div>
         ) : (
           <div className="w-full h-[280px] bg-mb-glass-strong backdrop-blur-xl border border-mb-glass-border rounded-3xl flex items-center justify-center text-xs text-mb-text-muted">
             Not enough data
           </div>
         )}
      </div>

      {/* 5. Latest Assessment Summary */}
      <div className="flex flex-col">
        <span className="text-[10px] uppercase font-bold tracking-widest text-mb-text-muted mb-4">Latest Assessment</span>
        <div className="flex flex-col gap-4">
           <div className="flex justify-between items-center text-xs border-b border-mb-glass-border pb-4">
             <span className="text-mb-text-secondary font-medium">Last assessment</span>
             <span className="text-mb-text-secondary font-medium">
               {latestAssessment ? new Date(latestAssessment.assessment_timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : "None"}
             </span>
           </div>
           <div className="flex justify-between items-center text-xs border-b border-mb-glass-border pb-4">
             <span className="text-mb-text-secondary font-medium">Next assessment</span>
             <span className="text-mb-text-secondary font-medium">
                {scheduleStatus?.hours_since_last_assessment != null ? `${Math.max(0, 24 - scheduleStatus.hours_since_last_assessment)}h remaining` : "Now"}
             </span>
           </div>
           <div className="flex justify-between items-center text-xs pb-2">
             <span className="text-mb-text-secondary font-medium">Status</span>
             {isAssessmentDue ? (
               <span className="text-mb-saffron font-bold">Due</span>
             ) : (
               <span className="text-mb-green font-bold flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5" /> Up to date</span>
             )}
           </div>
        </div>
      </div>

      {/* 6. Personalized Insight */}
      <div className="flex flex-col mt-2">
        <div className="p-5 bg-mb-glass-strong backdrop-blur-xl border border-mb-glass-border rounded-3xl">
          <div className="flex gap-4 items-start">
             <div className="mt-0.5 shrink-0"><ShieldCheck className="w-5 h-5 text-mb-accent opacity-80" /></div>
             <p className="text-sm font-medium text-mb-text-secondary leading-relaxed">
               {isAssessmentDue 
                  ? "Your daily assessment is due. Please log your operational telemetry." 
                  : latestAssessment?.stress_level === "High" 
                    ? "Your current stress level is elevated. Preventive measures and recovery are strongly advised."
                    : latestAssessment?.stress_level === "Medium"
                    ? "Your current stress level is moderate. Maintain consistent recovery routines."
                    : "Your wellbeing indicators are optimal. Keep up the good work and maintain your baseline."}
             </p>
          </div>
        </div>
      </div>

      {/* Active Welfare Requests (Fallback to maintain functionality) */}
      {welfareRequests.length > 0 && (
        <div className="flex flex-col mt-2 gap-3">
          <span className="text-[10px] uppercase font-bold tracking-widest text-mb-text-muted mb-1">Active Welfare Requests</span>
          {welfareRequests.map((req) => (
            <div key={req.id} className="flex justify-between items-center text-xs py-3 border-b border-mb-glass-border">
              <span className="text-mb-text-secondary opacity-80 line-clamp-1 flex-1 pr-4">{req.message || "Welfare request"}</span>
              <span className={`px-2 py-1 rounded-full text-[9px] font-bold uppercase shrink-0 ${
                  req.status === "resolved" ? "bg-emerald-500/10 text-mb-green"
                    : req.status === "in_progress" ? "bg-purple-500/10 text-purple-400"
                    : req.status === "acknowledged" ? "bg-blue-500/10 text-blue-400"
                    : "bg-amber-500/10 text-mb-saffron"
                }`}>
                {req.status.replace('_', ' ')}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* 7. Primary Action & Welfare */}
      <div className="flex flex-col gap-5 mt-6">
         <Link 
           href="/assessment" 
           className={`w-full py-4 rounded-3xl flex justify-center items-center gap-2 text-sm font-bold transition-transform active:scale-[0.98] ${
             isAssessmentDue 
               ? "bg-mb-saffron text-black shadow-lg shadow-saffron/20" 
               : "bg-mb-glass-strong backdrop-blur-xl border border-mb-glass-border text-mb-text-primary hover:bg-white/10"
           }`}
         >
           {isAssessmentDue ? "Start Assessment" : "View Assessment"} <ArrowRight className="w-4 h-4" />
         </Link>
         
         <button 
           onClick={() => setShowSupportSheet(true)} 
           className="w-full py-2 text-xs font-semibold text-mb-text-secondary hover:text-mb-text-primary transition-colors uppercase tracking-widest"
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


