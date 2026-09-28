import { apiClient } from './api';
import {
  WelfareRecommendationOut,
  PersonnelRecommendationsResponse,
  CommanderRecommendationSummaryResponse,
  RecommendationAcceptPayload,
  RecommendationDeferPayload,
  RecommendationDismissPayload,
  RecommendationActionPayload,
} from '@/types/api';

export async function getCommanderRecommendations(params?: {
  status?: string;
  priority?: string;
  recommendation_type?: string;
}): Promise<CommanderRecommendationSummaryResponse> {
  const searchParams = new URLSearchParams();
  if (params?.status && params.status !== 'ALL') searchParams.append('status', params.status);
  if (params?.priority && params.priority !== 'ALL') searchParams.append('priority', params.priority);
  if (params?.recommendation_type && params.recommendation_type !== 'ALL') {
    searchParams.append('recommendation_type', params.recommendation_type);
  }

  const qs = searchParams.toString();
  return apiClient<CommanderRecommendationSummaryResponse>(
    `/recommendations/commander${qs ? `?${qs}` : ''}`
  );
}

export async function getPersonnelRecommendations(
  personnelId: number,
  params?: { status?: string; priority?: string; recommendation_type?: string }
): Promise<PersonnelRecommendationsResponse> {
  const searchParams = new URLSearchParams();
  if (params?.status && params.status !== 'ALL') searchParams.append('status', params.status);
  if (params?.priority && params.priority !== 'ALL') searchParams.append('priority', params.priority);
  if (params?.recommendation_type && params.recommendation_type !== 'ALL') {
    searchParams.append('recommendation_type', params.recommendation_type);
  }

  const qs = searchParams.toString();
  return apiClient<PersonnelRecommendationsResponse>(
    `/recommendations/personnel/${personnelId}${qs ? `?${qs}` : ''}`
  );
}

export async function evaluateRecommendations(
  personnelId: number
): Promise<PersonnelRecommendationsResponse> {
  return apiClient<PersonnelRecommendationsResponse>(`/recommendations/evaluate/${personnelId}`, {
    method: 'POST',
  });
}

export async function acknowledgeRecommendation(
  recommendationId: number,
  notes?: string
): Promise<WelfareRecommendationOut> {
  return apiClient<WelfareRecommendationOut>(`/recommendations/${recommendationId}/acknowledge`, {
    method: 'POST',
    body: JSON.stringify({ notes }),
  });
}

export async function acceptRecommendation(
  recommendationId: number,
  payload: RecommendationAcceptPayload
): Promise<WelfareRecommendationOut> {
  return apiClient<WelfareRecommendationOut>(`/recommendations/${recommendationId}/accept`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function deferRecommendation(
  recommendationId: number,
  payload: RecommendationDeferPayload
): Promise<WelfareRecommendationOut> {
  return apiClient<WelfareRecommendationOut>(`/recommendations/${recommendationId}/defer`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function dismissRecommendation(
  recommendationId: number,
  payload: RecommendationDismissPayload
): Promise<WelfareRecommendationOut> {
  return apiClient<WelfareRecommendationOut>(`/recommendations/${recommendationId}/dismiss`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function actionRecommendation(
  recommendationId: number,
  payload: RecommendationActionPayload
): Promise<WelfareRecommendationOut> {
  return apiClient<WelfareRecommendationOut>(`/recommendations/${recommendationId}/action`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
