import { apiClient } from './api';
import {
  WelfareNotificationItem,
  NotificationListResponse,
  UnreadCountResponse,
} from '@/types/notifications';

/**
 * Broadcasts an updated unread notification count to all components in the portal.
 */
export function broadcastUnreadCount(count: number) {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(
      new CustomEvent('manobal:notification_count_updated', {
        detail: { unreadCount: count },
      })
    );
  }
}

/**
 * Retrieves the authenticated Jawan's authorized welfare notifications.
 */
export async function getMyNotifications(
  statusFilter?: string,
  limit: number = 50,
  offset: number = 0
): Promise<NotificationListResponse> {
  const ts = Date.now();
  let url = `/notifications?limit=${limit}&offset=${offset}&_t=${ts}`;
  if (statusFilter && statusFilter !== 'ALL') {
    url += `&status=${encodeURIComponent(statusFilter)}`;
  }
  const res = await apiClient<NotificationListResponse>(url, {
    method: 'GET',
    requiresAuth: true,
    cache: 'no-store',
  });
  if (typeof res?.unread_count === 'number') {
    broadcastUnreadCount(res.unread_count);
  }
  return res;
}

/**
 * Retrieves the unread count of welfare notifications with strict cache busting.
 */
export async function getUnreadCount(): Promise<number> {
  try {
    const ts = Date.now();
    const res = await apiClient<UnreadCountResponse>(`/notifications/unread-count?_t=${ts}`, {
      method: 'GET',
      requiresAuth: true,
      cache: 'no-store',
    });
    const count = typeof res?.unread_count === 'number' ? res.unread_count : 0;
    broadcastUnreadCount(count);
    return count;
  } catch (err) {
    console.warn('Failed to retrieve unread notification count:', err);
    return 0;
  }
}

/**
 * Marks a single notification as READ.
 */
export async function markNotificationAsRead(
  notificationId: number
): Promise<WelfareNotificationItem> {
  const res = await apiClient<WelfareNotificationItem>(`/notifications/${notificationId}/read`, {
    method: 'POST',
    requiresAuth: true,
  });
  // Immediately request a fresh unread count in background to keep all screens in sync
  getUnreadCount().catch(() => {});
  return res;
}

/**
 * Marks all pending unread notifications as READ.
 */
export async function markAllNotificationsAsRead(): Promise<void> {
  await apiClient<UnreadCountResponse>('/notifications/read-all', {
    method: 'POST',
    requiresAuth: true,
  });
  broadcastUnreadCount(0);
}
