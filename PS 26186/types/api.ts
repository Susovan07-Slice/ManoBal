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
  confidence?: 'High' | 'Moderate' | 'Low' | string;
  uncertainty?: number;
  risk_trend?: 'Improving' | 'Worsening' | 'Stable' | string;
  risk_change?: number;
  consecutive_high_risk?: number;
  risk_probability?: number;
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
  battalion?: string | null;
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

export interface LongitudinalCurrentState {
  risk_score: number;
  risk_category: string;
  assessment_timestamp: string;
}

export interface LongitudinalTrendState {
  direction: 'IMPROVING' | 'STABLE' | 'WORSENING' | 'INSUFFICIENT_DATA';
  score_change?: number | null;
  slope?: number | null;
  acceleration: 'INCREASING' | 'DECREASING' | 'STABLE' | 'INSUFFICIENT_DATA';
}

export interface LongitudinalHistoryState {
  assessment_count: number;
  data_sufficiency: 'INSUFFICIENT_DATA' | 'LIMITED_HISTORY' | 'SUFFICIENT_HISTORY';
  persistent_elevated_risk: boolean;
  consecutive_elevated_assessments: number;
  recent_average_score?: number | null;
  highest_recent_score?: number | null;
}

export interface LongitudinalBaselineState {
  historical_mean?: number | null;
  historical_median?: number | null;
  historical_std?: number | null;
  current_deviation?: number | null;
}

export interface RepeatedFactor {
  factor: string;
  type: 'risk' | 'protective';
  frequency: number;
  total_assessments: number;
  most_recent_occurrence: string;
  description: string;
}

export interface LongitudinalTrendResponse {
  personnel_id: number;
  current?: LongitudinalCurrentState | null;
  trend: LongitudinalTrendState;
  history: LongitudinalHistoryState;
  baseline: LongitudinalBaselineState;
  repeated_factors: RepeatedFactor[];
  disclaimer: string;
}

export interface WelfareAlertAuditOut {
  id: number;
  alert_id: number;
  action: string;
  actor_id?: number | null;
  previous_status?: string | null;
  new_status?: string | null;
  timestamp: string;
  metadata_json?: string | null;
}

export interface WelfareInterventionOut {
  id: number;
  alert_id: number;
  personnel_id: number;
  intervention_type: string;
  status: string;
  created_by: number;
  created_at: string;
  planned_date?: string | null;
  completed_at?: string | null;
  follow_up_date?: string | null;
  notes?: string | null;
}

export interface WelfareAlertOut {
  id: number;
  personnel_id: number;
  alert_type: string;
  severity: string;
  status: string;
  trigger_assessment_id?: number | null;
  trigger_reason?: string | null;
  created_at: string;
  acknowledged_at?: string | null;
  acknowledged_by?: number | null;
  resolved_at?: string | null;
  resolved_by?: number | null;
  resolution_reason?: string | null;
  interventions: WelfareInterventionOut[];
  audits: WelfareAlertAuditOut[];
}

// Phase 38: Commander Analytics Types
export interface CommanderAnalyticsScope {
  role: string;
  battalion?: string | null;
  location?: string | null;
  total_authorized_personnel: number;
  min_group_size_threshold: number;
}

export interface CommanderRiskCategoryItem {
  label: string;
  count: number;
  percentage: number;
}

export interface CommanderRiskDistribution {
  total_represented: number;
  categories: CommanderRiskCategoryItem[];
  low_count: number;
  low_pct: number;
  moderate_count: number;
  moderate_pct: number;
  elevated_count: number;
  elevated_pct: number;
  high_count: number;
  high_pct: number;
  critical_count: number;
  critical_pct: number;
}

export interface CommanderTimelinePoint {
  date: string;
  average_risk_score?: number | null;
  elevated_and_above_count: number;
  low_moderate_count: number;
  total_assessed: number;
}

export interface CommanderTrendSection {
  direction: 'IMPROVING' | 'STABLE' | 'WORSENING' | 'INSUFFICIENT_DATA' | 'LIMITED_HISTORY';
  improving_count: number;
  improving_pct: number;
  stable_count: number;
  stable_pct: number;
  worsening_count: number;
  worsening_pct: number;
  insufficient_history_count: number;
  insufficient_history_pct: number;
  mean_risk_score?: number | null;
  median_risk_score?: number | null;
  persistent_elevated_population: number;
  persistent_elevated_pct: number;
  timeline: CommanderTimelinePoint[];
}

export interface CommanderAlertTimelinePoint {
  date: string;
  created_count: number;
  resolved_count: number;
}

export interface CommanderAlertsSection {
  total_alerts: number;
  open_alerts: number;
  under_review_alerts: number;
  resolved_alerts: number;
  unresolved_alerts: number;
  by_type: Record<string, number>;
  by_severity: Record<string, number>;
  timeline: CommanderAlertTimelinePoint[];
}

export interface CommanderWelfareFactorItem {
  factor: string;
  affected_count: number;
  affected_pct: number;
  trend?: string | null;
}

export interface CommanderWelfareFactorsSection {
  factors: CommanderWelfareFactorItem[];
  total_records_analyzed: number;
}

export interface CommanderInterventionsSection {
  total_interventions: number;
  planned: number;
  completed: number;
  follow_up_required: number;
  by_type: Record<string, number>;
}

export interface CommanderSummarySection {
  total_authorized_personnel: number;
  assessed_personnel_count: number;
  assessment_coverage_pct: number;
  open_alerts_count: number;
  worsening_trend_count: number;
  worsening_trend_pct: number;
  persistent_elevated_count: number;
  persistent_elevated_pct: number;
  average_risk_score?: number | null;
}

export interface CommanderDateRangeInfo {
  start_date?: string | null;
  end_date?: string | null;
  filter_type: string;
}

export interface CommanderDataQualitySection {
  records_analyzed: number;
  personnel_count: number;
  latest_assessment_date?: string | null;
  date_range: CommanderDateRangeInfo;
  insufficient_data: boolean;
  notes: string[];
}

export interface CommanderAnalyticsResponse {
  status: 'SUCCESS' | 'INSUFFICIENT_GROUP_SIZE' | 'INSUFFICIENT_DATA';
  message?: string | null;
  scope: CommanderAnalyticsScope;
  summary?: CommanderSummarySection | null;
  risk_distribution?: CommanderRiskDistribution | null;
  trend?: CommanderTrendSection | null;
  alerts?: CommanderAlertsSection | null;
  welfare_factors?: CommanderWelfareFactorsSection | null;
  interventions?: CommanderInterventionsSection | null;
  data_quality: CommanderDataQualitySection;
}

// Phase 39: Welfare Anomaly & Early-Warning Types
export interface AnomalyEvidence {
  reason: string;
  baseline_metric?: string | null;
  baseline_value?: number | null;
  baseline_std?: number | null;
  current_value?: number | null;
  previous_value?: number | null;
  delta?: number | null;
  slope?: number | null;
  acceleration?: string | null;
  sample_count?: number;
  recent_records?: number;
  window_description?: string | null;
  co_occurring_factors?: string[];
  explanation: string;
}

export interface WelfareAnomalyOut {
  id: number;
  personnel_id?: number | null;
  personnel_code?: string | null;
  personnel_name?: string | null;
  department?: string | null;
  battalion?: string | null;
  location?: string | null;
  scope_type: string;
  scope_battalion?: string | null;
  scope_location?: string | null;
  anomaly_type: string;
  severity: 'INFO' | 'WATCH' | 'ATTENTION' | 'URGENT_REVIEW';
  status: 'DETECTED' | 'ACKNOWLEDGED' | 'UNDER_REVIEW' | 'RESOLVED' | 'DISMISSED';
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  baseline_sample_count: number;
  detected_at: string;
  observation_window_start?: string | null;
  observation_window_end?: string | null;
  evidence: AnomalyEvidence;
  acknowledged_at?: string | null;
  acknowledged_by?: number | null;
  resolved_at?: string | null;
  resolved_by?: number | null;
  resolution_notes?: string | null;
  associated_alert_id?: number | null;
  created_at: string;
  updated_at: string;
}

export interface PersonnelAnomalyHistoryResponse {
  personnel_id: number;
  status: 'DETECTED' | 'NO_ANOMALY' | 'INSUFFICIENT_BASELINE' | 'INSUFFICIENT_DATA';
  message: string;
  active_anomalies_count: number;
  anomalies: WelfareAnomalyOut[];
  baseline_summary?: Record<string, any> | null;
}

export interface CommanderAnomalyScope {
  role: string;
  battalion?: string | null;
  location?: string | null;
  total_authorized_personnel: number;
  min_group_size_threshold: number;
}

export interface CommanderAnomalySummaryResponse {
  status: 'SUCCESS' | 'INSUFFICIENT_GROUP_SIZE' | 'INSUFFICIENT_DATA';
  message?: string | null;
  scope: CommanderAnomalyScope;
  total_detected_anomalies: number;
  active_anomalies_count: number;
  by_severity: Record<string, number>;
  by_type: Record<string, number>;
  by_status: Record<string, number>;
  anomalies: WelfareAnomalyOut[];
  unit_level_signals: WelfareAnomalyOut[];
  data_quality: Record<string, any>;
}

// Phase 40: Welfare Recommendation & Support Engine Types
export interface RecommendationEvidence {
  trigger?: string;
  evidence_metrics?: Record<string, any>;
  reason: string;
  source_signals?: string[];
  key_factors?: string[];
  protective_factors?: string[];
  baseline_deviations?: Record<string, any>;
  trend_indicators?: Record<string, any>;
  audit_context?: Record<string, any>;
}

export type RecommendationType =
  | 'RECOVERY_REVIEW'
  | 'DUTY_SCHEDULE_REVIEW'
  | 'WELFARE_FOLLOW_UP'
  | 'VOLUNTARY_WELLNESS_CHECKIN'
  | 'SUPPORT_RESOURCE_REFERRAL'
  | 'FOLLOW_UP_ASSESSMENT'
  | 'CONTINUE_MONITORING'
  | 'HUMAN_REVIEW';

export type RecommendationPriority = 'ROUTINE' | 'ELEVATED' | 'HIGH' | 'CRITICAL';

export type RecommendationStatus =
  | 'SUGGESTED'
  | 'ACKNOWLEDGED'
  | 'ACCEPTED'
  | 'DEFERRED'
  | 'DISMISSED'
  | 'ACTIONED';

export interface WelfareRecommendationOut {
  id: number;
  personnel_id: number;
  personnel_code?: string | null;
  personnel_name?: string | null;
  department?: string | null;
  battalion?: string | null;
  location?: string | null;
  assessment_id?: number | null;
  recommendation_type: RecommendationType | string;
  recommendation_text: string;
  title: string;
  description?: string | null;
  reason?: string | null;
  priority: RecommendationPriority;
  status: RecommendationStatus;
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  evidence: RecommendationEvidence;
  source_signals: string[];
  recommended_review_window?: string | null;
  linked_alert_id?: number | null;
  linked_anomaly_id?: number | null;
  linked_intervention_id?: number | null;
  acknowledged_at?: string | null;
  acknowledged_by?: number | null;
  actioned_at?: string | null;
  actioned_by?: number | null;
  action_notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PersonnelRecommendationsResponse {
  personnel_id: number;
  status: string;
  message: string;
  total_recommendations: number;
  recommendations: WelfareRecommendationOut[];
}

export interface CommanderRecommendationSummaryResponse {
  scope_battalion?: string | null;
  scope_location?: string | null;
  total_active_recommendations: number;
  priority_breakdown: Record<string, number>;
  status_breakdown: Record<string, number>;
  type_breakdown: Record<string, number>;
  small_group_suppressed: boolean;
  recommendations: WelfareRecommendationOut[];
}

export interface RecommendationAcceptPayload {
  create_intervention?: boolean;
  intervention_type?: string;
  scheduled_date?: string;
  notes?: string;
}

export interface RecommendationDeferPayload {
  defer_days?: number;
  notes?: string;
}

export interface RecommendationDismissPayload {
  reason: string;
}

export interface RecommendationActionPayload {
  action_notes: string;
}



