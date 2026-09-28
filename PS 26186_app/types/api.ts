export type UserRole = 'admin' | 'officer' | 'welfare' | 'personnel';

export interface UserOut {
  id: number;
  username: string;
  role: UserRole;
  is_active: boolean;
  personnel_id: number | null;
  battalion?: string | null;
  location?: string | null;
  created_at: string;
}

export interface Token {
  access_token: string;
  token_type: string;
  role: UserRole;
  username: string;
  personnel_id: number | null;
  battalion?: string | null;
  location?: string | null;
}

export interface PredictionResponse {
  stress_level: 'Low' | 'Medium' | 'High';
  risk_score: number;
  risk_priority: 'Routine' | 'Preventive' | 'Priority';
  risk_probability?: number;
  confidence?: 'High' | 'Moderate' | 'Low' | string;
  uncertainty?: number;
  risk_trend?: 'Improving' | 'Worsening' | 'Stable' | string;
  risk_change?: number;
  consecutive_high_risk?: number;
  probabilities: Record<string, number>;
  key_factors: string[];
  recommendations: string[];
  disclaimer: string;
}

export interface RecommendationOut {
  id: number;
  personnel_id: number;
  assessment_id: number;
  recommendation_type: string;
  recommendation_text: string;
  priority: string;
  status: 'pending' | 'acknowledged' | 'completed' | 'dismissed';
  created_at: string;
}

export interface StressAssessmentOut {
  id: number;
  personnel_id: number;
  personnel_code?: string | null;
  personnel_name?: string | null;
  stress_level: 'Low' | 'Medium' | 'High';
  low_probability: number;
  medium_probability: number;
  high_probability: number;
  risk_score: number;
  risk_priority: 'Routine' | 'Preventive' | 'Priority';
  risk_category?: 'Low' | 'Moderate' | 'Elevated' | 'High' | 'Critical' | string;
  confidence?: 'High' | 'Moderate' | 'Low' | string | number;
  uncertainty?: number;
  risk_trend?: 'Improving' | 'Worsening' | 'Stable' | string;
  risk_change?: number;
  consecutive_high_risk?: number;
  risk_probability?: number;
  key_factors: string[];
  top_risk_factors?: string[];
  protective_factors?: string[];
  model_version: string;
  assessment_timestamp: string;
  recommendations: RecommendationOut[];
}


export interface AssessmentResponse {
  status: string;
  message: string;
  assessment: StressAssessmentOut;
  disclaimer: string;
}

export interface AssessmentOverride {
  duty_hours_per_week?: number;
  night_shifts_per_month?: number;
  consecutive_duty_days?: number;
  leave_gap_days?: number;
  sleep_hours?: number;
  physical_activity_hours_per_week?: number;
  operational_exposure?: 'Low' | 'Medium' | 'High';
  remote_posting?: 'Yes' | 'No';
  mood_score?: number;
  burnout_symptoms?: 'Rarely' | 'Sometimes' | 'Often';
  physical_fatigue?: number;
  interest_score?: number;
  discouraged_score?: number;
  concentration_score?: number;
}

export interface AssessmentScheduleStatus {
  personnel_id: number;
  has_assessment: boolean;
  last_assessment_at: string | null;
  assessment_due: boolean;
  hours_since_last_assessment: number | null;
  next_assessment_due_at: string | null;
  latest_stress_level: 'Low' | 'Medium' | 'High' | null;
  latest_risk_score: number | null;
  latest_priority: 'Routine' | 'Preventive' | 'Priority' | null;
  message: string;
}

export interface WelfareRequestCreate {
  category: string;
  message?: string;
  urgency: 'Routine' | 'Medium' | 'High';
}

export interface WelfareRequestOut {
  id: number;
  personnel_id: number;
  personnel_code?: string | null;
  personnel_name?: string | null;
  department?: string | null;
  battalion?: string | null;
  job_role?: string | null;
  location?: string | null;
  current_risk_score?: number | null;
  current_stress_level?: 'Low' | 'Medium' | 'High' | null;
  current_risk_priority?: 'Routine' | 'Preventive' | 'Priority' | null;
  category: string;
  message?: string | null;
  urgency: 'Routine' | 'Medium' | 'High';
  status: 'pending' | 'acknowledged' | 'in_progress' | 'resolved';
  source: string;
  created_at: string;
  updated_at: string;
  resolved_at?: string | null;
}

export interface WelfareRecommendationOut {
  id: number;
  personnel_id: number;
  recommendation_type: string;
  recommendation_text: string;
  title: string;
  description?: string | null;
  reason?: string | null;
  priority: string;
  status: string;
  confidence: string;
  recommended_review_window?: string | null;
  created_at: string;
}

export interface PersonnelRecommendationsResponse {
  personnel_id: number;
  status: string;
  message: string;
  total_recommendations: number;
  recommendations: WelfareRecommendationOut[];
}



