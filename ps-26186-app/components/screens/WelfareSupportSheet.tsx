"use client";

import React, { useState } from "react";
import { submitWelfareRequest } from "@/lib/welfare";
import { WelfareRequestOut } from "@/types/api";
import { X, HeartPulse, Send, AlertTriangle, CheckCircle2, ShieldCheck, Info } from "lucide-react";
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
    <div className="absolute inset-0 z-[60] bg-black/40 backdrop-blur-sm flex flex-col justify-end animate-in fade-in duration-200">
      <div className="bg-white rounded-t-[28px] max-h-[90dvh] flex flex-col shadow-[0_-16px_40px_rgba(31,110,140,0.15)] border-t border-white/60 animate-sheet-up">
        <div className="w-10 h-1 bg-ink-3/30 rounded-full mx-auto mt-3 mb-1" />
        
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {/* Header */}
          <div className="flex justify-between items-start border-b border-sky-200/50 pb-3">
            <div className="flex items-center space-x-2">
              <div className="w-10 h-10 rounded-full bg-brand-100 flex items-center justify-center">
                <HeartPulse className="w-5 h-5 text-brand-500" />
              </div>
              <div>
                <h3 className="text-base font-bold text-ink">Request Welfare Support</h3>
                <p className="text-[11px] text-ink-3 font-medium">Voluntary &bull; Non-Punitive Decision Support</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-full text-ink-3 hover:text-ink hover:bg-sky-50 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {error && (
            <div className="p-3 bg-alert-bg border border-alert/30 rounded-2xl text-[13px] text-ink flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-alert shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form id="welfare-form" onSubmit={handleSubmit} className="space-y-4">
            {/* Category */}
            <div className="space-y-1.5">
              <label className="text-[12px] font-semibold text-ink-2 block mb-1.5">Support Category</label>
              <div className="grid grid-cols-1 gap-1.5">
                {CATEGORIES.map((cat) => (
                  <button
                    key={cat}
                    type="button"
                    onClick={() => setCategory(cat)}
                    className={`text-left text-[13px] p-3 rounded-2xl border transition-all h-[52px] flex items-center ${
                      category === cat
                        ? "bg-brand-100 text-brand-600 border-brand-500 font-semibold shadow-sm"
                        : "bg-white border-sky-200 text-ink-2 hover:bg-sky-50"
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            </div>

            {/* Urgency */}
            <div className="space-y-1.5 pt-2 border-t border-sky-200/50">
              <label className="text-[12px] font-semibold text-ink-2 block mb-1.5">Requested Urgency</label>
              <div className="grid grid-cols-3 gap-2">
                {URGENCIES.map((u) => (
                  <button
                    key={u.value}
                    type="button"
                    onClick={() => setUrgency(u.value)}
                    className={`p-3 rounded-2xl border text-center transition-all shadow-sm ${
                      urgency === u.value
                        ? u.value === "Routine"
                          ? "bg-brand-100 text-brand-600 border-brand-500 font-bold"
                          : u.value === "Medium"
                          ? "bg-warn-bg text-warn border-warn font-bold"
                          : "bg-alert-bg text-alert border-alert font-bold"
                        : "bg-white border-sky-200 text-ink-2 hover:bg-sky-50"
                    }`}
                  >
                    <span className="text-[13px] block">{u.label}</span>
                    <span className="text-[10px] font-normal block mt-0.5 opacity-80">{u.desc}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Optional Message */}
            <div className="space-y-1.5 pt-2 border-t border-sky-200/50">
              <div className="flex justify-between items-center">
                <label className="text-[12px] font-semibold text-ink-2">Brief Note / Context (Optional)</label>
                <span className="text-[11px] text-ink-3">Max 1000 chars</span>
              </div>
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                maxLength={1000}
                rows={3}
                placeholder="E.g., I would like to consult regarding consecutive night shifts or request leave pacing..."
                className="w-full bg-white border border-sky-200 rounded-2xl p-4 text-[13px] text-ink placeholder:text-ink-3 focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100 transition"
              />
            </div>

            {/* Disclaimer */}
            <div className="text-[11px] text-ink-3 italic leading-relaxed p-3 bg-brand-100/50 rounded-xl flex items-start gap-2">
              <Info className="w-4 h-4 text-brand-500 shrink-0 mt-0.5" />
              <p>This request will appear in your battalion Commander & Welfare Officer dashboard for supportive review. It is not disciplinary.</p>
            </div>
          </form>
        </div>

        <div className="sticky bottom-0 bg-white/95 backdrop-blur-sm border-t border-sky-200/50 p-4" style={{paddingBottom: 'calc(1rem + env(safe-area-inset-bottom, 0px))'}}>
          <div className="flex gap-2.5">
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
              form="welfare-form"
              disabled={submitting}
              className="flex-1 justify-center gap-1.5"
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
        </div>
      </div>
    </div>
  );
}


