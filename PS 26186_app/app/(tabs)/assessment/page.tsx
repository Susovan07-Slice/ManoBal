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
import { StressEmojiScale } from "@/components/ui/StressEmojiScale";

const SCREENS = [
  { id: "intro", type: "intro", bg: "/assessment_pics/1.png", cardTopColor: "#d3d8cd", title: "Daily Assessment", subtitle: "Single unified operational duty, recovery, and wellness reporting." },
  { id: "dutyHours", section: "Operational Duty", type: "slider", min: 20, max: 90, step: 2, unit: "hrs/week", bg: "/assessment_pics/2.png", cardTopColor: "#cfd6c9", title: "Weekly Duty Hours", subtitle: "Standard military pacing ~44-52 hrs" },
  { id: "consecDays", section: "Operational Duty", type: "slider", min: 0, max: 30, step: 1, unit: "days", bg: "/assessment_pics/3.png", cardTopColor: "#b8c3b6", title: "Consecutive Duty Days", subtitle: "Without 24h rest" },
  { id: "nightShifts", section: "Operational Duty", type: "slider", min: 0, max: 20, step: 1, unit: "shifts", bg: "/assessment_pics/5.png", cardTopColor: "#93a8a8", title: "Night Shifts (Last 30 Days)", subtitle: "Total number of night shifts" },
  { id: "opExposure", section: "Operational Duty", type: "choice", options: ["Low", "Medium", "High"], bg: "/assessment_pics/4.png", cardTopColor: "#b8c2b7", title: "Operational Exposure Level", subtitle: "Select your perceived exposure" },
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
        <div className="w-full mt-4">
          <div className="flex justify-end items-center mb-6">
            <span className="text-3xl font-semibold text-brand-500 tabular-nums">
              {value} <span className="text-sm text-ink-3">{screen.unit}</span>
            </span>
          </div>
          <input
            type="range"
            min={screen.min}
            max={screen.max}
            step={screen.step}
            value={value}
            onChange={(e) => setter(parseFloat(e.target.value))}
            className="w-full accent-brand-500"
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
        <div className="w-full mt-4">
          <div className="flex bg-sky-50 border border-sky-200 rounded-2xl p-1 gap-1">
            {screen.options?.map((opt, idx) => {
              const actualValue = isIndexBased ? idx : opt;
              const isSelected = value === actualValue;
              return (
                <button
                  key={opt}
                  type="button"
                  onClick={() => setter(actualValue)}
                  className={`flex-1 py-1.5 text-sm font-bold transition-all duration-300 border ${
                    isSelected
                      ? "bg-white border-brand-500/30 text-ink shadow-sm rounded-xl"
                      : "border-transparent text-ink-3 hover:text-ink hover:bg-white/50 rounded-xl"
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
        <div className="w-full mt-4">
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
      <div className="flex flex-col h-full items-center justify-center p-6 text-center space-y-4">
        <div className="w-12 h-12 border-3 border-brand-500 border-t-transparent rounded-full animate-spin" />
        <div>
          <p className="text-base font-semibold text-ink">Running AI Stress Pipeline...</p>
          <p className="text-xs text-ink-3 mt-1 font-mono">
            Evaluating combined operational & wellbeing telemetry via LightGBM
          </p>
        </div>
      </div>
    );
  }

  if (assessmentResult) {
    const scoreVal = typeof assessmentResult.risk_score === 'number'
      ? assessmentResult.risk_score
      : parseFloat(String(assessmentResult.risk_score)) || 0;

    let parsedFactors: any = {};
    if (typeof assessmentResult.key_factors === 'string') {
      try {
        parsedFactors = JSON.parse(assessmentResult.key_factors);
      } catch (e) {
        parsedFactors = { top_risk_factors: [assessmentResult.key_factors] };
      }
    } else if (Array.isArray(assessmentResult.key_factors)) {
      parsedFactors = { top_risk_factors: assessmentResult.key_factors };
    }

    const category = assessmentResult.risk_category ||
      (scoreVal >= 85 ? "Critical" :
       scoreVal >= 70 ? "High" :
       scoreVal >= 55 ? "Elevated" :
       scoreVal >= 35 ? "Moderate" : "Low");

    const topFactors: string[] = (
      parsedFactors.top_risk_factors ||
      assessmentResult.top_risk_factors ||
      (Array.isArray(assessmentResult.key_factors) ? assessmentResult.key_factors : [])
    ).slice(0, 4);

    const protective: string[] = (
      parsedFactors.protective_factors ||
      assessmentResult.protective_factors ||
      []
    ).slice(0, 3);

    const categoryColor =
      category === "Critical" ? "text-danger bg-danger/10 border-danger/20" :
      category === "High" ? "text-alert bg-alert-bg border-alert/20" :
      category === "Elevated" ? "text-warn bg-warn-bg border-warn/20" :
      category === "Moderate" ? "text-brand-500 bg-brand-100 border-brand-500/20" :
      "text-ok bg-ok-bg border-ok/20";

    const barColor =
      category === "Critical" ? "bg-danger" :
      category === "High" ? "bg-alert" :
      category === "Elevated" ? "bg-warn" :
      category === "Moderate" ? "bg-brand-500" :
      "bg-ok";

    return (
      <div className="p-5 flex flex-col gap-5 pb-32 relative min-h-screen">
        {/* Status Confirmation Banner */}
        <div className="glass-card p-5 flex items-center gap-3 bg-ok-bg/30 border-ok/20">
          <div className="w-8 h-8 rounded-full bg-ok-bg flex items-center justify-center shrink-0">
            <CheckCircle2 className="w-5 h-5 text-ok" />
          </div>
          <div>
            <h3 className="text-ink font-semibold">Daily Assessment Completed</h3>
          </div>
        </div>

        {/* Welfare Risk Score Card */}
        <div className="glass-card p-6 text-center">
          <span className="eyebrow block mb-4">Continuous Welfare Risk</span>
          
          <div className="relative w-48 h-48 mx-auto mb-4 flex items-center justify-center">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke="#BFE3F0"
                strokeWidth="8"
              />
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                className={`transition-all duration-1000 ease-out`}
                stroke={category === 'Critical' ? '#E5484D' : category === 'High' ? '#F0508C' : category === 'Elevated' ? '#F5A623' : category === 'Moderate' ? '#2A9BC8' : '#2FBF8F'}
                strokeWidth="8"
                strokeDasharray={`${(scoreVal / 100) * 283} 283`}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-[44px] font-semibold text-ink tabular-nums leading-none">
                {scoreVal.toFixed(1)}
              </span>
              <span className="text-sm text-ink-3">/ 100</span>
            </div>
          </div>

          <div className={`inline-block px-4 py-1.5 rounded-full border text-sm font-semibold mb-4 ${categoryColor}`}>
            {category} Concern
          </div>

          {/* Continuous Progress Bar */}
          <div className="w-full bg-sky-200 rounded-full h-2 overflow-hidden relative mb-2">
            <div
              className={`h-full rounded-full transition-all duration-1000 ease-out ${barColor}`}
              style={{ width: `${Math.min(100, Math.max(5, scoreVal))}%` }}
            />
          </div>

          <StressEmojiScale score={scoreVal} />
        </div>

        {/* What is Contributing (Risk Factors) */}
        {topFactors.length > 0 && (
          <div className="glass-card p-5">
            <h4 className="eyebrow mb-4 flex items-center gap-2">
              <div className="w-10 h-10 rounded-full bg-warn-bg flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-warn" />
              </div>
              Contributing Factors
            </h4>
            <div className="flex flex-wrap gap-2">
              {topFactors.map((factor, idx) => (
                <span key={idx} className="px-3 py-1.5 bg-sky-50 rounded-full text-[12px] text-ink-2 font-medium border border-sky-200">
                  {factor}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Protective Factors */}
        {protective.length > 0 && (
          <div className="glass-card p-5">
            <h4 className="eyebrow mb-4 flex items-center gap-2">
              <div className="w-10 h-10 rounded-full bg-ok-bg flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-ok" />
              </div>
              Protective Factors
            </h4>
            <div className="flex flex-wrap gap-2">
              {protective.map((factor, idx) => (
                <span key={idx} className="px-3 py-1.5 bg-sky-50 rounded-full text-[12px] text-ink-2 font-medium border border-sky-200">
                  {factor}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Recommended Action */}
        {assessmentResult.recommendations && assessmentResult.recommendations.length > 0 && (
          <div className="glass-card p-5">
            <h4 className="eyebrow mb-4 flex items-center gap-2">
              <div className="w-10 h-10 rounded-full bg-brand-100 flex items-center justify-center">
                <HeartPulse className="w-5 h-5 text-brand-500" />
              </div>
              Recommended Guidance
            </h4>
            <div className="space-y-3">
              {assessmentResult.recommendations.slice(0, 2).map((rec: any, idx: number) => (
                <div key={idx} className="p-4 bg-sky-50/50 rounded-2xl border border-sky-200/50">
                  <div className="font-semibold text-sm text-ink mb-1">{rec.recommendation_type || rec.type || "Welfare Action"}</div>
                  <div className="text-ink-3 text-sm mb-3">{rec.recommendation_text || rec.action || String(rec)}</div>
                  <button onClick={() => handleRecStatusChange(rec.id, 'IN_PROGRESS')} className="rounded-full text-[11px] px-3 py-1 border border-brand-500 text-brand-500">
                    {rec.status || 'Mark in Progress'}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Navigation Action Buttons */}
        <div className="flex gap-3 mt-4 mb-8">
          <Link
            href="/"
            className="flex-1 py-3 bg-white border border-sky-200 hover:bg-sky-50 rounded-full text-[15px] font-bold text-ink text-center transition-colors"
          >
            Dashboard
          </Link>
          <Link
            href="/trends"
            className="flex-1 py-3 bg-brand-500 hover:opacity-90 rounded-full text-[15px] font-bold text-white text-center transition-colors"
          >
            View Trends
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="relative min-h-screen flex flex-col">
      {/* Top Header Section */}
      <div className="pt-12 px-6 pb-4 flex justify-between items-center z-10">
        <button
          onClick={currentIndex > 0 ? handleBack : undefined}
          className={`p-2 rounded-full bg-white border border-sky-200 text-ink transition-opacity shadow-sm ${currentIndex === 0 ? "opacity-0 pointer-events-none" : "opacity-100"}`}
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
        {currentIndex > 0 && currentIndex < SCREENS.length - 1 && (
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] font-bold text-ink-3 tracking-widest uppercase">
              {String(currentIndex).padStart(2, '0')} / {String(SCREENS.length - 2).padStart(2, '0')}
            </span>
          </div>
        )}
        <div className="w-9 h-9" />
      </div>

      {/* Main Content Area (center-aligned, pushed up slightly) */}
      <div className="flex-1 flex flex-col justify-center p-5 pb-40 z-10 w-full">
        {screen.type === "intro" ? (
          <div className="glass-card p-8 text-center flex flex-col items-center animate-fade-up">
            <h2 className="text-2xl font-bold text-ink">{screen.title}</h2>
            <p className="text-[14px] text-ink-2 mt-2 mb-8">{screen.subtitle}</p>
            <Button onClick={handleNext} className="w-full justify-center gap-2 rounded-full py-4 text-base bg-brand-500 text-white">
              Start Assessment <ArrowRight className="w-5 h-5" />
            </Button>
          </div>
        ) : screen.type === "completion" ? (
          <div className="glass-card p-8 text-center flex flex-col items-center animate-fade-up">
            <div className="w-16 h-16 rounded-full bg-ok-bg flex items-center justify-center mb-4">
              <CheckCircle2 className="w-8 h-8 text-ok" />
            </div>
            <h2 className="text-2xl font-bold text-ink">{screen.title}</h2>
            <p className="text-[14px] text-ink-2 mt-2 mb-8">{screen.subtitle}</p>
            <Button onClick={handleSubmitAssessment} className="w-full justify-center gap-2 rounded-full py-4 text-base bg-brand-500 text-white">
              Submit Assessment <CheckCircle2 className="w-5 h-5" />
            </Button>
            {error && (
              <div className="mt-4 text-danger text-sm">
                {error}
                <button onClick={handleSubmitAssessment} className="ml-2 px-3 py-1 bg-white text-brand-500 border border-sky-200 rounded-full text-xs">
                  Retry
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="glass-card p-6 animate-fade-up w-full flex flex-col">
            <div className="mb-2">
              {screen.section && (
                <span className="eyebrow mb-2 block">{screen.section}</span>
              )}
              <h2 className="text-xl font-bold text-ink leading-snug">{screen.title}</h2>
              {screen.subtitle && (
                <p className="text-[13px] text-ink-3 mt-1">{screen.subtitle}</p>
              )}
            </div>

            <div className="flex-1 flex flex-col justify-center">
              {renderControl()}
              <div className="flex justify-between items-center mt-6 mb-4 gap-3">
                <Button variant="ghost" onClick={handleBack} className="flex-1 justify-center gap-1 py-3 rounded-full border border-sky-200 bg-white text-ink hover:bg-sky-50">
                  <ChevronLeft className="w-4 h-4" /> Previous
                </Button>
                <Button onClick={handleNext} className="flex-1 justify-center gap-2 py-3 rounded-full bg-brand-500 text-white">
                  Next <ArrowRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function AssessmentPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center p-6 bg-white/50">
          <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      }
    >
      <AssessmentContent />
    </Suspense>
  );
}




    {/* This is a comment inside TSX markup */}
