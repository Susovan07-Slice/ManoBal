'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  WelfareNotificationItem,
  NotificationType,
} from '@/types/notifications';
import {
  getMyNotifications,
  markNotificationAsRead,
  markAllNotificationsAsRead,
  broadcastUnreadCount,
  getUnreadCount,
} from '@/lib/notifications';
import {
  Bell,
  X,
  Check,
  CheckCheck,
  Calendar,
  HeartPulse,
  Shield,
  LifeBuoy,
  Clock,
  ArrowRight,
  RefreshCw,
  Sparkles,
  ExternalLink,
} from 'lucide-react';

interface NotificationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onUnreadCountChange?: (count: number) => void;
}

export default function NotificationDrawer({
  isOpen,
  onClose,
  onUnreadCountChange,
}: NotificationDrawerProps) {
  const router = useRouter();
  const [notifications, setNotifications] = useState<WelfareNotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<number | null>(null);

  const fetchNotifications = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getMyNotifications('ALL', 50, 0);
      setNotifications(res.notifications || []);
      setUnreadCount(res.unread_count || 0);
      if (onUnreadCountChange) {
        onUnreadCountChange(res.unread_count || 0);
      }
    } catch (err: any) {
      console.error('Failed to load welfare notifications:', err);
      setError(err?.message || 'Unable to load notifications.');
    } finally {
      setLoading(false);
    }
  }, [onUnreadCountChange]);

  useEffect(() => {
    if (isOpen) {
      fetchNotifications();
    }
  }, [isOpen, fetchNotifications]);

  const cleanText = (str?: string) => {
    if (!str) return '';
    return str.replace(/&amp;amp;/g, '&').replace(/&amp;/g, '&');
  };

  const handleMarkAsRead = async (id: number, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setUpdatingId(id);
    try {
      const updated = await markNotificationAsRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, status: 'READ', read_at: updated.read_at } : n))
      );
      const newCount = Math.max(0, unreadCount - 1);
      setUnreadCount(newCount);
      if (onUnreadCountChange) onUnreadCountChange(newCount);
      broadcastUnreadCount(newCount);
    } catch (err: any) {
      console.error('Failed to mark notification read:', err);
    } finally {
      setUpdatingId(null);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsAsRead();
      setNotifications((prev) =>
        prev.map((n) => ({ ...n, status: 'READ', read_at: new Date().toISOString() }))
      );
      setUnreadCount(0);
      if (onUnreadCountChange) onUnreadCountChange(0);
      broadcastUnreadCount(0);
    } catch (err: any) {
      console.error('Failed to mark all notifications read:', err);
    }
  };

  const handleActionClick = async (notif: WelfareNotificationItem) => {
    if (notif.status === 'UNREAD') {
      await handleMarkAsRead(notif.id);
    }
    onClose();
    if (notif.action_url) {
      router.push(notif.action_url);
    }
  };

  const getTypeMeta = (type: NotificationType) => {
    switch (type) {
      case 'FOLLOW_UP_REQUEST':
      case 'FOLLOW_UP_REMINDER':
        return {
          icon: Calendar,
          label: 'Follow-up Check-in',
          badgeClass: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
          actionLabel: 'Complete Check-in',
        };
      case 'SUPPORT_RECOMMENDATION':
        return {
          icon: Sparkles,
          label: 'Support Recommendation',
          badgeClass: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
          actionLabel: 'View Welfare Resources',
        };
      case 'DUTY_SUPPORT_REVIEW':
      case 'RECOVERY_SUPPORT':
        return {
          icon: HeartPulse,
          label: 'Recovery & Support',
          badgeClass: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
          actionLabel: 'View Support Guidance',
        };
      case 'CASE_UPDATE':
        return {
          icon: Shield,
          label: 'Welfare Team Update',
          badgeClass: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30',
          actionLabel: 'Review Portal',
        };
      case 'WELFARE_MESSAGE':
      case 'WELFARE_SUPPORT':
      default:
        return {
          icon: LifeBuoy,
          label: 'Welfare Support',
          badgeClass: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
          actionLabel: 'Open Details',
        };
    }
  };

  const formatTimeAgo = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      const diffMs = Date.now() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return `${diffHours}h ago`;
      const diffDays = Math.floor(diffHours / 24);
      if (diffDays === 1) return 'Yesterday';
      return `${diffDays}d ago`;
    } catch {
      return '';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="absolute inset-0 z-[60] flex flex-col animate-fade-in-down overflow-hidden rounded-[24px]">
      {/* Drawer Container (Full Screen Mobile) */}
      <div className="relative w-full h-full bg-gradient-to-br from-brand-50 via-white to-sky-50 flex flex-col shadow-2xl z-10">
        {/* Top Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-brand-100 bg-white/60 backdrop-blur-md">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-full bg-brand-100 border border-brand-200 flex items-center justify-center text-brand-600 shadow-sm">
              <Bell className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-[16px] font-bold text-ink tracking-tight">
                Welfare Notifications
              </h2>
              <p className="text-[11px] text-ink-3 font-medium">
                Authorized communications & support guidance
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-white shadow-sm border border-brand-100 flex items-center justify-center text-ink-3 hover:text-ink hover:bg-brand-50 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Action bar (Unread summary & Mark all read) */}
        <div className="flex items-center justify-between px-5 py-3 bg-brand-50/50 border-b border-brand-100 text-xs">
          <div className="flex items-center space-x-2">
            <span className="text-ink-3 font-medium">Pending:</span>
            {unreadCount > 0 ? (
              <span className="px-2 py-0.5 rounded-full bg-brand-100 text-brand-700 font-bold text-[11px] border border-brand-200">
                {unreadCount} unread
              </span>
            ) : (
              <span className="text-ink-3/60 font-medium">All caught up</span>
            )}
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={fetchNotifications}
              title="Refresh"
              className="text-ink-3 hover:text-ink transition flex items-center gap-1 text-[11px] font-semibold"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>

            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="text-[11px] text-brand-600 hover:text-brand-700 font-bold flex items-center gap-1 transition"
              >
                <CheckCheck className="w-3.5 h-3.5" /> Mark all read
              </button>
            )}
          </div>
        </div>

        {/* Notification List Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 pb-24">
          {loading ? (
            <div className="space-y-3 pt-2">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="p-4 rounded-2xl bg-white border border-brand-100 shadow-sm animate-pulse space-y-2.5"
                >
                  <div className="flex justify-between items-center">
                    <div className="h-4 w-28 bg-brand-50 rounded" />
                    <div className="h-3 w-12 bg-brand-50 rounded" />
                  </div>
                  <div className="h-3 w-3/4 bg-brand-50 rounded" />
                  <div className="h-3 w-1/2 bg-brand-50 rounded" />
                </div>
              ))}
            </div>
          ) : error ? (
            <div className="py-12 px-4 text-center">
              <p className="text-xs text-alert mb-3">{error}</p>
              <button
                onClick={fetchNotifications}
                className="px-4 py-2 bg-brand-100 rounded-lg text-xs font-semibold text-brand-700 hover:bg-brand-200 transition"
              >
                Retry
              </button>
            </div>
          ) : notifications.length === 0 ? (
            <div className="py-16 px-4 text-center flex flex-col items-center justify-center">
              <div className="w-14 h-14 rounded-full bg-brand-100 border border-brand-200 flex items-center justify-center text-brand-500 mb-4 shadow-sm">
                <Check className="w-7 h-7" />
              </div>
              <h3 className="text-[15px] font-bold text-ink mb-1.5">
                No Notifications
              </h3>
              <p className="text-[12px] text-ink-3 max-w-[240px] leading-relaxed">
                You have no active welfare notifications. Your unit welfare officer and monitoring team will reach out here with support updates.
              </p>
            </div>
          ) : (
            notifications.map((notif) => {
              const meta = getTypeMeta(notif.notification_type);
              const Icon = meta.icon;
              const isUnread = notif.status === 'UNREAD';

              return (
                <div
                  key={notif.id}
                  className={`p-4 rounded-2xl border transition-all ${
                    isUnread
                      ? 'bg-white border-brand-200 shadow-[0_4px_16px_rgba(16,185,129,0.08)]'
                      : 'bg-white/60 border-brand-100 opacity-80'
                  }`}
                >
                  {/* Category Pill and Time */}
                  <div className="flex items-center justify-between mb-2.5">
                    <div className="flex items-center space-x-2">
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${meta.badgeClass}`}
                      >
                        <Icon className="w-3 h-3" />
                        {meta.label}
                      </span>
                      {isUnread && (
                        <span className="w-2 h-2 rounded-full bg-brand-500 shadow-sm animate-pulse" />
                      )}
                    </div>
                    <span className="text-[10px] text-ink-3 font-mono font-medium">
                      {formatTimeAgo(notif.created_at)}
                    </span>
                  </div>

                  {/* Title */}
                  <h4 className="text-[14px] font-bold text-ink mb-1 tracking-tight">
                    {cleanText(notif.title)}
                  </h4>

                  {/* Message body */}
                  <p className="text-[12px] text-ink-2 leading-relaxed mb-3.5">
                    {cleanText(notif.message)}
                  </p>

                  {/* Action row */}
                  <div className="flex items-center justify-between pt-3 border-t border-brand-100/50">
                    {notif.action_url ? (
                      <button
                        onClick={() => handleActionClick(notif)}
                        className="inline-flex items-center gap-1.5 text-[11px] font-bold text-brand-600 hover:text-brand-700 transition"
                      >
                        {meta.actionLabel}
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    ) : (
                      <div />
                    )}

                    {isUnread && (
                      <button
                        disabled={updatingId === notif.id}
                        onClick={(e) => handleMarkAsRead(notif.id, e)}
                        className="text-[11px] font-semibold text-ink-3 hover:text-ink-2 transition flex items-center gap-1"
                      >
                        <Check className="w-3.5 h-3.5" /> Mark read
                      </button>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
