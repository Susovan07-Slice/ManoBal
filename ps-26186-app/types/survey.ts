export type SurveyType = 'PHQ9_STYLE';

export interface SurveyQuestion {
  id: string;
  category: string;          // paraphrased category label, e.g. "Sleep difficulty"
  promptSummary: string;     // placeholder phrasing for dev/layout — replace with licensed text
  sensitive?: boolean;       // true only for the self-harm screening item
}

export interface SurveyAnswer {
  questionId: string;
  value: 0 | 1 | 2 | 3;      // "not at all" → "nearly every day"
}

export interface AssessmentSurvey {
  surveyId: string;
  type: SurveyType;
  date: string;
  answers: SurveyAnswer[];
  totalScore: number;                                                      // sum of values, 0-27
  severityBand: 'Minimal' | 'Mild' | 'Moderate' | 'Moderately Severe' | 'Severe';
  flaggedForImmediateReview: boolean;   // true if the sensitive item scored > 0
  submittedAt: string;
}
