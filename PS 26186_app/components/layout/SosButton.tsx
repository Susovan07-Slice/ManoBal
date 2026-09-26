"use client";

import { LifeBuoy, CheckCircle2, AlertTriangle, ShieldAlert, AlertCircle } from 'lucide-react';
import { useState } from 'react';
import { ConfirmSheet } from '@/components/ui/ConfirmSheet';
import { cn } from '@/lib/utils';
import { submitWelfareRequest } from '@/lib/welfare';

interface FeedbackAlert {
  type: 'success' | 'active' | 'unauthorized' | 'error';
  title: string;
  message: string;
}

export default function SosButton() {
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [sent, setSent] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<FeedbackAlert | null>(null);

  const handleTrigger = () => {
    if (!sent && !submitting) {
      setConfirmOpen(true);
    }
  };

  const handleConfirm = async () => {
    setConfirmOpen(false);
    setSubmitting(true);
    try {
      await submitWelfareRequest({
        category: "Emergency SOS Support",
        urgency: "High",
        message: "Urgent welfare assistance requested via mobile SOS button.",
      });
      setSent(true);
      setFeedback({
        type: 'success',
        title: 'Welfare Request Sent',
        message: 'Welfare request sent successfully. Transmitted to Commander portal.',
      });
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('manobal:welfare_created'));
      }
      setTimeout(() => {
        setSent(false);
        setFeedback(null);
      }, 5000);
    } catch (err: any) {
      console.error("SOS submission failed:", err);
      setSent(false);
      const status = err?.status;
      if (status === 409) {
        setFeedback({
          type: 'active',
          title: 'Request Already Active',
          message: 'You already have an active welfare request.',
        });
      } else if (status === 401 || status === 403) {
        setFeedback({
          type: 'unauthorized',
          title: 'Authorization Required',
          message: 'You are not authorized to submit this request.',
        });
      } else {
        setFeedback({
          type: 'error',
          title: 'Backend Failure',
          message: 'Unable to send welfare request. Please try again.',
        });
      }
      setTimeout(() => {
        setFeedback(null);
      }, 5000);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <button
        onClick={handleTrigger}
        disabled={submitting}
        className={cn(
          "absolute bottom-20 right-4 z-40 h-14 rounded-full shadow-lg flex items-center justify-center transition-all duration-300",
          sent 
            ? "bg-[#1C2530] border-2 border-mb-accent text-mb-accent w-auto px-4 gap-2" 
            : "bg-red-600/90 text-mb-text-primary hover:bg-red-500 w-14 active:scale-95"
        )}
        aria-label={sent ? "SOS Sent" : "SOS"}
      >
        {sent ? (
          <>
            <CheckCircle2 className="w-5 h-5 text-mb-accent" />
            <span className="font-medium text-sm mr-1 text-teal-300">Alert Sent</span>
          </>
        ) : (
          <LifeBuoy className="w-7 h-7" />
        )}
      </button>

      {/* Confirmed Alert Notification Banner */}
      {feedback && (
        <div
          role="alert"
          className={cn(
            "absolute top-24 left-4 right-4 z-40 p-3 rounded-lg text-center backdrop-blur-md animate-in slide-in-from-top-4 shadow-[0_8px_30px_rgba(0,0,0,0.12)] border",
            feedback.type === 'success' && "bg-emerald-500/20 border-emerald-500/60 text-emerald-200",
            feedback.type === 'active' && "bg-amber-500/20 border-amber-500/60 text-amber-200",
            feedback.type === 'unauthorized' && "bg-rose-500/20 border-rose-500/60 text-rose-200",
            feedback.type === 'error' && "bg-red-500/20 border-red-500/60 text-red-200"
          )}
        >
          <div className="flex items-center justify-center gap-1.5 font-bold text-xs">
            {feedback.type === 'success' && <CheckCircle2 className="w-4 h-4 text-mb-green shrink-0" />}
            {feedback.type === 'active' && <AlertTriangle className="w-4 h-4 text-mb-saffron shrink-0" />}
            {feedback.type === 'unauthorized' && <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0" />}
            {feedback.type === 'error' && <AlertCircle className="w-4 h-4 text-mb-danger shrink-0" />}
            <span
              className={cn(
                feedback.type === 'success' && "text-mb-text-primary",
                feedback.type === 'active' && "text-amber-300",
                feedback.type === 'unauthorized' && "text-rose-300",
                feedback.type === 'error' && "text-red-300"
              )}
            >
              {feedback.title}
            </span>
          </div>
          <p className="text-[11px] mt-0.5 opacity-90">
            {feedback.message}
          </p>
        </div>
      )}

      <ConfirmSheet
        open={confirmOpen}
        title="Emergency Welfare Request"
        message="Are you sure you want to notify the Welfare Officer? An urgent welfare flag will be transmitted to the command dashboard."
        confirmLabel="Yes, Notify Officer"
        cancelLabel="Cancel"
        isDanger={true}
        onConfirm={handleConfirm}
        onCancel={() => setConfirmOpen(false)}
      />
    </>
  );
}


