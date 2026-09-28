"use client";

import { HeartPulse, CheckCircle2, AlertTriangle, ShieldAlert, AlertCircle } from 'lucide-react';
import { useState } from 'react';
import { WelfareSupportSheet } from '@/components/screens/WelfareSupportSheet';
import { cn } from '@/lib/utils';
import { submitWelfareRequest } from '@/lib/welfare';
import { useAuth } from '@/lib/AuthContext';

interface FeedbackAlert {
  type: 'success' | 'active' | 'unauthorized' | 'error';
  title: string;
  message: string;
}

export default function SosButton() {
  const { user } = useAuth();
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [sent, setSent] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<FeedbackAlert | null>(null);

  if (!user) {
    return null;
  }

  const handleTrigger = () => {
    if (!sent && !submitting) {
      setConfirmOpen(true);
    }
  };

  const handleSuccess = () => {
    setConfirmOpen(false);
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
  };

  return (
    <>
      <button
        onClick={handleTrigger}
        disabled={submitting}
        className={cn(
          "absolute bottom-20 right-4 z-40 rounded-2xl shadow-[0_8px_20px_rgba(0,168,150,0.3)] transition-all duration-300",
          sent 
            ? "bg-white border-2 border-emerald-500 text-emerald-600 h-14 px-4 flex items-center justify-center gap-2" 
            : "bg-[#00a896] text-white hover:bg-[#00a896]/90 active:scale-95 py-2.5 px-4 flex flex-col items-start"
        )}
        aria-label={sent ? "Request Sent" : "Welfare Support"}
      >
        {sent ? (
          <>
            <CheckCircle2 className="w-5 h-5" />
            <span className="font-bold text-sm mr-1">Alert Sent</span>
          </>
        ) : (
          <div className="flex flex-col items-start leading-tight">
            <div className="flex items-center gap-1.5 mb-0.5">
              <HeartPulse className="w-4 h-4" />
              <span className="font-bold text-[13px] tracking-wide">Welfare</span>
            </div>
            <span className="font-bold text-[13px] tracking-wide ml-[22px]">Support</span>
          </div>
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

      <WelfareSupportSheet
        isOpen={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        onSuccess={handleSuccess}
      />
    </>
  );
}


