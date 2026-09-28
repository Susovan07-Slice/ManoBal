import { apiClient } from './api';
import {
  WelfareAnomalyOut,
  PersonnelAnomalyHistoryResponse,
  CommanderAnomalySummaryResponse,
} from '@/types/api';

export async function getPersonnelAnomalies(
  personnelId: number
): Promise<PersonnelAnomalyHistoryResponse> {
  return apiClient<PersonnelAnomalyHistoryResponse>(`/anomalies/personnel/${personnelId}`);
}

export async function getCommanderAnomalies(): Promise<CommanderAnomalySummaryResponse> {
  return apiClient<CommanderAnomalySummaryResponse>('/anomalies/commander');
}

export async function acknowledgeAnomaly(anomalyId: number): Promise<WelfareAnomalyOut> {
  return apiClient<WelfareAnomalyOut>(`/anomalies/${anomalyId}/acknowledge`, {
    method: 'POST',
  });
}

export async function reviewAnomaly(anomalyId: number): Promise<WelfareAnomalyOut> {
  return apiClient<WelfareAnomalyOut>(`/anomalies/${anomalyId}/review`, {
    method: 'POST',
  });
}

export async function resolveAnomaly(
  anomalyId: number,
  resolutionNotes: string
): Promise<WelfareAnomalyOut> {
  return apiClient<WelfareAnomalyOut>(`/anomalies/${anomalyId}/resolve`, {
    method: 'POST',
    body: JSON.stringify({ resolution_notes: resolutionNotes }),
  });
}
