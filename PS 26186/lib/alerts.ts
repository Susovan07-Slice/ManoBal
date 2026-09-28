import { apiClient } from './api';
import { WelfareAlertOut, WelfareInterventionOut } from '@/types/api';

export async function getWelfareAlerts(
  personnelId?: number,
  status?: string,
  severity?: string
): Promise<WelfareAlertOut[]> {
  const query = new URLSearchParams();
  if (personnelId !== undefined) query.append('personnel_id', personnelId.toString());
  if (status) query.append('status', status);
  if (severity) query.append('severity', severity);
  
  return apiClient<WelfareAlertOut[]>(`/welfare/alerts?${query.toString()}`);
}

export async function getAlertById(alertId: number): Promise<WelfareAlertOut> {
  return apiClient<WelfareAlertOut>(`/welfare/alerts/${alertId}`);
}

export async function acknowledgeAlert(alertId: number): Promise<WelfareAlertOut> {
  return apiClient<WelfareAlertOut>(`/welfare/alerts/${alertId}/acknowledge`, {
    method: 'POST',
  });
}

export async function startReviewAlert(alertId: number): Promise<WelfareAlertOut> {
  return apiClient<WelfareAlertOut>(`/welfare/alerts/${alertId}/review`, {
    method: 'POST',
  });
}

export async function createIntervention(
  alertId: number, 
  interventionType: string, 
  plannedDate?: string, 
  notes?: string
): Promise<WelfareInterventionOut> {
  return apiClient<WelfareInterventionOut>(`/welfare/alerts/${alertId}/intervention`, {
    method: 'POST',
    body: JSON.stringify({ intervention_type: interventionType, planned_date: plannedDate, notes }),
  });
}

export async function scheduleFollowUp(
  interventionId: number, 
  followUpDate: string, 
  notes?: string
): Promise<WelfareInterventionOut> {
  return apiClient<WelfareInterventionOut>(`/welfare/interventions/${interventionId}/follow-up`, {
    method: 'POST',
    body: JSON.stringify({ follow_up_date: followUpDate, notes }),
  });
}

export async function resolveAlert(
  alertId: number, 
  resolutionReason: string, 
  dismiss: boolean = false
): Promise<WelfareAlertOut> {
  return apiClient<WelfareAlertOut>(`/welfare/alerts/${alertId}/resolve?dismiss=${dismiss}`, {
    method: 'POST',
    body: JSON.stringify({ resolution_reason: resolutionReason }),
  });
}
