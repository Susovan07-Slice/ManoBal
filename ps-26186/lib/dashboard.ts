import { apiClient } from './api';
import {
  DashboardSummary,
  DistributionResponse,
  RecentAssessmentItem,
  HighRiskPersonnelItem,
} from '@/types/api';

export async function getDashboardSummary(): Promise<DashboardSummary> {
  return apiClient<DashboardSummary>('/dashboard/summary');
}

export async function getStressDistribution(): Promise<DistributionResponse> {
  return apiClient<DistributionResponse>('/dashboard/stress-distribution');
}

export async function getRiskDistribution(): Promise<DistributionResponse> {
  return apiClient<DistributionResponse>('/dashboard/risk-distribution');
}

export async function getRecentAssessments(limit: number = 10): Promise<RecentAssessmentItem[]> {
  return apiClient<RecentAssessmentItem[]>(`/dashboard/recent-assessments?limit=${limit}`);
}

export async function getHighRiskPersonnel(): Promise<HighRiskPersonnelItem[]> {
  return apiClient<HighRiskPersonnelItem[]>('/dashboard/high-risk');
}
