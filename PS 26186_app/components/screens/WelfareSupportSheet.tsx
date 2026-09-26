"use client";

import React, { useState } from "react";
import { submitWelfareRequest } from "@/lib/welfare";
import { WelfareRequestOut } from "@/types/api";
import { X, HeartPulse, Send, AlertTriangle, CheckCircle2, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface WelfareSupportSheetProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (newReq: WelfareRequestOut) => void;
}

const CATEGORIES = [
  "Duty Schedule & Workload",
  "Rest & Sleep Fatigue",
  "Personal & Family Matters",
  "Operational Stress & Morale",
  "General Welfare Consultation",
];

const URGENCIES = [
  { value: "Routine", label: "Routine", desc: "Standard unit review" },
  { value: "Medium", label: "Medium", desc: "Review within 24-48 hours" },
  { value: "High", label: "High", desc: "Priority welfare review" },
] as const;

export function WelfareSupportSheet({
  isOpen,
  onClose,
  onSuccess,
}: WelfareSupportSheetProps) {
  const [category, setCategory] = useState<string>(CATEGORIES[0]);
  const [urgency, setUrgency] = useState<"Routine" | "Medium" | "High">("Routine");
  const [message, setMessage] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const created = await submitWelfareRequest({
        category,
        urgency,
        message: message.trim() || undefined,
      });
      onSuccess(created);
      onClose();
    } catch (err: any) {
      console.error("Welfare request failed:", err);
      setError(err?.message || "Failed to submit request to server.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="absolute inset-0 z-50 bg-black/70 backdrop-blur-sm flex flex-col justify-end animate-in fade-in duration-200">
      <div className="bg-[#1C2530] border-t border-slate-700/80 rounded-t-2xl max-h-[90%] overflow-y-auto p-5 space-y-4 shadow-2xl animate-in slide-in-from-bottom duration-300">
        {/* Header */}
        <div className="flex justify-between items-start border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <HeartPulse className="w-5 h-5 text-teal-400" />
            <div>
              <h3 className="text-base font-bold text-slate-100">Request Welfare Support</h3>
              <p className="text-[11px] text-slate-400 font-mono">Voluntary • Non-Punitive Decision Support</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="p-3 bg-red-950/60 border border-red-800 rounded-xl text-xs text-red-200 flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Category */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 block">Support Category</label>
            <div className="grid grid-cols-1 gap-1.5">
              {CATEGORIES.map((cat) => (
                <button
                  key={cat}
                  type="button"
                  onClick={() => setCategory(cat)}
                  className={`text-left text-xs p-2.5 rounded-xl border transition-colors ${
                    category === cat
                      ? "bg-teal-500/20 text-teal-300 border-teal-500/60 font-semibold"
                      : "bg-slate-900/60 text-slate-400 border-slate-800 hover:bg-slate-800"
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          {/* Urgency */}
          <div className="space-y-1.5 pt-2 border-t border-slate-800">
            <label className="text-xs font-semibold text-slate-300 block">Requested Urgency</label>
            <div className="grid grid-cols-3 gap-2">
              {URGENCIES.map((u) => (
                <button
                  key={u.value}
                  type="button"
                  onClick={() => setUrgency(u.value)}
                  className={`p-2 rounded-xl border text-center transition-colors ${
                    urgency === u.value
                      ? u.value === "High"
                        ? "bg-rose-500/20 text-rose-300 border-rose-500 font-bold"
                        : "bg-teal-500 text-slate-950 border-teal-500 font-bold"
                      : "bg-slate-900/60 text-slate-400 border-slate-800 hover:bg-slate-800 text-xs"
                  }`}
                >
                  <span className="text-xs block">{u.label}</span>
                  <span className="text-[9px] text-slate-400 font-normal block mt-0.5">{u.desc}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Optional Message */}
          <div className="space-y-1.5 pt-2 border-t border-slate-800">
            <div className="flex justify-between items-center text-xs">
              <label className="font-semibold text-slate-300">Brief Note / Context (Optional)</label>
              <span className="text-[10px] text-slate-500">Max 1000 chars</span>
            </div>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              maxLength={1000}
              rows={3}
              placeholder="E.g., I would like to consult regarding consecutive night shifts or request leave pacing..."
              className="w-full bg-slate-900/80 border border-slate-800 rounded-xl p-3 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-teal-500 transition"
            />
          </div>

          {/* Disclaimer */}
          <p className="text-[10px] text-slate-400 italic leading-relaxed">
            This request will appear in your battalion Commander & Welfare Officer dashboard for supportive review. It is not disciplinary.
          </p>

          {/* Buttons */}
          <div className="flex gap-2.5 pt-1 pb-2">
            <Button
              type="button"
              variant="ghost"
              onClick={onClose}
              disabled={submitting}
              className="flex-1 justify-center"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={submitting}
              className="flex-1 justify-center gap-1.5 bg-gradient-to-r from-teal-500 to-emerald-500 text-slate-950 font-bold shadow-md"
            >
              {submitting ? (
                <span>Submitting...</span>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>Submit Request</span>
                </>
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
