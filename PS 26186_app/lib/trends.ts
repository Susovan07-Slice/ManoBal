import { StressAssessmentOut } from '@/types/api';
import { PersonalTrend, TrendDay } from '@/types/trends';

/**
 * Computes trend metrics from real backend assessment history.
 */
export function computePersonalTrend(assessments: StressAssessmentOut[]): PersonalTrend {
  if (!assessments || assessments.length === 0) {
    return {
      last7Days: [],
      averageStressIndex: 0,
      averageSleepHours: 0,
      trendDirection: 'stable',
    };
  }

  // Sort chronologically ascending
  const sorted = [...assessments].sort(
    (a, b) => new Date(a.assessment_timestamp).getTime() - new Date(b.assessment_timestamp).getTime()
  );

  // Take the most recent up to 7 entries
  const recent = sorted.slice(-7);

  const days: TrendDay[] = recent.map((item) => {
    const date = item.assessment_timestamp.split(/[T ]/)[0];
    const stressIndex = Math.round(item.risk_score);
    // Use real assessment sleep & duty hours if present; otherwise fallback gracefully
    const sleepHours = typeof item.sleep_hours === 'number'
      ? item.sleep_hours
      : (item.stress_level === 'Low' ? 7.2 : item.stress_level === 'Medium' ? 5.8 : 4.5);
    const dutyHours = typeof item.duty_hours_per_week === 'number'
      ? item.duty_hours_per_week
      : 48;
    const moodScore = typeof item.mood_score === 'number'
      ? item.mood_score
      : (item.stress_level === 'Low' ? 4 : item.stress_level === 'Medium' ? 3 : 2);

    return {
      date,
      stressIndex,
      sleepHours,
      dutyHours,
      moodScore,
    };
  });

  const avgStress = Math.round(
    days.reduce((acc, curr) => acc + curr.stressIndex, 0) / days.length
  );
  const avgSleep = parseFloat(
    (days.reduce((acc, curr) => acc + curr.sleepHours, 0) / days.length).toFixed(1)
  );
  const avgDuty = parseFloat(
    (days.reduce((acc, curr) => acc + (curr.dutyHours ?? 48), 0) / days.length).toFixed(1)
  );

  let trendDirection: 'improving' | 'stable' | 'worsening' = 'stable';
  if (days.length >= 2) {
    const firstScore = days[0].stressIndex;
    const lastScore = days[days.length - 1].stressIndex;

    if (lastScore < firstScore - 2) {
      trendDirection = 'improving';
    } else if (lastScore > firstScore + 2) {
      trendDirection = 'worsening';
    }
  }

  return {
    last7Days: days,
    averageStressIndex: avgStress,
    averageSleepHours: avgSleep,
    averageDutyHours: avgDuty,
    trendDirection,
  };
}
