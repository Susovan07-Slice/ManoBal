import { apiClient } from './api';
import {
  AssessmentResponse,
  StressAssessmentOut,
  AssessmentOverride,
  AssessmentScheduleStatus,
} from '@/types/api';

export async function submitAssessment(
  personnelId: number,
  override?: AssessmentOverride
): Promise<AssessmentResponse> {
  return apiClient<AssessmentResponse>(`/personnel/${personnelId}/assess`, {
    method: 'POST',
    body: override ? JSON.stringify(override) : undefined,
    requiresAuth: true,
  });
}

export async function getAssessmentHistory(
  personnelId: number
): Promise<StressAssessmentOut[]> {
  return apiClient<StressAssessmentOut[]>(`/personnel/${personnelId}/assessments`, {
    method: 'GET',
    requiresAuth: true,
  });
}

export async function getAssessmentScheduleStatus(
  personnelId?: number
): Promise<AssessmentScheduleStatus> {
  const endpoint = personnelId
    ? `/personnel/${personnelId}/assessment-status`
    : `/assessment/status`;
  return apiClient<AssessmentScheduleStatus>(endpoint, {
    method: 'GET',
    requiresAuth: true,
  });
}

