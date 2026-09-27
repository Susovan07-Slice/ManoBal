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
    <div className="absolute inset-0 z-[60] bg-black/60 backdrop-blur-sm flex flex-col justify-end animate-in fade-in duration-200">
      <div className="bg-white/95 backdrop-blur-2xl border-t border-white/60 rounded-t-3xl max-h-[90%] overflow-y-auto p-5 space-y-4 shadow-[0_-8px_30px_rgba(0,0,0,0.12)] animate-in slide-in-from-bottom duration-300">
        {/* Header */}
        <div className="flex justify-between items-start border-b border-gray-200 pb-3">
          <div className="flex items-center space-x-2">
            <HeartPulse className="w-5 h-5 text-mb-accent" />
            <div>
              <h3 className="text-base font-bold text-gray-800">Request Welfare Support</h3>
              <p className="text-[11px] text-gray-500 font-mono">Voluntary &bull; Non-Punitive Decision Support</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="p-3 bg-red-950/60 border border-red-800 rounded-xl text-xs text-red-200 flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-mb-danger shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Category */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-gray-500 block">Support Category</label>
            <div className="grid grid-cols-1 gap-1.5">
              {CATEGORIES.map((cat) => (
                <button
                  key={cat}
                  type="button"
                  onClick={() => setCategory(cat)}
                  className={`text-left text-xs p-2.5 rounded-xl border transition-colors ${
                    category === cat
                      ? "bg-teal-50 text-teal-700 border-teal-300 font-bold shadow-sm"
                      : "bg-white border-gray-200 text-gray-600 hover:bg-gray-50 hover:text-gray-800"
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          {/* Urgency */}
          <div className="space-y-1.5 pt-2 border-t border-gray-200">
            <label className="text-xs font-semibold text-gray-500 block">Requested Urgency</label>
            <div className="grid grid-cols-3 gap-2">
              {URGENCIES.map((u) => (
                <button
                  key={u.value}
                  type="button"
                  onClick={() => setUrgency(u.value)}
                  className={`p-2 rounded-xl border text-center transition-colors shadow-sm ${
                    urgency === u.value
                      ? u.value === "High"
                        ? "bg-rose-50 text-rose-700 border-rose-300 font-bold"
                        : "bg-teal-50 text-teal-700 border-teal-300 font-bold"
                      : "bg-white border-gray-200 text-gray-600 hover:bg-gray-50 hover:text-gray-800 text-xs"
                  }`}
                >
                  <span className="text-xs block">{u.label}</span>
                  <span className="text-[9px] font-normal block mt-0.5 opacity-80">{u.desc}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Optional Message */}
          <div className="space-y-1.5 pt-2 border-t border-gray-200">
            <div className="flex justify-between items-center text-xs">
              <label className="font-semibold text-gray-500">Brief Note / Context (Optional)</label>
              <span className="text-[10px] text-gray-400">Max 1000 chars</span>
            </div>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              maxLength={1000}
              rows={3}
              placeholder="E.g., I would like to consult regarding consecutive night shifts or request leave pacing..."
              className="w-full bg-white border border-gray-200 rounded-xl p-3 text-xs text-gray-800 placeholder:text-gray-400 focus:outline-none focus:border-mb-accent focus:ring-1 focus:ring-mb-accent transition"
            />
          </div>

          {/* Disclaimer */}
          <p className="text-[10px] text-gray-500 italic leading-relaxed">
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
              className="flex-1 justify-center gap-1.5 bg-gradient-to-r from-mb-accent to-mb-accent text-mb-text-dark font-bold shadow-md"
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


