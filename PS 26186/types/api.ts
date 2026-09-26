import { UserRole } from './rbac';

export interface UserOut {
  id: number;
  username: string;
  email?: string | null;
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

export interface CommanderSignupData {
  name: string;
  username: string;
  email?: string;
  password: string;
  battalion: string;
  location: string;
}

export interface PersonnelBase {
  personnel_code: string;
  name: string;
  age: number;
  gender: 'Male' | 'Female' | 'Other';
  department: string;
  job_role: string;
  battalion?: string;
  location: string;
  experience_years: number;
  duty_hours_per_week: number;
  night_shifts_per_month: number;
  consecutive_duty_days: number;
  transfer_frequency: number;
  training_load: number;
  leave_gap_days: number;
  deployment_days: number;
  remote_posting: 'Yes' | 'No';
  operational_exposure: 'Low' | 'Medium' | 'High';
}

export interface PersonnelOut extends PersonnelBase {
  id: number;
  created_at: string;
  updated_at: string;
  latest_risk_score?: number | null;
  latest_stress_level?: string | null;
  latest_priority?: string | null;
}

export interface PersonnelListResponse {
  items: PersonnelOut[];
  total: number;
  page: number;
  size: number;
  pages: number;
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
  key_factors: string[];
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

export interface DistributionItem {
  label: string;
  count: number;
  percentage: number;
}

export interface DashboardSummary {
  total_personnel: number;
  assessed_personnel: number;
  low_risk: number;
  medium_risk: number;
  high_risk: number;
  pending_recommendations: number;
  acknowledged_recommendations: number;
}

export interface DistributionResponse {
  total_assessed: number;
  distribution: DistributionItem[];
}

export interface RecentAssessmentItem {
  id: number;
  personnel_id: number;
  personnel_code: string;
  personnel_name: string;
  department: string;
  location: string;
  stress_level: string;
  risk_score: number;
  risk_priority: string;
  assessment_timestamp: string;
}

export interface HighRiskPersonnelItem {
  id: number;
  personnel_id: number;
  personnel_code: string;
  personnel_name: string;
  department: string;
  job_role: string;
  location: string;
  risk_score: number;
  stress_level: string;
  risk_priority: string;
  duty_hours_per_week: number;
  night_shifts_per_month: number;
  consecutive_duty_days: number;
  leave_gap_days: number;
  key_factors: string[];
  pending_recommendations_count: number;
  latest_assessment_date: string;
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
}

export interface WelfareRequestOut {
  id: number;
  personnel_id: number;
  personnel_code?: string | null;
  personnel_name?: string | null;
  department?: string | null;
  job_role?: string | null;
  location?: string | null;
  current_risk_score?: number | null;
  current_stress_level?: string | null;
  current_risk_priority?: string | null;
  category: string;
  message?: string | null;
  urgency: 'Routine' | 'Medium' | 'High';
  status: 'pending' | 'acknowledged' | 'in_progress' | 'resolved';
  source: string;
  created_at: string;
  updated_at: string;
  resolved_at?: string | null;
}

