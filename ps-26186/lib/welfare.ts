import { apiClient } from './api';
import { WelfareRequestOut } from '@/types/api';

export async function getWelfareRequests(
  status?: string,
  urgency?: string
): Promise<WelfareRequestOut[]> {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  if (urgency) params.append('urgency', urgency);

  const query = params.toString() ? `?${params.toString()}` : '';
  return apiClient<WelfareRequestOut[]>(`/welfare/requests${query}`, {
    method: 'GET',
    requiresAuth: true,
  });
}

export async function updateWelfareRequestStatus(
  requestId: number,
  status: 'pending' | 'acknowledged' | 'in_progress' | 'resolved'
): Promise<WelfareRequestOut> {
  return apiClient<WelfareRequestOut>(`/welfare/requests/${requestId}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
    requiresAuth: true,
  });
}
