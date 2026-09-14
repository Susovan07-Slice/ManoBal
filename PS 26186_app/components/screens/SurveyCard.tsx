"use client";

import { useState } from "react";
import { SurveyQuestion as SurveyQuestionType, SurveyAnswer } from "@/types/survey";
import { SurveyQuestion } from "./SurveyQuestion";
import { ProgressDots } from "@/components/ui/ProgressDots";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { AlertCircle, Phone } from "lucide-react";

export function SurveyCard({
  questions,
  onComplete
}: {
  questions: SurveyQuestionType[];
  onComplete: (answers: SurveyAnswer[]) => void;
}) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<SurveyAnswer[]>([]);
  const [showSupport, setShowSupport] = useState(false);

  const currentQ = questions[currentIndex];
  const currentValue = answers.find(a => a.questionId === currentQ.id)?.value ?? null;

  const handleAnswer = (value: number) => {
    const newAnswers = [...answers.filter(a => a.questionId !== currentQ.id), { questionId: currentQ.id, value: value as 0|1|2|3 }];
    setAnswers(newAnswers);

    if (currentQ.sensitive && value > 0) {
      setShowSupport(true);
      return;
    }

    setTimeout(() => {
      if (currentIndex < questions.length - 1) {
        setCurrentIndex(prev => prev + 1);
      } else {
        onComplete(newAnswers);
      }
    }, 400);
  };

  if (showSupport) {
    return (
      <div className="flex flex-col h-full justify-center animate-in fade-in zoom-in-95 duration-300">
        <Card className="flex flex-col items-center text-center p-8 border-red-500/50 bg-[#1A1515]">
          <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mb-6">
            <AlertCircle className="w-8 h-8 text-red-500" />
          </div>
          <h2 className="text-xl font-semibold text-slate-100 mb-4">Support is Available</h2>
          <p className="text-slate-300 mb-8 leading-relaxed">
            Based on your response, we want to make sure you have immediate support. You can connect with the Welfare Officer right now.
          </p>
          <div className="flex flex-col w-full gap-4">
            <Button variant="danger" className="w-full gap-2 text-lg min-h-[56px]">
              <Phone className="w-5 h-5" />
              Contact Welfare Officer
            </Button>
            <Button variant="ghost" className="min-h-[56px]" onClick={() => {
              setShowSupport(false);
              if (currentIndex < questions.length - 1) {
                setCurrentIndex(prev => prev + 1);
              } else {
                onComplete(answers);
              }
            }}>
              Continue Survey
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full justify-between pb-8">
      <div>
        <ProgressDots current={currentIndex} total={questions.length} />
        
        <div className="mt-4">
          <SurveyQuestion
            key={currentQ.id}
            question={currentQ}
            value={currentValue}
            onAnswer={handleAnswer}
          />
        </div>
      </div>

      <div className="flex justify-between items-center mt-8">
        <Button
          variant="ghost"
          disabled={currentIndex === 0}
          onClick={() => setCurrentIndex(prev => prev - 1)}
          className="px-4"
        >
          Back
        </Button>
        {currentValue !== null && (
          <Button
            onClick={() => {
              if (currentIndex < questions.length - 1) {
                setCurrentIndex(prev => prev + 1);
              } else {
                onComplete(answers);
              }
            }}
            className="px-6"
          >
            {currentIndex === questions.length - 1 ? "Finish" : "Next"}
          </Button>
        )}
      </div>
    </div>
  );
}
