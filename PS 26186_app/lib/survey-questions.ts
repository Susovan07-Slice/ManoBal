import { SurveyQuestion } from '@/types/survey';

/**
 * Standard duty and operational wellness questionnaire items.
 * PHQ-9 adapted for operational environment self-screening.
 */
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

export async function getSurveyQuestions(): Promise<SurveyQuestion[]> {
  return surveyQuestions;
}
