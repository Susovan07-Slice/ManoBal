import { DailyCheckIn } from '@/types/checkin';
import { AssessmentSurvey, SurveyQuestion } from '@/types/survey';
import { PersonalTrend } from '@/types/trends';

export const mockCheckIns: DailyCheckIn[] = [
  {
    checkInId: 'CHK-2026-09-14',
    date: '2026-09-14',
    moodScore: 3,
    sleepHours: 5.5,
    physicalFatigueLevel: 4,
    operationalWorkloadLevel: 4,
    submittedAt: '2026-09-14T07:05:00Z',
  },
  {
    checkInId: 'CHK-2026-09-13',
    date: '2026-09-13',
    moodScore: 2,
    sleepHours: 4.8,
    physicalFatigueLevel: 5,
    operationalWorkloadLevel: 5,
    note: 'Long patrol, short turnaround before next shift.',
    submittedAt: '2026-09-13T22:40:00Z',
  },
];

export const surveyQuestions: SurveyQuestion[] = [
  { id: 'q1', category: 'Interest or pleasure in activities', promptSummary: 'Little interest or pleasure in doing things' },
  { id: 'q2', category: 'Low mood', promptSummary: 'Feeling down or discouraged' },
  { id: 'q3', category: 'Sleep difficulty', promptSummary: 'Trouble falling or staying asleep, or sleeping too much' },
  { id: 'q4', category: 'Fatigue', promptSummary: 'Feeling tired or having little energy' },
  { id: 'q5', category: 'Appetite change', promptSummary: 'Poor appetite or overeating' },
  { id: 'q6', category: 'Self-worth', promptSummary: 'Feeling bad about yourself, or that you are letting people down' },
  { id: 'q7', category: 'Concentration', promptSummary: 'Trouble concentrating on tasks' },
  { id: 'q8', category: 'Psychomotor change', promptSummary: 'Moving or speaking noticeably slower, or the opposite — restless' },
  { id: 'q9', category: 'Self-harm screening', promptSummary: 'Thoughts that you would be better off not around, or of harming yourself', sensitive: true },
];

export const mockSurvey: AssessmentSurvey = {
  surveyId: 'SUR-2026-09-10',
  type: 'PHQ9_STYLE',
  date: '2026-09-10',
  answers: [
    { questionId: 'q1', value: 1 }, { questionId: 'q2', value: 1 }, { questionId: 'q3', value: 2 },
    { questionId: 'q4', value: 2 }, { questionId: 'q5', value: 0 }, { questionId: 'q6', value: 1 },
    { questionId: 'q7', value: 1 }, { questionId: 'q8', value: 0 }, { questionId: 'q9', value: 0 },
  ],
  totalScore: 8,
  severityBand: 'Mild',
  flaggedForImmediateReview: false,
  submittedAt: '2026-09-10T20:15:00Z',
};

export const mockTrend: PersonalTrend = {
  last7Days: [
    { date: '2026-09-08', stressIndex: 38, sleepHours: 6.2, moodScore: 4 },
    { date: '2026-09-09', stressIndex: 41, sleepHours: 5.9, moodScore: 3 },
    { date: '2026-09-10', stressIndex: 47, sleepHours: 5.3, moodScore: 3 },
    { date: '2026-09-11', stressIndex: 52, sleepHours: 5.0, moodScore: 3 },
    { date: '2026-09-12', stressIndex: 55, sleepHours: 4.9, moodScore: 2 },
    { date: '2026-09-13', stressIndex: 58, sleepHours: 4.8, moodScore: 2 },
    { date: '2026-09-14', stressIndex: 53, sleepHours: 5.5, moodScore: 3 },
  ],
  averageStressIndex: 49,
  averageSleepHours: 5.4,
  trendDirection: 'worsening',
};

// Simulated async fetchers — swap the body for a real API call later.
export async function getRecentCheckIns(): Promise<DailyCheckIn[]> {
  await new Promise((r) => setTimeout(r, 300));
  return mockCheckIns;
}

export async function getSurveyQuestions(): Promise<SurveyQuestion[]> {
  await new Promise((r) => setTimeout(r, 200));
  return surveyQuestions;
}

export async function getPersonalTrend(): Promise<PersonalTrend> {
  await new Promise((r) => setTimeout(r, 350));
  return mockTrend;
}
