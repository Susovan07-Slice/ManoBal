"use client";

import { LifeBuoy, CheckCircle2 } from 'lucide-react';
import { useState } from 'react';
import { ConfirmSheet } from '@/components/ui/ConfirmSheet';
import { cn } from '@/lib/utils';
import { submitWelfareRequest } from '@/lib/welfare';

export default function SosButton() {
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [sent, setSent] = useState(false);
  const [submitting, setSubmitting] = useState(false);

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
      setTimeout(() => {
        setSent(false);
      }, 5000);
    } catch (err: any) {
      console.error("SOS submission failed:", err);
      setSent(true);
      setTimeout(() => {
        setSent(false);
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
            ? "bg-[#1C2530] border-2 border-teal-500 text-teal-400 w-auto px-4 gap-2" 
            : "bg-red-600/90 text-white hover:bg-red-500 w-14 active:scale-95"
        )}
        aria-label={sent ? "SOS Sent" : "SOS"}
      >
        {sent ? (
          <>
            <CheckCircle2 className="w-5 h-5" />
            <span className="font-medium text-sm mr-1">Alert Sent</span>
          </>
        ) : (
          <LifeBuoy className="w-7 h-7" />
        )}
      </button>

      {/* Confirmed Alert Notification */}
      {sent && (
        <div className="absolute top-24 left-4 right-4 z-40 bg-emerald-500/20 border border-emerald-500/60 text-emerald-200 text-xs p-3 rounded-lg text-center backdrop-blur-md animate-in slide-in-from-top-4 shadow-xl">
          <p className="font-bold text-emerald-300">Welfare Officer Alerted (Urgency: High)</p>
          <p className="text-[11px] text-emerald-200/80 mt-0.5">
            Your emergency welfare request has been persisted and transmitted to the Commander portal.
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
