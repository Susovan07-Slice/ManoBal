export interface TrendDay {
  date: string;
  stressIndex: number;   // 0-100, derived from check-in + survey signals
  sleepHours: number;
  moodScore: number;     // 1-5
}

export interface PersonalTrend {
  last7Days: TrendDay[];
  averageStressIndex: number;
  averageSleepHours: number;
  trendDirection: 'improving' | 'stable' | 'worsening';
}
