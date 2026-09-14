"use client";

import { useEffect, useState } from "react";
import { SurveyCard } from "@/components/screens/SurveyCard";
import { getSurveyQuestions } from "@/lib/mock-data";
import { SurveyQuestion } from "@/types/survey";

export default function AssessmentPage() {
  const [questions, setQuestions] = useState<SurveyQuestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [completed, setCompleted] = useState(false);

  useEffect(() => {
    getSurveyQuestions().then((data) => {
      setQuestions(data);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center text-slate-400">
        <div className="w-6 h-6 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (completed) {
    return (
      <div className="flex flex-col h-full items-center justify-center text-slate-400 p-6 text-center animate-in fade-in duration-500">
        <div className="w-16 h-16 bg-teal-500/20 text-teal-400 rounded-full flex items-center justify-center mb-6">
          <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <p className="text-xl text-slate-200 font-medium mb-2">Assessment Complete</p>
        <p className="text-sm">Your responses have been recorded.</p>
      </div>
    );
  }

  return (
    <div className="p-4 flex flex-col h-full">
      <SurveyCard
        questions={questions}
        onComplete={(answers) => {
          console.log("Survey completed:", answers);
          setCompleted(true);
        }}
      />
    </div>
  );
}
