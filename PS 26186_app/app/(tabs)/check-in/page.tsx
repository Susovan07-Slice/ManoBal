"use client";

import { CheckInForm } from "@/components/screens/CheckInForm";
import { useState } from "react";

export default function CheckInPage() {
  const [submitted, setSubmitted] = useState(false);

  if (submitted) {
    return (
      <div className="flex flex-col h-full items-center justify-center text-slate-400 p-6 text-center animate-in fade-in duration-500">
        <div className="w-16 h-16 bg-teal-500/20 text-teal-400 rounded-full flex items-center justify-center mb-6">
          <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <p className="text-xl text-slate-200 font-medium mb-2">Check-In Complete</p>
        <p className="text-sm">Thank you for logging your daily status.</p>
      </div>
    );
  }

  return (
    <div className="p-4 flex flex-col h-full">
      <h2 className="text-xl font-semibold mb-6 text-slate-100">Daily Status</h2>
      <CheckInForm onSubmit={(data) => {
        console.log("Check-in submitted:", data);
        setSubmitted(true);
      }} />
    </div>
  );
}
