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
          "absolute right-4 z-40 transition-all duration-300",
          sent 
            ? "bg-white border-2 border-ok text-ok rounded-full h-12 px-4 flex items-center justify-center gap-2 shadow-[0_16px_40px_rgba(31,110,140,0.22)]" 
            : "rounded-full px-4 py-2.5 bg-gradient-to-r from-brand-500 to-[#1E8FC0] text-white shadow-[0_16px_40px_rgba(31,110,140,0.22)] animate-pulse-ring flex items-center gap-1.5"
        )}
        style={{ bottom: "calc(96px + env(safe-area-inset-bottom, 0px))" }}
        aria-label={sent ? "Request Sent" : "Welfare Support"}
      >
        {sent ? (
          <>
            <CheckCircle2 className="w-5 h-5" />
            <span className="font-bold text-sm mr-1">Alert Sent</span>
          </>
        ) : (
          <>
            <HeartPulse className="w-4 h-4" />
            <span className="font-bold text-[13px] tracking-wide whitespace-nowrap">Welfare Support</span>
          </>
        )}
      </button>

      {/* Confirmed Alert Notification Banner */}
      {feedback && (
        <div
          role="alert"
          className={cn(
            "absolute top-24 left-4 right-4 z-40 p-3 rounded-lg text-center backdrop-blur-md animate-in slide-in-from-top-4 shadow-[0_8px_30px_rgba(0,0,0,0.12)] border",
            feedback.type === 'success' && "bg-ok-bg border-ok/40 text-ink",
            feedback.type === 'active' && "bg-warn-bg border-warn/40 text-ink",
            feedback.type === 'unauthorized' && "bg-alert-bg border-alert/40 text-ink",
            feedback.type === 'error' && "bg-red-50 border-danger/40 text-ink"
          )}
        >
          <div className="flex items-center justify-center gap-1.5 font-bold text-xs">
            {feedback.type === 'success' && <CheckCircle2 className="w-4 h-4 text-ok shrink-0" />}
            {feedback.type === 'active' && <AlertTriangle className="w-4 h-4 text-warn shrink-0" />}
            {feedback.type === 'unauthorized' && <ShieldAlert className="w-4 h-4 text-alert shrink-0" />}
            {feedback.type === 'error' && <AlertCircle className="w-4 h-4 text-danger shrink-0" />}
            <span
              className={cn(
                feedback.type === 'success' && "text-ok",
                feedback.type === 'active' && "text-warn",
                feedback.type === 'unauthorized' && "text-alert",
                feedback.type === 'error' && "text-danger"
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
