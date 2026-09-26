import { apiClient } from './api';
import { WelfareRequestCreate, WelfareRequestOut } from '@/types/api';

export async function submitWelfareRequest(
  payload: WelfareRequestCreate
): Promise<WelfareRequestOut> {
  return apiClient<WelfareRequestOut>('/welfare/requests', {
    method: 'POST',
    body: JSON.stringify(payload),
    requiresAuth: true,
  });
}

export async function getMyWelfareRequests(): Promise<WelfareRequestOut[]> {
  return apiClient<WelfareRequestOut[]>('/welfare/requests/my', {
    method: 'GET',
    requiresAuth: true,
  });
}
