import { apiClient } from './api';
import {
  WelfareAnomalyOut,
  AnomalyReviewRequest,
  AnomalyResolutionRequest,
  WelfareAnomalyAuditOut,
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

export async function reviewAnomaly(
  anomalyId: number,
  payload?: AnomalyReviewRequest
): Promise<WelfareAnomalyOut> {
  return apiClient<WelfareAnomalyOut>(`/anomalies/${anomalyId}/review`, {
    method: 'POST',
    body: payload ? JSON.stringify(payload) : undefined,
  });
}

export async function resolveAnomaly(
  anomalyId: number,
  payload: string | AnomalyResolutionRequest
): Promise<WelfareAnomalyOut> {
  const body =
    typeof payload === 'string'
      ? { resolution_notes: payload, notify_personnel: true }
      : {
          resolution_notes: payload.resolution_notes,
          notify_personnel: payload.notify_personnel !== false,
          custom_message: payload.custom_message,
        };
  return apiClient<WelfareAnomalyOut>(`/anomalies/${anomalyId}/resolve`, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function getAnomalyAudits(
  anomalyId: number
): Promise<WelfareAnomalyAuditOut[]> {
  return apiClient<WelfareAnomalyAuditOut[]>(`/anomalies/${anomalyId}/audits`);
}

