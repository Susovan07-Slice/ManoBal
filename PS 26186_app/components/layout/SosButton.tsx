"use client";

import { LifeBuoy, CheckCircle2 } from 'lucide-react';
import { useState } from 'react';
import { ConfirmSheet } from '@/components/ui/ConfirmSheet';
import { cn } from '@/lib/utils';

export default function SosButton() {
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [sent, setSent] = useState(false);

  const handleTrigger = () => {
    if (!sent) {
      setConfirmOpen(true);
    }
  };

  const handleConfirm = () => {
    setConfirmOpen(false);
    setSent(true);
    
    // UI SIMULATION ONLY: Not wired to a real alerting backend yet.
    console.log("[DEV SIMULATION] Welfare officer notified.");
    
    // Auto-reset after 5 seconds for demonstration purposes
    setTimeout(() => {
      setSent(false);
    }, 5000);
  };

  return (
    <>
      <button
        onClick={handleTrigger}
        className={cn(
          "absolute bottom-20 right-4 z-40 h-14 rounded-full shadow-lg flex items-center justify-center transition-all duration-300",
          sent 
            ? "bg-[#1C2530] border-2 border-teal-500 text-teal-400 w-auto px-4 gap-2" 
            : "bg-red-600/90 text-white hover:bg-red-500 w-14"
        )}
        aria-label={sent ? "SOS Sent" : "SOS"}
      >
        {sent ? (
          <>
            <CheckCircle2 className="w-5 h-5" />
            <span className="font-medium text-sm mr-1">Notified</span>
          </>
        ) : (
          <LifeBuoy className="w-7 h-7" />
        )}
      </button>

      {/* Visible DEV note if sent */}
      {sent && (
        <div className="absolute top-24 left-4 right-4 z-40 bg-yellow-500/10 border border-yellow-500/50 text-yellow-200 text-xs p-3 rounded-lg text-center backdrop-blur-md animate-in slide-in-from-top-4">
          DEV SIMULATION: No real alert was sent. Backend not wired.
        </div>
      )}

      <ConfirmSheet
        open={confirmOpen}
        title="Emergency Request"
        message="Are you sure you want to notify the Welfare Officer? They will be alerted immediately."
        confirmLabel="Yes, Notify"
        cancelLabel="Cancel"
        isDanger={true}
        onConfirm={handleConfirm}
        onCancel={() => setConfirmOpen(false)}
      />
    </>
  );
}
