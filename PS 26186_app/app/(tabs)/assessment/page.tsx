"use client";

import React, { useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { submitAssessment } from "@/lib/assessment";
import { StressAssessmentOut, AssessmentOverride } from "@/types/api";
import { useAuth } from "@/lib/AuthContext";
import { RatingSlider } from "@/components/ui/RatingSlider";
import { Button } from "@/components/ui/Button";
import { CheckCircle2, ChevronLeft, ArrowRight, HeartPulse, AlertTriangle, Sparkles, Clock } from "lucide-react";
import Link from "next/link";
import { apiClient } from "@/lib/api";

const SCREENS = [
  { id: "intro", type: "intro", bg: "/assessment_pics/1.png", cardTopColor: "#d3d8cd", title: "Daily Assessment", subtitle: "Single unified operational duty, recovery, and wellness reporting." },
  { id: "dutyHours", section: "Operational Duty", type: "slider", min: 20, max: 90, step: 2, unit: "hrs/week", bg: "/assessment_pics/2.png", cardTopColor: "#cfd6c9", title: "Weekly Duty Hours", subtitle: "Standard military pacing ~44-52 hrs" },
  { id: "consecDays", section: "Operational Duty", type: "slider", min: 0, max: 30, step: 1, unit: "days", bg: "/assessment_pics/3.png", cardTopColor: "#b8c3b6", title: "Consecutive Duty Days", subtitle: "Without 24h rest" },
  { id: "nightShifts", section: "Operational Duty", type: "slider", min: 0, max: 20, step: 1, unit: "shifts", bg: "/assessment_pics/4.png", cardTopColor: "#93a8a8", title: "Night Shifts (Last 30 Days)", subtitle: "Total number of night shifts" },
  { id: "opExposure", section: "Operational Duty", type: "choice", options: ["Low", "Medium", "High"], bg: "/assessment_pics/5.png", cardTopColor: "#b8c2b7", title: "Operational Exposure Level", subtitle: "Select your perceived exposure" },
  { id: "sleepHours", section: "Recovery & Rest", type: "slider", min: 2.0, max: 12.0, step: 0.5, unit: "hrs", bg: "/assessment_pics/6.jpg", cardTopColor: "#99b0ac", title: "Restorative Sleep", subtitle: "Average sleep duration per 24h" },
  { id: "physicalFatigue", section: "Recovery & Rest", type: "rating", min: 1, max: 5, bg: "/assessment_pics/7.jpg", cardTopColor: "#bac5c0", title: "Physical Fatigue Level", subtitle: "1 = Fully refreshed, 5 = Severe fatigue" },
  { id: "physicalActivity", section: "Recovery & Rest", type: "slider", min: 0, max: 25, step: 1, unit: "hrs/wk", bg: "/assessment_pics/8.jpg", cardTopColor: "#a3b1a8", title: "Physical Conditioning", subtitle: "Physical training hours per week" },
  { id: "moodScore", section: "Wellbeing & Morale", type: "rating", min: 1, max: 5, bg: "/assessment_pics/9.jpg", cardTopColor: "#c2cfbd", title: "Overall Morale & Mood", subtitle: "1 = Distressed, 5 = Highly Resilient" },
  { id: "burnoutSymptoms", section: "Wellbeing & Morale", type: "choice", options: ["Rarely", "Sometimes", "Often"], bg: "/assessment_pics/10.jpg", cardTopColor: "#aebfae", title: "Burnout / Overwhelm Symptoms", subtitle: "Frequency of feeling overwhelmed" },
  { id: "interestScore", section: "Wellbeing & Morale", type: "choice", options: ["None", "Mild", "Mod", "High"], bg: "/assessment_pics/11.jpg", cardTopColor: "#b0bfad", title: "Interest or satisfaction in daily tasks & duty:", subtitle: "Select severity" },
  { id: "discouragedScore", section: "Wellbeing & Morale", type: "choice", options: ["Rarely", "Some", "Often", "Const"], bg: "/assessment_pics/12.jpg", cardTopColor: "#94a8a0", title: "Feeling down, discouraged, or mentally exhausted:", subtitle: "Select frequency" },
  { id: "concentrationScore", section: "Wellbeing & Morale", type: "choice", options: ["Never", "Rare", "Often", "Severe"], bg: "/assessment_pics/13.jpg", cardTopColor: "#abbab2", title: "Trouble concentrating on operational procedures:", subtitle: "Select frequency" },
  { id: "completion", type: "completion", bg: "/assessment_pics/14.jpg", cardTopColor: "#b2bfad", title: "Assessment Complete", subtitle: "You have completed today's wellness assessment." }
];

function AssessmentContent() {
  const { user } = useAuth();
  const searchParams = useSearchParams();
  const router = useRouter();
  const reason = searchParams.get("reason");

  const [currentIndex, setCurrentIndex] = useState(0);

  // Exact state matches original implementation
  const [dutyHours, setDutyHours] = useState<number>(48);
  const [consecDays, setConsecDays] = useState<number>(4);
  const [nightShifts, setNightShifts] = useState<number>(3);
  const [opExposure, setOpExposure] = useState<"Low" | "Medium" | "High">("Medium");
  const [remotePosting, setRemotePosting] = useState<"Yes" | "No">("No");
  const [sleepHours, setSleepHours] = useState<number>(6.5);
  const [physicalFatigue, setPhysicalFatigue] = useState<number>(2);
  const [physicalActivity, setPhysicalActivity] = useState<number>(5);
  const [moodScore, setMoodScore] = useState<number>(4);
  const [burnoutSymptoms, setBurnoutSymptoms] = useState<"Rarely" | "Sometimes" | "Often">("Rarely");
  const [interestScore, setInterestScore] = useState<number>(0);
  const [discouragedScore, setDiscouragedScore] = useState<number>(0);
  const [concentrationScore, setConcentrationScore] = useState<number>(0);

  // Submission & evaluation state
  const [evaluating, setEvaluating] = useState(false);
  const [assessmentResult, setAssessmentResult] = useState<StressAssessmentOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [updatingRecId, setUpdatingRecId] = useState<number | null>(null);

  const handleSubmitAssessment = async () => {
    setEvaluating(true);
    setError(null);

    // Compute burnout symptoms if wellbeing questions indicate severe fatigue or discouragement
    let finalBurnout = burnoutSymptoms;
    if (discouragedScore >= 2 || concentrationScore >= 2 || consecDays > 14) {
      finalBurnout = "Often";
    } else if (discouragedScore === 1 || consecDays > 7) {
      if (finalBurnout === "Rarely") finalBurnout = "Sometimes";
    }

    const overridePayload: AssessmentOverride = {
      duty_hours_per_week: dutyHours,
      consecutive_duty_days: consecDays,
      night_shifts_per_month: nightShifts,
      leave_gap_days: consecDays > 10 ? 90 : 30,
      sleep_hours: sleepHours,
      physical_activity_hours_per_week: physicalActivity,
      operational_exposure: opExposure,
      remote_posting: remotePosting,
      mood_score: moodScore,
      burnout_symptoms: finalBurnout,
      physical_fatigue: physicalFatigue,
      interest_score: interestScore,
      discouraged_score: discouragedScore,
      concentration_score: concentrationScore,
    };

    const targetPersonnelId = user?.personnel_id || 1;

    try {
      const response = await submitAssessment(targetPersonnelId, overridePayload);
      setAssessmentResult(response.assessment);

      if (user?.personnel_id && typeof window !== "undefined") {
        sessionStorage.removeItem(`assessment_dismissed_${user.personnel_id}`);
      }
    } catch (err: any) {
      console.error("Assessment inference failed:", err);
      setError(err?.message || "Failed to submit assessment to ML backend.");
    } finally {
      setEvaluating(false);
    }
  };

  const handleRecStatusChange = async (recId: number, newStatus: string) => {
    setUpdatingRecId(recId);
    try {
      await apiClient(`/recommendations/${recId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status: newStatus }),
      });
      if (assessmentResult) {
        setAssessmentResult({
          ...assessmentResult,
          recommendations: assessmentResult.recommendations.map((r) =>
            r.id === recId ? { ...r, status: newStatus as any } : r
          ),
        });
      }
    } catch (err: any) {
      alert(`Could not update recommendation: ${err?.message || "Access restricted"}`);
    } finally {
      setUpdatingRecId(null);
    }
  };

  const screen = SCREENS[currentIndex];

  const handleNext = () => {
    if (currentIndex < SCREENS.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const handleBack = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  const renderControl = () => {
    if (screen.type === "slider") {
      let value = 0;
      let setter: any = null;
      if (screen.id === "dutyHours") { value = dutyHours; setter = setDutyHours; }
      if (screen.id === "consecDays") { value = consecDays; setter = setConsecDays; }
      if (screen.id === "nightShifts") { value = nightShifts; setter = setNightShifts; }
      if (screen.id === "sleepHours") { value = sleepHours; setter = setSleepHours; }
      if (screen.id === "physicalActivity") { value = physicalActivity; setter = setPhysicalActivity; }

      return (
        <div className="w-full">
          <div className="flex justify-between items-center mb-6">
            <span className="text-mb-text-primary font-semibold text-[13px] tracking-wider uppercase">{screen.title}</span>
            <span className="font-mono font-bold text-mb-accent text-2xl">{value} <span className="text-xs font-normal text-mb-text-secondary">{screen.unit}</span></span>
          </div>
          <input
            type="range"
            min={screen.min}
            max={screen.max}
            step={screen.step}
            value={value}
            onChange={(e) => setter(parseFloat(e.target.value))}
            className="w-full"
          />
        </div>
      );
    }

    if (screen.type === "choice") {
      let value: any;
      let setter: any = null;
      if (screen.id === "opExposure") { value = opExposure; setter = setOpExposure; }
      if (screen.id === "burnoutSymptoms") { value = burnoutSymptoms; setter = setBurnoutSymptoms; }
      if (screen.id === "interestScore") { value = interestScore; setter = setInterestScore; }
      if (screen.id === "discouragedScore") { value = discouragedScore; setter = setDiscouragedScore; }
      if (screen.id === "concentrationScore") { value = concentrationScore; setter = setConcentrationScore; }

      const isIndexBased = ["interestScore", "discouragedScore", "concentrationScore"].includes(screen.id);

      return (
        <div className="w-full">
          <div className="flex bg-gradient-to-br from-slate-50 to-slate-100 border border-slate-200 rounded-2xl p-1 shadow-inner gap-1">
            {screen.options?.map((opt, idx) => {
              const actualValue = isIndexBased ? idx : opt;
              const isSelected = value === actualValue;
              return (
                <button
                  key={opt}
                  type="button"
                  onClick={() => setter(actualValue)}
                  className={`flex-1 py-1.5 text-sm rounded-xl font-bold transition-all duration-300 border ${
                    isSelected
                      ? "bg-gradient-to-b from-mb-accent/20 to-mb-accent/5 border-mb-accent/30 text-mb-text-primary shadow-sm"
                      : "border-transparent text-mb-text-muted hover:text-mb-text-primary hover:bg-white/50"
                  }`}
                >
                  {opt}
                </button>
              );
            })}
          </div>
        </div>
      );
    }

    if (screen.type === "rating") {
      let value = 0;
      let setter: any = null;
      if (screen.id === "physicalFatigue") { value = physicalFatigue; setter = setPhysicalFatigue; }
      if (screen.id === "moodScore") { value = moodScore; setter = setMoodScore; }

      return (
        <div className="w-full">
          <RatingSlider
            label=""
            value={value}
            onChange={setter}
            min={screen.min || 1}
            max={screen.max || 5}
          />
        </div>
      );
    }

    return null;
  };

  if (evaluating) {
    return (
      <div className="flex flex-col h-full items-center justify-center text-mb-text-secondary p-6 text-center space-y-4">
        <div className="absolute inset-0 z-[-1] bg-[#0a110e]" />
        <div className="w-12 h-12 border-3 border-mb-accent border-t-transparent rounded-full animate-spin" />
        <div>
          <p className="text-base font-semibold text-mb-text-primary">Running AI Stress Pipeline...</p>
          <p className="text-xs text-mb-text-secondary mt-1 font-mono">
            Evaluating combined operational & wellbeing telemetry via LightGBM
          </p>
        </div>
      </div>
    );
  }

  if (assessmentResult) {
    return (
      <div className="p-4 flex flex-col gap-5 animate-in fade-in duration-500 pb-24 relative min-h-screen">
        <div className="absolute inset-0 z-[-1] bg-[#0a110e] transition-opacity duration-1000" />
        {/* Unified Result Component */}
        <div className="p-4 bg-mb-accent/10 border border-mb-accent/30 rounded-xl flex items-center space-x-3 mt-4">
          <CheckCircle2 className="w-7 h-7 text-mb-accent shrink-0" />
          <div>
            <h3 className="text-sm font-bold text-mb-text-primary">Daily Assessment Completed</h3>
            <p className="text-xs text-mb-text-secondary">
              Evaluated via LightGBM Pipeline ({assessmentResult.model_version}) • 24h Timer Active
            </p>
          </div>
        </div>
        <div className="flex flex-col items-center mt-4 mb-8">
          <span className="text-[10px] uppercase font-bold tracking-widest text-mb-text-secondary mb-6">Continuous Risk Result</span>
          <div className="text-[80px] font-light text-mb-text-primary mb-2 tracking-tighter leading-none">
            {typeof assessmentResult.risk_score === 'number'
              ? assessmentResult.risk_score.toFixed(1)
              : assessmentResult.risk_score}
          </div>
          <div className={`text-xl font-medium mb-8 ${
            assessmentResult.stress_level === "High" ? "text-mb-danger" : 
            assessmentResult.stress_level === "Medium" ? "text-mb-saffron" : "text-mb-green"
          }`}>
            {assessmentResult.stress_level} Risk
          </div>
          <div className="w-full max-w-xs h-1.5 bg-white/10 rounded-full overflow-hidden mb-6 relative">
             <div 
               className={`absolute top-0 left-0 h-full rounded-full transition-all duration-1000 ease-out ${
                 assessmentResult.stress_level === "High" ? "bg-mb-danger w-[85%]" : 
                 assessmentResult.stress_level === "Medium" ? "bg-mb-saffron w-[55%]" : "bg-mb-green w-[25%]"
               }`}
             />
          </div>
        </div>
        <div className="flex gap-3 mt-auto">
          <Link href="/" className="flex-1 py-3 bg-mb-glass-strong hover:bg-white/10 border border-mb-glass-border rounded-2xl text-sm font-semibold text-mb-text-primary text-center transition-colors">
            Dashboard
          </Link>
          <Link href="/trends" className="flex-1 py-3 bg-mb-accent hover:opacity-90 rounded-2xl text-sm font-bold text-mb-text-dark text-center flex items-center justify-center transition-colors">
            View Trends
          </Link>
        </div>
      </div>
    );
  }

  // Active Screen UI
  return (
    <div className="relative min-h-screen flex flex-col">
      {/* Dynamic Background Image overlay for just this page */}
      {SCREENS.map((s, idx) => (
        <div
          key={s.id}
          className={`absolute inset-0 z-[-1] bg-cover bg-center transition-opacity duration-700 ease-in-out ${
            idx === currentIndex ? "opacity-100" : "opacity-0"
          }`}
          style={{ backgroundImage: `url('${s.bg}')` }}
        />
      ))}
      <div className="absolute inset-0 z-[-1] bg-gradient-to-b from-transparent via-transparent to-[#0a110e]/80" />

      {/* Top Header Section */}
      <div className="pt-12 px-6 pb-4 flex justify-between items-center z-10">
        <button
          onClick={currentIndex > 0 ? handleBack : undefined}
          className={`p-2 rounded-full bg-black/20 backdrop-blur-md border border-white/10 text-white transition-opacity ${currentIndex === 0 ? "opacity-0 pointer-events-none" : "opacity-100"}`}
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
        {currentIndex > 0 && currentIndex < SCREENS.length - 1 && (
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] font-bold text-white/90 tracking-widest uppercase">
              {String(currentIndex).padStart(2, '0')} / {String(SCREENS.length - 2).padStart(2, '0')}
            </span>
          </div>
        )}
        <div className="w-9 h-9" /> {/* spacer */}
      </div>

      {/* Main Content Area (bottom-aligned) */}
      <div className="mt-auto p-5 pb-32 z-10 flex flex-col gap-5 w-full">
        <div 
          className="rounded-[32px] p-6 shadow-[0_8px_30px_rgba(0,0,0,0.12)] min-h-[220px] flex flex-col justify-center relative overflow-hidden border border-white/60"
          style={{
            background: `linear-gradient(to bottom, ${screen.cardTopColor} 0%, #f3f5f0 45%, #fdfcf8 100%)`
          }}
        >
          
          <div className="mb-8">
            {screen.section && (
              <span className="text-[10px] text-mb-accent font-bold tracking-widest uppercase block mb-1.5">{screen.section}</span>
            )}
            <h2 className="text-xl font-bold text-mb-text-primary tracking-wide leading-snug">{screen.title}</h2>
            {screen.subtitle && (
              <p className="text-[12px] text-mb-text-secondary mt-1.5">{screen.subtitle}</p>
            )}
          </div>

          {screen.type === "intro" ? (
             <div className="space-y-4 mt-auto">
               <Button onClick={handleNext} className="w-full justify-center gap-2 bg-mb-accent hover:opacity-90 text-mb-text-dark font-bold py-4 rounded-2xl shadow-lg shadow-teal-900/20 text-base">
                 Start Assessment <ArrowRight className="w-5 h-5" />
               </Button>
             </div>
          ) : screen.type === "completion" ? (
            <div className="space-y-4 mt-auto">
               <Button onClick={handleSubmitAssessment} className="w-full justify-center gap-2 bg-mb-accent hover:opacity-90 text-mb-text-dark font-bold py-4 rounded-2xl shadow-lg shadow-teal-900/20 text-base">
                 Submit Assessment <CheckCircle2 className="w-5 h-5" />
               </Button>
            </div>
          ) : (
             <div className="flex-1 flex flex-col justify-center">
               {renderControl()}
               <div className="mt-10 flex gap-3">
                 <Button onClick={handleBack} className="flex-1 justify-center gap-1 bg-white/5 hover:bg-white/10 border border-white/10 text-mb-text-primary font-semibold py-3.5 rounded-2xl transition-colors">
                   <ChevronLeft className="w-4 h-4" /> Previous
                 </Button>
                 <Button onClick={handleNext} className="flex-1 justify-center gap-2 bg-mb-glass hover:bg-white/10 border border-white/20 text-mb-text-primary font-bold py-3.5 rounded-2xl transition-colors">
                   Next <ArrowRight className="w-4 h-4" />
                 </Button>
               </div>
             </div>
          )}

        </div>
      </div>
    </div>
  );
}

export default function AssessmentPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center p-6 text-mb-text-secondary bg-[#0a110e]">
          <div className="w-8 h-8 border-2 border-mb-accent border-t-transparent rounded-full animate-spin" />
        </div>
      }
    >
      <AssessmentContent />
    </Suspense>
  );
}
