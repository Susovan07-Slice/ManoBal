export type NotificationType =
  | 'WELFARE_SUPPORT'
  | 'FOLLOW_UP_REQUEST'
  | 'FOLLOW_UP_REMINDER'
  | 'SUPPORT_RECOMMENDATION'
  | 'DUTY_SUPPORT_REVIEW'
  | 'RECOVERY_SUPPORT'
  | 'CASE_UPDATE'
  | 'WELFARE_MESSAGE';

export type NotificationPriority = 'INFO' | 'STANDARD' | 'PRIORITY' | 'URGENT';

export type NotificationStatus = 'UNREAD' | 'READ' | 'ACKNOWLEDGED' | 'DISMISSED';

export interface WelfareNotificationItem {
  id: number;
  recipient_personnel_id: number;
  recipient_personnel_code?: string | null;
  recipient_name?: string | null;
  notification_type: NotificationType;
  title: string;
  message: string;
  source_type?: string | null;
  source_id?: number | null;
  priority: NotificationPriority;
  action_url?: string | null;
  status: NotificationStatus;
  created_at: string;
  read_at?: string | null;
  acknowledged_at?: string | null;
  created_by?: number | null;
  creator_username?: string | null;
}

export interface NotificationListResponse {
  total: number;
  unread_count: number;
  notifications: WelfareNotificationItem[];
}

export interface UnreadCountResponse {
  unread_count: number;
}
