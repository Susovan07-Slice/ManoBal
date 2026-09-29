import { apiClient } from './api';
import {
  PersonnelOut,
  PersonnelListResponse,
  PersonnelBase,
} from '@/types/api';

export interface PersonnelFilters {
  page?: number;
  size?: number;
  department?: string;
  location?: string;
  risk_priority?: string;
  stress_level?: string;
}

export async function getPersonnel(
  filters: PersonnelFilters = {}
): Promise<PersonnelListResponse> {
  const params = new URLSearchParams();
  if (filters.page) params.append('page', filters.page.toString());
  if (filters.size) params.append('size', filters.size.toString());
  if (filters.department) params.append('department', filters.department);
  if (filters.location) params.append('location', filters.location);
  if (filters.risk_priority) params.append('risk_priority', filters.risk_priority);
  if (filters.stress_level) params.append('stress_level', filters.stress_level);

  const qs = params.toString();
  return apiClient<PersonnelListResponse>(`/personnel${qs ? `?${qs}` : ''}`);
}

export async function getPersonnelById(id: number): Promise<PersonnelOut> {
  return apiClient<PersonnelOut>(`/personnel/${id}`);
}

export async function createPersonnel(
  data: PersonnelBase
): Promise<PersonnelOut> {
  return apiClient<PersonnelOut>('/personnel', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updatePersonnel(
  id: number,
  data: Partial<PersonnelBase>
): Promise<PersonnelOut> {
  return apiClient<PersonnelOut>(`/personnel/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}
