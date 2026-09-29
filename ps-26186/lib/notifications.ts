import { apiClient } from './api';

export interface SendNotificationPayload {
  recipient_personnel_id: number;
  notification_type: string;
  title: string;
  message: string;
  priority?: string;
  action_url?: string;
  source_type?: string;
  source_id?: number;
}

export interface WelfareNotificationOut {
  id: number;
  recipient_personnel_id: number;
  recipient_personnel_code?: string | null;
  recipient_name?: string | null;
  notification_type: string;
  title: string;
  message: string;
  source_type?: string | null;
  source_id?: number | null;
  priority: string;
  action_url?: string | null;
  status: string;
  created_at: string;
  read_at?: string | null;
  acknowledged_at?: string | null;
  created_by?: number | null;
  creator_username?: string | null;
}

/**
 * Sends an authorized, supportive welfare notification to a personnel within scope.
 */
export async function sendWelfareNotification(
  payload: SendNotificationPayload
): Promise<WelfareNotificationOut> {
  return apiClient<WelfareNotificationOut>('/notifications/send', {
    method: 'POST',
    body: JSON.stringify(payload),
    requiresAuth: true,
  });
}
