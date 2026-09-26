"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { submitAssessment } from "@/lib/assessment";
import { StressAssessmentOut, AssessmentOverride } from "@/types/api";
import { useAuth } from "@/lib/AuthContext";
import { RatingSlider } from "@/components/ui/RatingSlider";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import {
  Activity,
  HeartPulse,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ShieldCheck,
  ChevronRight,
  ChevronLeft,
  ArrowRight,
  ShieldAlert,
  Info,
  Sliders,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import { apiClient } from "@/lib/api";

function AssessmentContent() {
  const { user } = useAuth();
  const searchParams = useSearchParams();
  const router = useRouter();

  const reason = searchParams.get("reason");

  // Step wizard state: 1 = Duty & Ops, 2 = Recovery & Rest, 3 = Wellbeing & Morale
  const [step, setStep] = useState<1 | 2 | 3>(1);

  // Section A: Daily Duty & Operational Information
  const [dutyHours, setDutyHours] = useState<number>(48);
  const [consecDays, setConsecDays] = useState<number>(4);
  const [nightShifts, setNightShifts] = useState<number>(3);
  const [opExposure, setOpExposure] = useState<"Low" | "Medium" | "High">("Medium");
  const [remotePosting, setRemotePosting] = useState<"Yes" | "No">("No");

  // Section B: Personal Welfare & Recovery
  const [sleepHours, setSleepHours] = useState<number>(6.5);
  const [physicalFatigue, setPhysicalFatigue] = useState<number>(2);
  const [physicalActivity, setPhysicalActivity] = useState<number>(5);

  // Section C: Stress & Wellbeing Indicators
  const [moodScore, setMoodScore] = useState<number>(4);
  const [burnoutSymptoms, setBurnoutSymptoms] = useState<"Rarely" | "Sometimes" | "Often">("Rarely");
  const [interestScore, setInterestScore] = useState<number>(0); // 0=Not at all, 1=Several days, 2=More than half, 3=Nearly every day
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

      // Clear any session dismiss flag so next visit checks updated database state
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

  if (evaluating) {
    return (
      <div className="flex flex-col h-full items-center justify-center text-slate-300 p-6 text-center space-y-4">
        <div className="w-12 h-12 border-3 border-teal-500 border-t-transparent rounded-full animate-spin" />
        <div>
          <p className="text-base font-semibold text-slate-100">Running AI Stress Pipeline...</p>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Evaluating combined operational & wellbeing telemetry via LightGBM
          </p>
        </div>
      </div>
    );
  }

  // Display Unified Assessment Result (Section 3, 4, 5, 13)
  if (assessmentResult) {
    return (
      <div className="p-4 flex flex-col gap-5 animate-in fade-in duration-500 pb-24">
        {/* Success Banner */}
        <div className="p-4 bg-teal-500/10 border border-teal-500/30 rounded-xl flex items-center space-x-3">
          <CheckCircle2 className="w-7 h-7 text-teal-400 shrink-0" />
          <div>
            <h3 className="text-sm font-bold text-slate-100">Daily Assessment Completed</h3>
            <p className="text-xs text-slate-300">
              Evaluated via LightGBM Pipeline ({assessmentResult.model_version}) • 24h Timer Active
            </p>
          </div>
        </div>

        {/* Core Unified Result Card */}
        <div className="flex flex-col items-center mt-4 mb-8">
          <span className="text-[10px] uppercase font-bold tracking-widest text-slate-400 mb-6">Continuous Risk Result</span>
          
          <div className="text-[80px] font-light text-white mb-2 tracking-tighter leading-none">
            {typeof assessmentResult.risk_score === 'number'
              ? assessmentResult.risk_score.toFixed(1)
              : assessmentResult.risk_score}
          </div>
          <div className={`text-xl font-medium mb-8 ${
            assessmentResult.stress_level === "High" ? "text-saffron" : 
            assessmentResult.stress_level === "Medium" ? "text-amber-400" : "text-emerald-400"
          }`}>
            {assessmentResult.stress_level} Risk
          </div>
          
          <div className="w-full max-w-xs h-1.5 bg-white/10 rounded-full overflow-hidden mb-6 relative">
             <div 
               className={`absolute top-0 left-0 h-full rounded-full transition-all duration-1000 ease-out ${
                 assessmentResult.stress_level === "High" ? "bg-saffron w-[85%]" : 
                 assessmentResult.stress_level === "Medium" ? "bg-amber-400 w-[55%]" : "bg-emerald-400 w-[25%]"
               }`}
             />
          </div>

          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider mb-8">
            <span className="text-slate-400">Priority:</span>
            <span className={`flex items-center gap-1.5 ${
              assessmentResult.risk_priority === "Priority" ? "text-saffron" : 
              assessmentResult.risk_priority === "Preventive" ? "text-amber-400" : "text-emerald-400"
            }`}>
              <div className="w-2 h-2 rounded-full bg-current" />
              {assessmentResult.risk_priority}
            </span>
          </div>

          {/* Key Contributing Model Factors */}
          {assessmentResult.key_factors && assessmentResult.key_factors.length > 0 && (
            <div className="w-full text-left bg-[var(--color-glass-dark)] backdrop-blur-xl border border-[var(--color-glass-border)] rounded-3xl p-6 shadow-2xl">
              <span className="text-xs font-bold text-slate-400 tracking-wider block mb-4 uppercase">
                Primary Associated Factors
              </span>
              <ul className="space-y-3">
                {assessmentResult.key_factors.map((factor, i) => (
                  <li key={i} className="text-sm font-medium text-slate-200 flex items-center space-x-3">
                    <span className="w-1.5 h-1.5 rounded-full bg-teal-500 opacity-80 shrink-0"></span>
                    <span>{factor}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

          {/* Welfare Recommendations */}
          {assessmentResult.recommendations && assessmentResult.recommendations.length > 0 && (
            <div className="pt-2 border-t border-slate-700/60 space-y-2">
              <span className="text-[11px] uppercase font-semibold text-teal-400 tracking-wider flex items-center space-x-1.5">
                <HeartPulse className="w-3.5 h-3.5" />
                <span>Supportive Welfare Interventions:</span>
              </span>
              <div className="space-y-2">
                {assessmentResult.recommendations.map((rec) => (
                  <div
                    key={rec.id}
                    className="p-3 bg-slate-800/60 rounded-lg text-xs space-y-1.5 border border-slate-700"
                  >
                    <div className="flex justify-between items-center">
                      <span className="text-[10px] uppercase font-mono font-bold text-teal-400">
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
                    <p className="text-slate-200">{rec.recommendation_text}</p>
                    {rec.status !== "completed" && (
                      <button
                        disabled={updatingRecId === rec.id}
                        onClick={() => handleRecStatusChange(rec.id, "completed")}
                        className="mt-1 text-[10px] text-teal-400 hover:underline"
                      >
                        Mark Completed
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

        {/* Prototype Ethical Notice */}
        <p className="text-[10px] text-slate-500 italic text-center px-4 leading-normal">
          AI decision-support prototype. Statistical associations only; not medical advice or disciplinary action.
        </p>

        {/* Actions */}
        <div className="flex gap-3">
          <Link
            href="/"
            className="flex-1 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl text-xs font-semibold text-slate-300 text-center transition-colors"
          >
            Dashboard
          </Link>
          <Link
            href="/trends"
            className="flex-1 py-2.5 bg-teal-500 hover:bg-teal-400 rounded-xl text-xs font-bold text-slate-950 text-center flex items-center justify-center transition-colors"
          >
            View Trends
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 flex flex-col h-full pb-20">
      {/* Due Banner if automatically triggered */}
      {reason === "due_24h" && (
        <div className="mb-4 p-3 bg-amber-500/15 border border-amber-500/40 rounded-xl flex items-start gap-2.5 text-xs text-amber-200 animate-in fade-in">
          <Clock className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold text-amber-300 block">Daily Assessment Due</span>
            It has been more than 24 hours since your last completed assessment. Please submit today&apos;s operational and recovery telemetry.
          </div>
        </div>
      )}

      {reason === "initial" && (
        <div className="mb-4 p-3 bg-teal-500/15 border border-teal-500/40 rounded-xl flex items-start gap-2.5 text-xs text-teal-200 animate-in fade-in">
          <Sparkles className="w-4 h-4 text-teal-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold text-teal-300 block">Initial Calibration Assessment</span>
            Welcome to ManoBal! Complete your initial baseline assessment to calibrate your continuous stress telemetry.
          </div>
        </div>
      )}

      {/* Header */}
      <div className="mb-4">
        <h2 className="text-xl font-bold text-slate-100">Daily Assessment</h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Single unified operational duty, recovery, and wellness reporting
        </p>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-950/60 border border-red-800 rounded-xl text-xs text-red-200 flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Stepper Progress */}
      <div className="flex items-center justify-between mb-8 px-2 text-xs font-semibold tracking-widest uppercase">
        <button
          onClick={() => setStep(1)}
          className={`flex-1 text-center transition-all duration-300 pb-2 border-b-2 ${
            step === 1 ? "text-teal-400 border-teal-400" : "text-slate-500 border-transparent hover:text-slate-300"
          }`}
        >
          01 Duty & Ops
        </button>
        <button
          onClick={() => setStep(2)}
          className={`flex-1 text-center transition-all duration-300 pb-2 border-b-2 ${
            step === 2 ? "text-teal-400 border-teal-400" : "text-slate-500 border-transparent hover:text-slate-300"
          }`}
        >
          02 Recovery
        </button>
        <button
          onClick={() => setStep(3)}
          className={`flex-1 text-center transition-all duration-300 pb-2 border-b-2 ${
            step === 3 ? "text-teal-400 border-teal-400" : "text-slate-500 border-transparent hover:text-slate-300"
          }`}
        >
          03 Wellbeing
        </button>
      </div>

      {/* STEP 1: Daily Duty / Operational Information (Section 2.A) */}
      {step === 1 && (
        <div className="space-y-8 animate-in fade-in duration-300">
          <div className="space-y-8">
            {/* Duty Hours */}
            <div className="space-y-2">
              <div className="flex justify-between items-center px-1">
                <span className="text-offwhite font-medium text-sm">Weekly Duty Hours</span>
                <span className="font-mono font-bold text-teal-400 text-lg tracking-wide">{dutyHours} <span className="text-sm font-normal text-slate-400">hrs</span></span>
              </div>
              <input
                type="range"
                min={20}
                max={90}
                step={2}
                value={dutyHours}
                onChange={(e) => setDutyHours(parseInt(e.target.value))}
                className="w-full"
              />
              <span className="text-xs text-slate-400 block px-1">Standard military pacing ~44-52 hrs</span>
            </div>

            {/* Consecutive Duty Days */}
            <div className="space-y-2 pt-6 border-t border-[var(--color-glass-border)]">
              <div className="flex justify-between items-center px-1">
                <span className="text-offwhite font-medium text-sm">Consecutive Duty Days</span>
                <span className="font-mono font-bold text-teal-400 text-lg tracking-wide">{consecDays} <span className="text-sm font-normal text-slate-400">days</span></span>
              </div>
              <input
                type="range"
                min={0}
                max={30}
                step={1}
                value={consecDays}
                onChange={(e) => setConsecDays(parseInt(e.target.value))}
                className="w-full"
              />
              <span className="text-xs text-slate-400 block px-1">Without 24h rest</span>
            </div>

            {/* Night Shifts */}
            <div className="space-y-2 pt-6 border-t border-[var(--color-glass-border)]">
              <div className="flex justify-between items-center px-1">
                <span className="text-offwhite font-medium text-sm">Night Shifts (Last 30 Days)</span>
                <span className="font-mono font-bold text-teal-400 text-lg tracking-wide">{nightShifts} <span className="text-sm font-normal text-slate-400">shifts</span></span>
              </div>
              <input
                type="range"
                min={0}
                max={20}
                step={1}
                value={nightShifts}
                onChange={(e) => setNightShifts(parseInt(e.target.value))}
                className="w-full"
              />
            </div>

            {/* Operational Exposure Level */}
            <div className="space-y-4 pt-6 border-t border-[var(--color-glass-border)]">
              <span className="text-sm text-offwhite font-medium block px-1">Operational Exposure Level</span>
              <div className="grid grid-cols-3 gap-3">
                {(["Low", "Medium", "High"] as const).map((lvl) => (
                  <button
                    key={lvl}
                    type="button"
                    onClick={() => setOpExposure(lvl)}
                    className={`py-3 px-2 text-sm rounded-2xl border font-semibold transition-all duration-300 ${
                      opExposure === lvl
                        ? "bg-teal-600 text-offwhite border-teal-500 shadow-lg shadow-teal-500/20 transform scale-[1.02]"
                        : "bg-[var(--color-glass-dark)] text-slate-400 border-[var(--color-glass-border)] hover:bg-white/10"
                    }`}
                  >
                    {lvl}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <Button onClick={() => setStep(2)} className="w-full justify-center gap-2">
            Next: Recovery & Rest <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      )}

      {/* STEP 2: Personal Welfare / Recovery (Section 2.B) */}
      {step === 2 && (
        <div className="space-y-8 animate-in fade-in duration-300">
          <div className="space-y-8">
            {/* Sleep Hours */}
            <div className="space-y-2">
              <div className="flex justify-between items-center px-1">
                <span className="text-offwhite font-medium text-sm">Restorative Sleep Hours</span>
                <span className="font-mono font-bold text-teal-400 text-lg tracking-wide">{sleepHours} <span className="text-sm font-normal text-slate-400">hrs</span></span>
              </div>
              <input
                type="range"
                min={2.0}
                max={12.0}
                step={0.5}
                value={sleepHours}
                onChange={(e) => setSleepHours(parseFloat(e.target.value))}
                className="w-full"
              />
              <span className="text-xs text-slate-400 block px-1">Average sleep duration per 24h</span>
            </div>

            {/* Physical Fatigue */}
            <div className="pt-6 border-t border-[var(--color-glass-border)]">
              <RatingSlider
                label="Physical Fatigue Level"
                value={physicalFatigue}
                onChange={setPhysicalFatigue}
                min={1}
                max={5}
              />
              <span className="text-xs text-slate-400 block mt-2 px-1">1 = Fully refreshed, 5 = Severe fatigue</span>
            </div>

            {/* Physical Activity / PT */}
            <div className="space-y-2 pt-6 border-t border-[var(--color-glass-border)]">
              <div className="flex justify-between items-center px-1">
                <span className="text-offwhite font-medium text-sm">Physical Conditioning / PT</span>
                <span className="font-mono font-bold text-teal-400 text-lg tracking-wide">{physicalActivity} <span className="text-sm font-normal text-slate-400">hrs/wk</span></span>
              </div>
              <input
                type="range"
                min={0}
                max={25}
                step={1}
                value={physicalActivity}
                onChange={(e) => setPhysicalActivity(parseInt(e.target.value))}
                className="w-full"
              />
            </div>
          </div>

          <div className="flex gap-3">
            <Button variant="ghost" onClick={() => setStep(1)} className="flex-1 justify-center gap-1">
              <ChevronLeft className="w-4 h-4" /> Back
            </Button>
            <Button onClick={() => setStep(3)} className="flex-1 justify-center gap-1">
              Next: Wellbeing <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}

      {/* STEP 3: Stress / Wellbeing Indicators (Section 2.C) */}
      {step === 3 && (
        <div className="space-y-8 animate-in fade-in duration-300">
          <div className="space-y-8">
            {/* Morale / Mood */}
            <div>
              <RatingSlider
                label="Overall Morale & Mood"
                value={moodScore}
                onChange={setMoodScore}
                min={1}
                max={5}
              />
              <span className="text-xs text-slate-400 block mt-2 px-1">1 = Very Low / Distressed, 5 = Highly Resilient</span>
            </div>

            {/* Burnout Symptoms Frequency */}
            <div className="space-y-4 pt-6 border-t border-[var(--color-glass-border)]">
              <span className="text-sm text-offwhite font-medium block px-1">
                Frequency of Burnout / Overwhelm Symptoms
              </span>
              <div className="grid grid-cols-3 gap-3">
                {(["Rarely", "Sometimes", "Often"] as const).map((b) => (
                  <button
                    key={b}
                    type="button"
                    onClick={() => setBurnoutSymptoms(b)}
                    className={`py-3 px-2 text-sm rounded-2xl border font-semibold transition-all duration-300 ${
                      burnoutSymptoms === b
                        ? "bg-teal-600 text-offwhite border-teal-500 shadow-lg shadow-teal-500/20 transform scale-[1.02]"
                        : "bg-[var(--color-glass-dark)] text-slate-400 border-[var(--color-glass-border)] hover:bg-white/10"
                    }`}
                  >
                    {b}
                  </button>
                ))}
              </div>
            </div>

            {/* Validated Non-Diagnostic Operational Wellbeing Prompts */}
            <div className="space-y-6 pt-6 border-t border-[var(--color-glass-border)]">
              <span className="text-sm font-semibold text-slate-400 block px-1 tracking-wide">
                Operational Screening Check
              </span>

              {/* Prompt 1 */}
              <div className="space-y-3">
                <p className="text-offwhite text-sm px-1">Interest or satisfaction in daily tasks & duty:</p>
                <div className="grid grid-cols-4 gap-2 text-xs font-medium">
                  {["None", "Mild", "Mod", "High"].map((lbl, idx) => (
                    <button
                      key={lbl}
                      type="button"
                      onClick={() => setInterestScore(idx)}
                      className={`py-2.5 rounded-xl border transition-all duration-300 ${
                        interestScore === idx
                          ? "bg-teal-600 text-offwhite border-teal-500 shadow-md"
                          : "bg-[var(--color-glass-dark)] text-slate-400 border-[var(--color-glass-border)] hover:bg-white/10"
                      }`}
                    >
                      {lbl}
                    </button>
                  ))}
                </div>
              </div>

              {/* Prompt 2 */}
              <div className="space-y-3 pt-2">
                <p className="text-offwhite text-sm px-1">Feeling down, discouraged, or mentally exhausted:</p>
                <div className="grid grid-cols-4 gap-2 text-xs font-medium">
                  {["Rarely", "Some", "Often", "Constant"].map((lbl, idx) => (
                    <button
                      key={lbl}
                      type="button"
                      onClick={() => setDiscouragedScore(idx)}
                      className={`py-2.5 rounded-xl border transition-all duration-300 ${
                        discouragedScore === idx
                          ? "bg-teal-600 text-offwhite border-teal-500 shadow-md"
                          : "bg-[var(--color-glass-dark)] text-slate-400 border-[var(--color-glass-border)] hover:bg-white/10"
                      }`}
                    >
                      {lbl}
                    </button>
                  ))}
                </div>
              </div>

              {/* Prompt 3 */}
              <div className="space-y-3 pt-2">
                <p className="text-offwhite text-sm px-1">Trouble concentrating on operational procedures:</p>
                <div className="grid grid-cols-4 gap-2 text-xs font-medium">
                  {["Never", "Rare", "Often", "Severe"].map((lbl, idx) => (
                    <button
                      key={lbl}
                      type="button"
                      onClick={() => setConcentrationScore(idx)}
                      className={`py-2.5 rounded-xl border transition-all duration-300 ${
                        concentrationScore === idx
                          ? "bg-teal-600 text-offwhite border-teal-500 shadow-md"
                          : "bg-[var(--color-glass-dark)] text-slate-400 border-[var(--color-glass-border)] hover:bg-white/10"
                      }`}
                    >
                      {lbl}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="flex gap-3">
            <Button variant="ghost" onClick={() => setStep(2)} className="flex-1 justify-center gap-1">
              <ChevronLeft className="w-4 h-4" /> Back
            </Button>
            <Button
              onClick={handleSubmitAssessment}
              className="flex-1 justify-center gap-1 bg-gradient-to-r from-teal-500 to-emerald-500 text-slate-950 font-bold shadow-lg"
            >
              Submit Assessment ✓
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function AssessmentPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-full items-center justify-center p-6 text-slate-400">
          <div className="w-8 h-8 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
        </div>
      }
    >
      <AssessmentContent />
    </Suspense>
  );
}
