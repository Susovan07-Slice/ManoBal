import { apiClient } from './api';
import {
  StressAssessmentOut,
  AssessmentResponse,
  AssessmentOverride,
  RecommendationOut,
} from '@/types/api';

export async function runPersonnelAssessment(
  personnelId: number,
  override?: AssessmentOverride
): Promise<AssessmentResponse> {
  return apiClient<AssessmentResponse>(`/personnel/${personnelId}/assess`, {
    method: 'POST',
    body: override ? JSON.stringify(override) : undefined,
  });
}

export async function getPersonnelAssessments(
  personnelId: number
): Promise<StressAssessmentOut[]> {
  return apiClient<StressAssessmentOut[]>(`/personnel/${personnelId}/assessments`);
}

export async function getAssessmentById(
  assessmentId: number
): Promise<StressAssessmentOut> {
  return apiClient<StressAssessmentOut>(`/assessments/${assessmentId}`);
}

export async function updateRecommendationStatus(
  recommendationId: number,
  status: 'pending' | 'acknowledged' | 'completed' | 'dismissed'
): Promise<RecommendationOut> {
  return apiClient<RecommendationOut>(`/recommendations/${recommendationId}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
}
