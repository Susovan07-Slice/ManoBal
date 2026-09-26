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
        <div className="p-5 bg-[#1C2530] border border-slate-700/80 rounded-xl space-y-4 shadow-lg">
          <div className="flex justify-between items-start">
            <div>
              <span className="text-[10px] uppercase font-mono tracking-widest text-slate-400 block">
                Classified Stress Level
              </span>
              <span
                className={`text-2xl font-extrabold ${
                  assessmentResult.stress_level === "High"
                    ? "text-rose-400"
                    : assessmentResult.stress_level === "Medium"
                    ? "text-amber-400"
                    : "text-emerald-400"
                }`}
              >
                {assessmentResult.stress_level} Stress
              </span>
            </div>

            <div className="text-right">
              <span className="text-[10px] uppercase font-mono tracking-widest text-slate-400 block">
                Continuous Risk Score
              </span>
              <span className="text-3xl font-black font-mono text-slate-100">
                {typeof assessmentResult.risk_score === 'number'
                  ? assessmentResult.risk_score.toFixed(1)
                  : assessmentResult.risk_score}
                <span className="text-xs text-slate-400 font-normal"> / 100</span>
              </span>
            </div>
          </div>

          <div className="p-2.5 bg-slate-900/60 rounded-lg flex items-center justify-between text-xs">
            <span className="text-slate-400">Operational Priority:</span>
            <span
              className={`font-mono font-bold uppercase px-2.5 py-0.5 rounded text-xs ${
                assessmentResult.risk_priority === "Priority"
                  ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                  : assessmentResult.risk_priority === "Preventive"
                  ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                  : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
              }`}
            >
              {assessmentResult.risk_priority}
            </span>
          </div>

          {/* Model Confidence & Longitudinal Trend */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="p-2 bg-slate-900/60 rounded-lg flex items-center justify-between">
              <span className="text-slate-400">Confidence:</span>
              <span className="font-mono font-semibold text-slate-200">
                {assessmentResult.confidence || "High"}
              </span>
            </div>
            <div className="p-2 bg-slate-900/60 rounded-lg flex items-center justify-between">
              <span className="text-slate-400">Trend:</span>
              <span className={`font-mono font-semibold ${
                assessmentResult.risk_trend === 'Worsening'
                  ? 'text-rose-400'
                  : assessmentResult.risk_trend === 'Improving'
                  ? 'text-emerald-400'
                  : 'text-slate-200'
              }`}>
                {assessmentResult.risk_trend || "Stable"}
              </span>
            </div>
          </div>


          {/* Model Class Probabilities */}
          <div className="pt-2 border-t border-slate-700/60 space-y-1.5">
            <span className="text-[11px] uppercase font-semibold text-slate-400 tracking-wider block">
              Class Probability Distribution:
            </span>
            <div className="grid grid-cols-3 gap-2 text-center text-xs font-mono">
              <div className="p-2 bg-slate-900/40 rounded border border-slate-800">
                <span className="text-[10px] text-slate-400 block">Low</span>
                <span className="text-emerald-400 font-bold">
                  {(assessmentResult.low_probability * 100).toFixed(0)}%
                </span>
              </div>
              <div className="p-2 bg-slate-900/40 rounded border border-slate-800">
                <span className="text-[10px] text-slate-400 block">Medium</span>
                <span className="text-amber-400 font-bold">
                  {(assessmentResult.medium_probability * 100).toFixed(0)}%
                </span>
              </div>
              <div className="p-2 bg-slate-900/40 rounded border border-slate-800">
                <span className="text-[10px] text-slate-400 block">High</span>
                <span className="text-rose-400 font-bold">
                  {(assessmentResult.high_probability * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>

          {/* Key Contributing Model Factors */}
          {assessmentResult.key_factors && assessmentResult.key_factors.length > 0 && (
            <div className="pt-2 border-t border-slate-700/60 space-y-1.5">
              <span className="text-[11px] uppercase font-semibold text-slate-400 tracking-wider block">
                Primary Associated Factors:
              </span>
              <ul className="space-y-1.5">
                {assessmentResult.key_factors.map((factor, i) => (
                  <li
                    key={i}
                    className="text-xs text-slate-300 bg-slate-900/40 p-2 rounded border-l-2 border-teal-500 flex items-start space-x-1.5"
                  >
                    <span className="text-teal-400 font-bold">•</span>
                    <span>{factor}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

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
        </div>

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
      <div className="flex items-center justify-between mb-5 bg-[#1C2530] p-2 rounded-xl border border-slate-800 text-xs font-medium">
        <button
          onClick={() => setStep(1)}
          className={`flex-1 py-1.5 rounded-lg text-center transition-colors ${
            step === 1 ? "bg-teal-500 text-slate-950 font-bold" : "text-slate-400 hover:text-slate-200"
          }`}
        >
          1. Duty & Ops
        </button>
        <button
          onClick={() => setStep(2)}
          className={`flex-1 py-1.5 rounded-lg text-center transition-colors ${
            step === 2 ? "bg-teal-500 text-slate-950 font-bold" : "text-slate-400 hover:text-slate-200"
          }`}
        >
          2. Recovery
        </button>
        <button
          onClick={() => setStep(3)}
          className={`flex-1 py-1.5 rounded-lg text-center transition-colors ${
            step === 3 ? "bg-teal-500 text-slate-950 font-bold" : "text-slate-400 hover:text-slate-200"
          }`}
        >
          3. Wellbeing
        </button>
      </div>

      {/* STEP 1: Daily Duty / Operational Information (Section 2.A) */}
      {step === 1 && (
        <div className="space-y-4 animate-in fade-in duration-300">
          <Card className="p-4 space-y-4 bg-[#1C2530] border-slate-700/80">
            <h3 className="text-xs uppercase font-mono tracking-wider text-teal-400 font-bold">
              Section A: Operational Duty Telemetry
            </h3>

            {/* Duty Hours */}
            <div className="space-y-1.5">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-200 font-medium">Weekly Duty Hours</span>
                <span className="font-mono font-bold text-teal-400 text-sm">{dutyHours} hrs/week</span>
              </div>
              <input
                type="range"
                min={20}
                max={90}
                step={2}
                value={dutyHours}
                onChange={(e) => setDutyHours(parseInt(e.target.value))}
                className="w-full h-2.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-teal-500"
              />
              <span className="text-[10px] text-slate-400 block">Standard military pacing ~44-52 hrs</span>
            </div>

            {/* Consecutive Duty Days */}
            <div className="space-y-1.5 pt-2 border-t border-slate-800">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-200 font-medium">Consecutive Duty Days</span>
                <span className="font-mono font-bold text-teal-400 text-sm">{consecDays} days continuous</span>
              </div>
              <input
                type="range"
                min={0}
                max={30}
                step={1}
                value={consecDays}
                onChange={(e) => setConsecDays(parseInt(e.target.value))}
                className="w-full h-2.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-teal-500"
              />
              <span className="text-[10px] text-slate-400 block">Consecutive days on duty without 24h rest</span>
            </div>

            {/* Night Shifts */}
            <div className="space-y-1.5 pt-2 border-t border-slate-800">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-200 font-medium">Night Shifts Assigned (Last 30 Days)</span>
                <span className="font-mono font-bold text-teal-400 text-sm">{nightShifts} shifts</span>
              </div>
              <input
                type="range"
                min={0}
                max={20}
                step={1}
                value={nightShifts}
                onChange={(e) => setNightShifts(parseInt(e.target.value))}
                className="w-full h-2.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-teal-500"
              />
            </div>

            {/* Operational Exposure Level */}
            <div className="space-y-2 pt-2 border-t border-slate-800">
              <span className="text-xs text-slate-200 font-medium block">Operational Exposure Level</span>
              <div className="grid grid-cols-3 gap-2">
                {(["Low", "Medium", "High"] as const).map((lvl) => (
                  <button
                    key={lvl}
                    type="button"
                    onClick={() => setOpExposure(lvl)}
                    className={`py-2 px-1 text-xs rounded-xl border font-semibold transition-colors ${
                      opExposure === lvl
                        ? "bg-teal-500 text-slate-950 border-teal-500"
                        : "bg-slate-900/60 text-slate-400 border-slate-700 hover:bg-slate-800"
                    }`}
                  >
                    {lvl}
                  </button>
                ))}
              </div>
            </div>
          </Card>

          <Button onClick={() => setStep(2)} className="w-full justify-center gap-2">
            Next: Recovery & Rest <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      )}

      {/* STEP 2: Personal Welfare / Recovery (Section 2.B) */}
      {step === 2 && (
        <div className="space-y-4 animate-in fade-in duration-300">
          <Card className="p-4 space-y-4 bg-[#1C2530] border-slate-700/80">
            <h3 className="text-xs uppercase font-mono tracking-wider text-teal-400 font-bold">
              Section B: Personal Rest & Recovery
            </h3>

            {/* Sleep Hours */}
            <div className="space-y-1.5">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-200 font-medium">Restorative Sleep Hours</span>
                <span className="font-mono font-bold text-teal-400 text-sm">{sleepHours} hrs</span>
              </div>
              <input
                type="range"
                min={2.0}
                max={12.0}
                step={0.5}
                value={sleepHours}
                onChange={(e) => setSleepHours(parseFloat(e.target.value))}
                className="w-full h-2.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-teal-500"
              />
              <span className="text-[10px] text-slate-400 block">Average restorative sleep duration per 24h</span>
            </div>

            {/* Physical Fatigue */}
            <div className="pt-2 border-t border-slate-800">
              <RatingSlider
                label="Physical Fatigue Level"
                value={physicalFatigue}
                onChange={setPhysicalFatigue}
                min={1}
                max={5}
              />
              <span className="text-[10px] text-slate-400 block mt-1">1 = Fully refreshed, 5 = Severe bodily fatigue</span>
            </div>

            {/* Physical Activity / PT */}
            <div className="space-y-1.5 pt-2 border-t border-slate-800">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-200 font-medium">Physical Conditioning / PT</span>
                <span className="font-mono font-bold text-teal-400 text-sm">{physicalActivity} hrs/week</span>
              </div>
              <input
                type="range"
                min={0}
                max={25}
                step={1}
                value={physicalActivity}
                onChange={(e) => setPhysicalActivity(parseInt(e.target.value))}
                className="w-full h-2.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-teal-500"
              />
            </div>
          </Card>

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
        <div className="space-y-4 animate-in fade-in duration-300">
          <Card className="p-4 space-y-4 bg-[#1C2530] border-slate-700/80">
            <h3 className="text-xs uppercase font-mono tracking-wider text-teal-400 font-bold">
              Section C: Operational Wellbeing & Morale
            </h3>

            {/* Morale / Mood */}
            <div>
              <RatingSlider
                label="Overall Morale & Mood"
                value={moodScore}
                onChange={setMoodScore}
                min={1}
                max={5}
              />
              <span className="text-[10px] text-slate-400 block mt-1">1 = Very Low / Distressed, 5 = Highly Resilient</span>
            </div>

            {/* Burnout Symptoms Frequency */}
            <div className="space-y-2 pt-2 border-t border-slate-800">
              <span className="text-xs text-slate-200 font-medium block">
                Frequency of Burnout / Overwhelm Symptoms
              </span>
              <div className="grid grid-cols-3 gap-2">
                {(["Rarely", "Sometimes", "Often"] as const).map((b) => (
                  <button
                    key={b}
                    type="button"
                    onClick={() => setBurnoutSymptoms(b)}
                    className={`py-2 px-1 text-xs rounded-xl border font-semibold transition-colors ${
                      burnoutSymptoms === b
                        ? "bg-teal-500 text-slate-950 border-teal-500"
                        : "bg-slate-900/60 text-slate-400 border-slate-700 hover:bg-slate-800"
                    }`}
                  >
                    {b}
                  </button>
                ))}
              </div>
            </div>

            {/* Validated Non-Diagnostic Operational Wellbeing Prompts */}
            <div className="space-y-3 pt-2 border-t border-slate-800 text-xs">
              <span className="text-[11px] font-semibold text-slate-300 block">
                Operational Screening Check (Last 2 Weeks):
              </span>

              {/* Prompt 1 */}
              <div className="p-2.5 bg-slate-900/50 rounded-lg space-y-1.5 border border-slate-800">
                <p className="text-slate-300 text-xs">Interest or satisfaction in daily tasks & duty:</p>
                <div className="grid grid-cols-4 gap-1 text-[10px] font-mono">
                  {["None", "Mild", "Mod", "High"].map((lbl, idx) => (
                    <button
                      key={lbl}
                      type="button"
                      onClick={() => setInterestScore(idx)}
                      className={`py-1 rounded border text-center ${
                        interestScore === idx
                          ? "bg-teal-500 text-slate-950 font-bold border-teal-500"
                          : "bg-slate-800 text-slate-400 border-slate-700"
                      }`}
                    >
                      {lbl}
                    </button>
                  ))}
                </div>
              </div>

              {/* Prompt 2 */}
              <div className="p-2.5 bg-slate-900/50 rounded-lg space-y-1.5 border border-slate-800">
                <p className="text-slate-300 text-xs">Feeling down, discouraged, or mentally exhausted:</p>
                <div className="grid grid-cols-4 gap-1 text-[10px] font-mono">
                  {["Rarely", "Some", "Often", "Constant"].map((lbl, idx) => (
                    <button
                      key={lbl}
                      type="button"
                      onClick={() => setDiscouragedScore(idx)}
                      className={`py-1 rounded border text-center ${
                        discouragedScore === idx
                          ? "bg-teal-500 text-slate-950 font-bold border-teal-500"
                          : "bg-slate-800 text-slate-400 border-slate-700"
                      }`}
                    >
                      {lbl}
                    </button>
                  ))}
                </div>
              </div>

              {/* Prompt 3 */}
              <div className="p-2.5 bg-slate-900/50 rounded-lg space-y-1.5 border border-slate-800">
                <p className="text-slate-300 text-xs">Trouble concentrating on operational procedures:</p>
                <div className="grid grid-cols-4 gap-1 text-[10px] font-mono">
                  {["Never", "Rare", "Often", "Severe"].map((lbl, idx) => (
                    <button
                      key={lbl}
                      type="button"
                      onClick={() => setConcentrationScore(idx)}
                      className={`py-1 rounded border text-center ${
                        concentrationScore === idx
                          ? "bg-teal-500 text-slate-950 font-bold border-teal-500"
                          : "bg-slate-800 text-slate-400 border-slate-700"
                      }`}
                    >
                      {lbl}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </Card>

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
