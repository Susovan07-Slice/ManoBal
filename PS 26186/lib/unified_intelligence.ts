import { apiClient } from './api';

export interface CurrentRiskSignal {
  risk_score: number | null;
  stress_level: string | null;
  risk_priority: string | null;
  assessment_timestamp: string | null;
  confidence: string;
  data_sufficiency: string;
  key_factors: string[];
  notice: string;
}

export interface TrendSignal {
  trend_direction: string;
  trend_slope: number | null;
  persistence: string;
  acceleration: string;
  personal_baseline_score: number | null;
  personal_baseline_category: string | null;
  score_change: number | null;
  data_sufficiency: string;
  explanation: string;
}

export interface AlertSignalItem {
  id: number;
  alert_type: string;
  severity: string;
  status: string;
  trigger_reason?: string | null;
  created_at?: string | null;
  created_at_relative?: string;
  acknowledged_at?: string | null;
  has_intervention: boolean;
}

export interface AnomalySignalItem {
  id: number;
  anomaly_type: string;
  severity: string;
  status: string;
  confidence: string;
  explanation?: string | null;
  detected_at?: string | null;
  detected_at_relative?: string;
}

export interface RecommendationSignalItem {
  id: number;
  recommendation_type: string;
  recommendation_text: string;
  priority: string;
  status: string;
  recommended_review_window?: string | null;
  reason?: string | null;
  created_at?: string | null;
  created_at_relative?: string;
}

export interface InterventionSignalItem {
  id: number;
  alert_id?: number | null;
  intervention_type: string;
  status: string;
  created_at?: string | null;
  created_at_relative?: string;
  updated_at?: string | null;
  follow_up_scheduled?: string | null;
  follow_up_notes?: string | null;
}

export interface FollowupSignalItem {
  id: number;
  followup_type: string;
  status: string;
  scheduled_at?: string | null;
  due_date?: string | null;
  completed_at?: string | null;
  is_overdue: boolean;
  outcome_status?: string | null;
  created_at?: string | null;
}

export interface DataFreshnessReport {
  last_assessment?: string | null;
  last_assessment_relative: string;
  last_alert?: string | null;
  last_alert_relative: string;
  last_anomaly?: string | null;
  last_anomaly_relative: string;
  last_recommendation?: string | null;
  last_recommendation_relative: string;
  last_followup?: string | null;
  last_followup_relative: string;
  is_stale: boolean;
  overall_freshness_status: string;
}

export interface HumanReviewIndicator {
  review_attention_level: 'REVIEW' | 'MONITOR' | 'NO_ACTIVE_REVIEW_SIGNAL' | 'INSUFFICIENT_DATA';
  reasons: string[];
  explanation: string;
}

export interface TimelineEventItem {
  timestamp: string;
  relative_time: string;
  phase: string;
  event_type: string;
  title: string;
  status: string;
  severity_or_priority?: string | null;
  summary: string;
  evidence: Record<string, any>;
}

export interface PersonnelWelfareSnapshotResponse {
  personnel_id: number;
  personnel_code: string;
  name: string;
  department?: string | null;
  battalion?: string | null;
  location?: string | null;
  job_role?: string | null;
  current_risk: CurrentRiskSignal;
  trend: TrendSignal;
  alerts: AlertSignalItem[];
  anomalies: AnomalySignalItem[];
  recommendations: RecommendationSignalItem[];
  interventions: InterventionSignalItem[];
  followups: FollowupSignalItem[];
  data_freshness: DataFreshnessReport;
  data_sufficiency: string;
  human_review_indicator: HumanReviewIndicator;
  timeline: TimelineEventItem[];
  disclaimer: string;
}

export interface UnitPersonnelSummaryCard {
  personnel_id: number;
  personnel_code: string;
  name: string;
  department?: string | null;
  battalion?: string | null;
  location?: string | null;
  current_risk_category?: string | null;
  current_risk_score?: number | null;
  trend_direction: string;
  review_level: string;
  active_alerts_count: number;
  active_anomalies_count: number;
  open_recommendations_count: number;
  open_interventions_count: number;
  pending_followups_count: number;
  has_overdue_followup: boolean;
  freshness_status: string;
}

export interface UnitOverviewSection {
  personnel_monitored: number;
  risk_distribution: Record<string, number>;
  trend_distribution: Record<string, number>;
  active_alerts_total: number;
  active_anomalies_total: number;
  open_recommendations_total: number;
  open_interventions_total: number;
  followups_total: number;
  followups_summary: {
    total: number;
    pending: number;
    scheduled: number;
    completed: number;
    overdue: number;
    deferred: number;
  };
  outcome_distribution: Record<string, number>;
}

export interface SupportWorkflowSection {
  recommendations_count: number;
  human_decisions_count: number;
  interventions_active_count: number;
  followups_completed_count: number;
  outcomes_observed_count: number;
}

export interface DataQualitySection {
  valid_assessments_count: number;
  stale_data_count: number;
  insufficient_data_count: number;
}

export interface HumanReviewSummarySection {
  review_needed_count: number;
  monitor_count: number;
  no_signal_count: number;
  insufficient_data_count: number;
}

export interface UnitWelfareIntelligenceResponse {
  scope_battalion?: string | null;
  scope_location?: string | null;
  total_personnel_in_scope: number;
  privacy_threshold: number;
  data_suppressed: boolean;
  suppression_reason?: string | null;
  unit_overview?: UnitOverviewSection;
  support_workflow?: SupportWorkflowSection;
  data_quality?: DataQualitySection;
  human_review_summary?: HumanReviewSummarySection;
  personnel_cards: UnitPersonnelSummaryCard[];
  disclaimer: string;
}

export async function fetchUnitWelfareIntelligence(params?: {
  battalion?: string;
  location?: string;
  timeFilter?: string;
}): Promise<UnitWelfareIntelligenceResponse> {
  const query = new URLSearchParams();
  if (params?.battalion) query.set('battalion', params.battalion);
  if (params?.location) query.set('location', params.location);
  if (params?.timeFilter) query.set('time_filter', params.timeFilter);

  const qs = query.toString() ? `?${query.toString()}` : '';
  return apiClient<UnitWelfareIntelligenceResponse>(`/analytics/welfare-intelligence/unit${qs}`);
}

export async function fetchPersonnelWelfareSnapshot(
  personnelId: number
): Promise<PersonnelWelfareSnapshotResponse> {
  return apiClient<PersonnelWelfareSnapshotResponse>(
    `/analytics/welfare-intelligence/personnel/${personnelId}`
  );
}
