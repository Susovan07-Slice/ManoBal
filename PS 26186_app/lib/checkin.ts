import { apiClient } from './api';
import { PredictionResponse } from '@/types/api';

export interface DailyCheckInInput {
  moodScore: number;                 // 1-5
  sleepHours: number;                // 0-24
  physicalFatigueLevel: number;       // 1-5
  operationalWorkloadLevel: number;   // 1-5
  note?: string;
}

export interface CheckInResponse {
  status: string;
  message: string;
  assessment: PredictionResponse;
}

export async function submitCheckIn(
  input: DailyCheckInInput,
  userProfile?: { age?: number; gender?: string; department?: string; experience_years?: number; personnel_id?: number }
): Promise<CheckInResponse> {
  // Map mobile check-in scale to realistic operational domain telemetry
  const dutyHours = Math.round(40 + (input.operationalWorkloadLevel * 4.5));
  const workingHours = Math.round(38 + (input.operationalWorkloadLevel * 4.0));
  const nightShifts = Math.round(input.operationalWorkloadLevel * 1.5);
  const consecutiveDays = Math.round(input.physicalFatigueLevel * 2.2);
  const leaveGap = Math.round(30 + (input.physicalFatigueLevel * 18));
  const physActivity = Math.max(1, Math.round(6 - input.physicalFatigueLevel));

  const payload = {
    personnel_id: userProfile?.personnel_id,
    age: userProfile?.age || 29,
    gender: (userProfile?.gender as any) || 'Male',
    department: (userProfile?.department as any) || 'Operations',
    job_role: 'Field Operative',
    experience_years: userProfile?.experience_years || 5.0,
    working_hours_per_week: workingHours,
    duty_hours_per_week: dutyHours,
    sleep_hours: Number(input.sleepHours),
    physical_activity_hours_per_week: physActivity,
    annual_leaves_taken: 8,
    night_shifts_per_month: nightShifts,
    consecutive_duty_days: consecutiveDays,
    leave_gap_days: leaveGap,
    burnout_symptoms: input.physicalFatigueLevel >= 4 ? 'Often' : input.physicalFatigueLevel >= 3 ? 'Sometimes' : 'Rarely',
  };

  return apiClient<CheckInResponse>('/submit-checkin', {
    method: 'POST',
    body: JSON.stringify(payload),
    requiresAuth: true,
  });
}
