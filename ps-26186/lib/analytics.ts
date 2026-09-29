import { apiClient } from './api';
import { CommanderAnalyticsResponse } from '@/types/api';

export interface CommanderAnalyticsFilterParams {
  timeFilter?: string; // 7d, 30d, 90d, all, custom
  startDate?: string;
  endDate?: string;
  referenceTime?: string;
}

export async function getCommanderAnalytics(
  params: CommanderAnalyticsFilterParams = {}
): Promise<CommanderAnalyticsResponse> {
  const query = new URLSearchParams();
  if (params.timeFilter) query.append('time_filter', params.timeFilter);
  if (params.startDate) query.append('start_date', params.startDate);
  if (params.endDate) query.append('end_date', params.endDate);
  if (params.referenceTime) query.append('reference_time', params.referenceTime);

  const queryString = query.toString();
  const endpoint = queryString ? `/analytics/commander?${queryString}` : '/analytics/commander';
  return apiClient<CommanderAnalyticsResponse>(endpoint);
}
