import { apiClient } from './api';

export type CaseStatus =
  | 'OPEN'
  | 'UNDER_REVIEW'
  | 'SUPPORT_IN_PROGRESS'
  | 'AWAITING_FOLLOW_UP'
  | 'MONITORING'
  | 'RESOLVED'
  | 'CLOSED';

export type CaseType =
  | 'CURRENT_RISK_REVIEW'
  | 'WORSENING_TREND'
  | 'ACTIVE_ALERT'
  | 'ANOMALY_REVIEW'
  | 'SUPPORT_FOLLOW_UP'
  | 'REPEATED_WELFARE_CONCERN'
  | 'OTHER';

export type HumanDecision =
  | 'CONTINUE_MONITORING'
  | 'CONTACT_PERSONNEL'
  | 'REVIEW_DUTY_SUPPORT'
  | 'OFFER_SUPPORT_RESOURCE'
  | 'SCHEDULE_FOLLOW_UP'
  | 'CONTINUE_EXISTING_INTERVENTION'
  | 'CLOSE_CASE'
  | 'REFER_TO_AUTHORIZED_SUPPORT'
  | 'OTHER';

export type ClosureReason =
  | 'RESOLVED'
  | 'MONITORING_COMPLETED'
  | 'SUPPORT_COMPLETED'
  | 'NO_FURTHER_ACTION_REQUIRED'
  | 'TRANSFERRED'
  | 'DUPLICATE'
  | 'OTHER';

export type NoteType =
  | 'REVIEW_NOTE'
  | 'SUPPORT_NOTE'
  | 'FOLLOW_UP_NOTE'
  | 'OUTCOME_NOTE'
  | 'CLOSURE_NOTE'
  | 'GENERAL_NOTE'
  | 'OTHER';

export type ReviewType =
  | 'INITIAL_TRIAGE'
  | 'PROGRESS_EVALUATION'
  | 'INTERVENTION_REVIEW'
  | 'FOLLOWUP_ASSESSMENT'
  | 'CLOSURE_REVIEW'
  | 'ROUTINE_MONITORING';

export interface SignalsSummaryOut {
  current_risk_category?: string | null;
  trend_direction?: string | null;
  has_active_alert: boolean;
  alert_severity?: string | null;
  has_active_anomaly: boolean;
  anomaly_severity?: string | null;
  has_open_recommendation: boolean;
  recommendation_priority?: string | null;
  intervention_status?: string | null;
  followup_status?: string | null;
  latest_outcome?: string | null;
}

export interface WelfareCaseListItemOut {
  id: number;
  case_reference: string;
  personnel_id: number;
  personnel_code: string;
  personnel_name: string;
  department: string;
  battalion: string;
  location: string;
  status: CaseStatus;
  case_type: CaseType;
  trigger_source: string;
  title: string;
  summary?: string | null;
  opened_at: string;
  opened_by_name?: string | null;
  last_reviewed_at?: string | null;
  last_reviewed_by_name?: string | null;
  closed_at?: string | null;
  closure_reason?: string | null;
  signals_summary: SignalsSummaryOut;
  created_at: string;
  updated_at: string;
}

export interface WelfareCaseListResponse {
  cases: WelfareCaseListItemOut[];
  total_count: number;
  data_suppressed: boolean;
  suppression_reason?: string | null;
}

export interface WelfareCaseReviewOut {
  id: number;
  case_id: number;
  reviewer_id?: number | null;
  reviewer_name?: string | null;
  reviewer_role?: string | null;
  reviewed_at: string;
  review_type: string;
  observations: string;
  decision: HumanDecision;
  next_step?: string | null;
  review_window?: string | null;
  notes?: string | null;
}

export interface WelfareCaseNoteOut {
  id: number;
  case_id: number;
  author_id?: number | null;
  author_name?: string | null;
  author_role?: string | null;
  created_at: string;
  note_type: NoteType;
  content: string;
}

export interface WelfareCaseAuditOut {
  id: number;
  case_id: number;
  action: string;
  actor_id?: number | null;
  actor_name?: string | null;
  previous_status?: string | null;
  new_status?: string | null;
  timestamp: string;
  metadata: Record<string, any>;
}

export interface TimelineEventOut {
  id: string;
  event_type: 'SYSTEM_EVENT' | 'HUMAN_ACTION';
  category: string;
  timestamp: string;
  title: string;
  description: string;
  actor?: string | null;
  metadata: Record<string, any>;
}

export interface WelfareCaseTimelineResponse {
  case_id: number;
  case_reference: string;
  personnel_code: string;
  events: TimelineEventOut[];
}

export interface WelfareCaseAuditsResponse {
  case_id: number;
  case_reference: string;
  audits: WelfareCaseAuditOut[];
}

export interface WelfareCaseEvidenceOut {
  current_risk: Record<string, any>;
  trend: Record<string, any>;
  active_alert?: Record<string, any> | null;
  active_anomaly?: Record<string, any> | null;
  open_recommendation?: Record<string, any> | null;
  intervention?: Record<string, any> | null;
  followup?: Record<string, any> | null;
  outcome?: Record<string, any> | null;
  notice: string;
}

export interface WelfareCaseDetailOut {
  id: number;
  case_reference: string;
  personnel_id: number;
  personnel_code: string;
  personnel_name: string;
  department: string;
  battalion: string;
  location: string;
  job_role?: string | null;
  status: CaseStatus;
  case_type: CaseType;
  trigger_source: string;
  title: string;
  summary?: string | null;
  opened_at: string;
  opened_by_id?: number | null;
  opened_by_name?: string | null;
  last_reviewed_at?: string | null;
  last_reviewed_by_id?: number | null;
  last_reviewed_by_name?: string | null;
  closed_at?: string | null;
  closed_by_id?: number | null;
  closed_by_name?: string | null;
  closure_reason?: string | null;
  closure_notes?: string | null;
  reopened_at?: string | null;
  reopened_by_id?: number | null;
  reopened_by_name?: string | null;
  reopen_reason?: string | null;
  assessment_id?: number | null;
  alert_id?: number | null;
  anomaly_id?: number | null;
  recommendation_id?: number | null;
  intervention_id?: number | null;
  followup_id?: number | null;
  evidence: WelfareCaseEvidenceOut;
  reviews: WelfareCaseReviewOut[];
  notes: WelfareCaseNoteOut[];
  latest_audit?: WelfareCaseAuditOut | null;
  created_at: string;
  updated_at: string;
}

export interface WelfareCaseSummaryStatsResponse {
  total_cases: number;
  open_cases: number;
  under_review_cases: number;
  monitoring_cases: number;
  closed_cases: number;
  status_counts: Record<string, number>;
  data_suppressed: boolean;
  suppression_reason?: string | null;
}

export interface WelfareCaseCreatePayload {
  personnel_id: number;
  case_type: CaseType;
  title?: string;
  summary?: string;
  trigger_source?: string;
  assessment_id?: number;
  alert_id?: number;
  anomaly_id?: number;
  recommendation_id?: number;
  intervention_id?: number;
  followup_id?: number;
}

export interface WelfareCaseReviewPayload {
  review_type: ReviewType;
  observations: string;
  decision: HumanDecision;
  next_step?: string;
  review_window?: string;
  notes?: string;
  new_status?: CaseStatus;
}

export interface WelfareCaseNotePayload {
  note_type: NoteType;
  content: string;
}

export interface WelfareCaseStatusPayload {
  status: CaseStatus;
  reason?: string;
}

export interface WelfareCaseClosePayload {
  closure_reason: ClosureReason;
  closure_notes?: string;
}

export interface WelfareCaseReopenPayload {
  reopen_reason: string;
}

export interface WelfareCaseFilters {
  status?: string;
  case_type?: string;
  search?: string;
  personnel_id?: number;
  battalion?: string;
  location?: string;
  limit?: number;
  offset?: number;
}

// ----------------------------------------------------------------------------
// API CALLS
// ----------------------------------------------------------------------------

export async function getWelfareCases(filters?: WelfareCaseFilters): Promise<WelfareCaseListResponse> {
  const params = new URLSearchParams();
  if (filters?.status && filters.status !== 'ALL') params.append('status', filters.status);
  if (filters?.case_type && filters.case_type !== 'ALL') params.append('case_type', filters.case_type);
  if (filters?.search) params.append('search', filters.search);
  if (filters?.personnel_id) params.append('personnel_id', filters.personnel_id.toString());
  if (filters?.battalion) params.append('battalion', filters.battalion);
  if (filters?.location) params.append('location', filters.location);
  if (filters?.limit) params.append('limit', filters.limit.toString());
  if (filters?.offset) params.append('offset', filters.offset.toString());

  const qs = params.toString();
  return apiClient<WelfareCaseListResponse>(`/welfare-cases${qs ? `?${qs}` : ''}`);
}

export async function getWelfareCaseDetail(caseId: number): Promise<WelfareCaseDetailOut> {
  return apiClient<WelfareCaseDetailOut>(`/welfare-cases/${caseId}`);
}

export async function createWelfareCase(payload: WelfareCaseCreatePayload): Promise<WelfareCaseDetailOut> {
  return apiClient<WelfareCaseDetailOut>('/welfare-cases', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function recordCaseReview(
  caseId: number,
  payload: WelfareCaseReviewPayload
): Promise<WelfareCaseReviewOut> {
  return apiClient<WelfareCaseReviewOut>(`/welfare-cases/${caseId}/review`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function addCaseNote(
  caseId: number,
  payload: WelfareCaseNotePayload
): Promise<WelfareCaseNoteOut> {
  return apiClient<WelfareCaseNoteOut>(`/welfare-cases/${caseId}/notes`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function updateCaseStatus(
  caseId: number,
  payload: WelfareCaseStatusPayload
): Promise<WelfareCaseDetailOut> {
  return apiClient<WelfareCaseDetailOut>(`/welfare-cases/${caseId}/status`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function closeWelfareCase(
  caseId: number,
  payload: WelfareCaseClosePayload
): Promise<WelfareCaseDetailOut> {
  return apiClient<WelfareCaseDetailOut>(`/welfare-cases/${caseId}/close`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function reopenWelfareCase(
  caseId: number,
  payload: WelfareCaseReopenPayload
): Promise<WelfareCaseDetailOut> {
  return apiClient<WelfareCaseDetailOut>(`/welfare-cases/${caseId}/reopen`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getCaseTimeline(caseId: number): Promise<WelfareCaseTimelineResponse> {
  return apiClient<WelfareCaseTimelineResponse>(`/welfare-cases/${caseId}/timeline`);
}

export async function getCaseAudits(caseId: number): Promise<WelfareCaseAuditsResponse> {
  return apiClient<WelfareCaseAuditsResponse>(`/welfare-cases/${caseId}/audits`);
}

export async function getCaseSummaryStats(params?: {
  battalion?: string;
  location?: string;
}): Promise<WelfareCaseSummaryStatsResponse> {
  const searchParams = new URLSearchParams();
  if (params?.battalion) searchParams.append('battalion', params.battalion);
  if (params?.location) searchParams.append('location', params.location);
  const qs = searchParams.toString();
  return apiClient<WelfareCaseSummaryStatsResponse>(`/welfare-cases/summary-stats${qs ? `?${qs}` : ''}`);
}
