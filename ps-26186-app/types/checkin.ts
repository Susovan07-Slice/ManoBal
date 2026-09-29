export interface DailyCheckIn {
  checkInId: string;
  date: string;                        // ISO date
  moodScore: 1 | 2 | 3 | 4 | 5;         // 1 = very low, 5 = very good
  sleepHours: number;
  physicalFatigueLevel: 1 | 2 | 3 | 4 | 5;
  operationalWorkloadLevel: 1 | 2 | 3 | 4 | 5;
  note?: string;                        // optional, short free text
  submittedAt: string;                  // ISO timestamp
}
