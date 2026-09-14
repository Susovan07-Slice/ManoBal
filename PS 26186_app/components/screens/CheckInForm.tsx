"use client";

import { useState } from "react";
import { RatingSlider } from "@/components/ui/RatingSlider";
import { Button } from "@/components/ui/Button";
import { DailyCheckIn } from "@/types/checkin";
import { ConfirmSheet } from "@/components/ui/ConfirmSheet";

export function CheckInForm({ onSubmit }: { onSubmit: (c: Omit<DailyCheckIn, 'checkInId' | 'submittedAt'>) => void }) {
  const [moodScore, setMoodScore] = useState<number>(0);
  const [sleepHours, setSleepHours] = useState<number>(7);
  const [physicalFatigue, setPhysicalFatigue] = useState<number>(0);
  const [workload, setWorkload] = useState<number>(0);
  
  const [confirmOpen, setConfirmOpen] = useState(false);

  const isComplete = moodScore > 0 && physicalFatigue > 0 && workload > 0;

  const handleSubmit = () => {
    onSubmit({
      date: new Date().toISOString().split('T')[0],
      moodScore: moodScore as any,
      sleepHours,
      physicalFatigueLevel: physicalFatigue as any,
      operationalWorkloadLevel: workload as any,
    });
    setConfirmOpen(false);
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-6">
        <RatingSlider label="Mood" value={moodScore} onChange={setMoodScore} />
        <RatingSlider label="Sleep (Hours)" value={sleepHours} onChange={setSleepHours} type="hours" />
        <RatingSlider label="Physical Fatigue" value={physicalFatigue} onChange={setPhysicalFatigue} />
        <RatingSlider label="Operational Workload" value={workload} onChange={setWorkload} />
      </div>

      <div className="pt-4 pb-12">
        <Button 
          className="w-full" 
          disabled={!isComplete} 
          onClick={() => setConfirmOpen(true)}
        >
          Submit Check-In
        </Button>
      </div>

      <ConfirmSheet
        open={confirmOpen}
        title="Submit Check-In"
        message="Are you sure you want to log these details for today?"
        onConfirm={handleSubmit}
        onCancel={() => setConfirmOpen(false)}
      />
    </div>
  );
}
