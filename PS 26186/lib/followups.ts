import { apiClient } from './api';

export interface WelfareFollowupOut {
  id: number;
  personnel_id: number;
  personnel_code?: string;
  personnel_name?: string;
  department?: string;
  battalion?: string;
  location?: string;
  recommendation_id?: number;
  intervention_id?: number;
  alert_id?: number;
  followup_type: string;
  status: string; // PENDING, SCHEDULED, COMPLETED, DEFERRED, DECLINED, CANCELLED, EXPIRED
  scheduled_at?: string;
  review_window?: string;
  due_date?: string;
  is_overdue: boolean;
  completed_at?: string;
  created_by?: number;
  completed_by?: number;
  notes?: string;
  outcome_status: string; // IMPROVED, STABLE, PERSISTENT_CONCERN, WORSENING, INSUFFICIENT_DATA
  baseline_source?: string;
  baseline_assessment_id?: number;
  followup_assessment_id?: number;
  evidence: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export interface UnitFollowupAnalyticsResponse {
  scope_battalion?: string;
  scope_location?: string;
  total_personnel_in_scope: number;
  privacy_threshold: number;
  data_suppressed: boolean;
  suppression_reason?: string;
  followups_total: number;
  followups_pending: number;
  followups_scheduled: number;
  followups_completed: number;
  followups_overdue: number;
  followups_deferred: number;
  followups_cancelled: number;
  outcome_distribution: Record<string, number>;
  persistent_concern_count: number;
  disclaimer: string;
}

export interface FollowupCreatePayload {
  personnel_id: number;
  followup_type: string;
  recommendation_id?: number;
  intervention_id?: number;
  alert_id?: number;
  review_window?: string;
  scheduled_at?: string;
  notes?: string;
}

export interface FollowupSchedulePayload {
  scheduled_at: string;
  notes?: string;
}

export interface FollowupCompletePayload {
  notes?: string;
  followup_assessment_id?: number;
  trigger_new_recommendation_if_worsening?: boolean;
}

export interface FollowupDeferPayload {
  defer_days: number;
  notes?: string;
}

export interface FollowupCancelPayload {
  reason: string;
}

export interface PersonnelFollowupsResponse {
  personnel_id: number;
  status: string;
  message: string;
  followups: WelfareFollowupOut[];
}

export interface FollowupAuditOut {
  id: number;
  followup_id: number;
  action: string;
  actor_id?: number;
  previous_status?: string;
  new_status?: string;
  timestamp: string;
  metadata: Record<string, any>;
}

export async function getPersonnelFollowups(personnelId: number): Promise<PersonnelFollowupsResponse> {
  return apiClient<PersonnelFollowupsResponse>(`/followups/personnel/${personnelId}`);
}

export async function createFollowup(payload: FollowupCreatePayload): Promise<WelfareFollowupOut> {
  return apiClient<WelfareFollowupOut>('/followups', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getFollowup(followupId: number): Promise<WelfareFollowupOut> {
  return apiClient<WelfareFollowupOut>(`/followups/${followupId}`);
}

export async function scheduleFollowup(
  followupId: number,
  payload: FollowupSchedulePayload
): Promise<WelfareFollowupOut> {
  return apiClient<WelfareFollowupOut>(`/followups/${followupId}/schedule`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function completeFollowup(
  followupId: number,
  payload: FollowupCompletePayload
): Promise<WelfareFollowupOut> {
  return apiClient<WelfareFollowupOut>(`/followups/${followupId}/complete`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function deferFollowup(
  followupId: number,
  payload: FollowupDeferPayload
): Promise<WelfareFollowupOut> {
  return apiClient<WelfareFollowupOut>(`/followups/${followupId}/defer`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function cancelFollowup(
  followupId: number,
  payload: FollowupCancelPayload
): Promise<WelfareFollowupOut> {
  return apiClient<WelfareFollowupOut>(`/followups/${followupId}/cancel`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function reassessFollowupOutcome(
  followupId: number,
  followupAssessmentId?: number
): Promise<WelfareFollowupOut> {
  const qs = followupAssessmentId ? `?followup_assessment_id=${followupAssessmentId}` : '';
  return apiClient<WelfareFollowupOut>(`/followups/${followupId}/reassess-outcome${qs}`, {
    method: 'POST',
  });
}

export async function getFollowupAudits(followupId: number): Promise<FollowupAuditOut[]> {
  return apiClient<FollowupAuditOut[]>(`/followups/${followupId}/audits`);
}

export async function getUnitFollowupSummary(params?: {
  battalion?: string;
  location?: string;
}): Promise<UnitFollowupAnalyticsResponse> {
  const searchParams = new URLSearchParams();
  if (params?.battalion) searchParams.append('battalion', params.battalion);
  if (params?.location) searchParams.append('location', params.location);
  const qs = searchParams.toString();
  return apiClient<UnitFollowupAnalyticsResponse>(`/followups/unit/summary${qs ? `?${qs}` : ''}`);
}
