'use client';

import React, { useState } from 'react';
import {
  sendWelfareNotification,
  SendNotificationPayload,
} from '@/lib/notifications';
import {
  Bell,
  X,
  Send,
  CheckCircle2,
  AlertTriangle,
  LifeBuoy,
  Calendar,
  Sparkles,
  HeartPulse,
  Info,
} from 'lucide-react';

interface SendWelfareNotificationModalProps {
  isOpen: boolean;
  onClose: () => void;
  personnelId: number;
  personnelCode?: string;
  personnelName?: string;
  battalion?: string;
  initialType?: string;
  initialTitle?: string;
  initialMessage?: string;
  initialActionUrl?: string;
  sourceType?: string;
  sourceId?: number;
  onSuccess?: () => void;
}

const SUPPORT_TEMPLATES = [
  {
    name: 'Welfare Check-in Requested',
    type: 'FOLLOW_UP_REQUEST',
    title: 'Welfare Follow-up Requested',
    message: 'Your unit welfare officer has requested a supportive check-in. Please review your portal to complete the check-in.',
    actionUrl: '/check-in',
    priority: 'PRIORITY',
  },
  {
    name: 'Support Resources Available',
    type: 'SUPPORT_RECOMMENDATION',
    title: 'Support Resources Available',
    message: 'Supportive guidance and wellness resources have been made available for you. Please review the details in your portal.',
    actionUrl: '/trends',
    priority: 'STANDARD',
  },
  {
    name: 'Follow-up Scheduled',
    type: 'FOLLOW_UP_REQUEST',
    title: 'Welfare Follow-up Scheduled',
    message: 'A routine welfare follow-up has been scheduled. Your unit leadership and welfare team are here to assist your recovery.',
    actionUrl: '/check-in',
    priority: 'STANDARD',
  },
  {
    name: 'Recovery & Support Guidance',
    type: 'RECOVERY_SUPPORT',
    title: 'Recovery Guidance Available',
    message: 'Please review your personal wellness guidance and suggested rest practices in your Jawan app.',
    actionUrl: '/trends',
    priority: 'STANDARD',
  },
  {
    name: 'Custom Support Message',
    type: 'WELFARE_SUPPORT',
    title: 'Welfare Support Notice',
    message: '',
    actionUrl: '',
    priority: 'STANDARD',
  },
];

export default function SendWelfareNotificationModal({
  isOpen,
  onClose,
  personnelId,
  personnelCode,
  personnelName,
  battalion,
  initialType,
  initialTitle,
  initialMessage,
  initialActionUrl,
  sourceType = 'COMMANDER_ACTION',
  sourceId,
  onSuccess,
}: SendWelfareNotificationModalProps) {
  const [selectedTemplateIndex, setSelectedTemplateIndex] = useState<number>(0);
  const [notifType, setNotifType] = useState<string>(initialType || SUPPORT_TEMPLATES[0].type);
  const [title, setTitle] = useState<string>(initialTitle || SUPPORT_TEMPLATES[0].title);
  const [message, setMessage] = useState<string>(initialMessage || SUPPORT_TEMPLATES[0].message);
  const [priority, setPriority] = useState<string>(SUPPORT_TEMPLATES[0].priority);
  const [actionUrl, setActionUrl] = useState<string>(initialActionUrl || SUPPORT_TEMPLATES[0].actionUrl);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [sentSuccess, setSentSuccess] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleTemplateChange = (idx: number) => {
    setSelectedTemplateIndex(idx);
    const tmpl = SUPPORT_TEMPLATES[idx];
    setNotifType(tmpl.type);
    setTitle(tmpl.title);
    if (tmpl.message) setMessage(tmpl.message);
    setPriority(tmpl.priority);
    setActionUrl(tmpl.actionUrl);
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !message.trim()) {
      setError('Please provide both title and message.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload: SendNotificationPayload = {
        recipient_personnel_id: personnelId,
        notification_type: notifType,
        title: title.trim(),
        message: message.trim(),
        priority: priority || 'STANDARD',
        action_url: actionUrl.trim() || undefined,
        source_type: sourceType,
        source_id: sourceId,
      };

      await sendWelfareNotification(payload);
      setSentSuccess(true);
      setTimeout(() => {
        if (onSuccess) onSuccess();
        onClose();
        setSentSuccess(false);
      }, 1200);
    } catch (err: any) {
      console.error('Failed to send welfare notification:', err);
      setError(err?.message || 'Failed to dispatch notification. Please check scope authorization.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-[520px] bg-surface border border-surfaceBorder rounded-2xl shadow-elevated overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-surfaceBorder bg-surfaceHighlight/50">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-accent/15 border border-accent/30 flex items-center justify-center text-accent">
              <Bell className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-textPrimary tracking-tight">
                Send Welfare Notification
              </h3>
              <p className="text-xs text-textSecondary">
                Authorized Commander-to-Jawan Support Communication
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-textSecondary hover:text-textPrimary hover:bg-surfaceHighlight transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Form */}
        <form onSubmit={handleSend} className="p-6 space-y-4">
          {/* Recipient summary pill */}
          <div className="p-3 rounded-xl bg-surfaceHighlight/60 border border-surfaceBorder flex items-center justify-between text-xs">
            <div>
              <span className="text-textSecondary">Recipient: </span>
              <span className="font-semibold text-textPrimary">
                {personnelName || 'Personnel'} ({personnelCode || `ID: ${personnelId}`})
              </span>
            </div>
            {battalion && (
              <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-accent/10 text-accent border border-accent/20">
                {battalion}
              </span>
            )}
          </div>

          {/* Template presets */}
          <div>
            <label className="block text-xs font-semibold text-textSecondary uppercase tracking-wider mb-1.5">
              Support Communication Template
            </label>
            <select
              value={selectedTemplateIndex}
              onChange={(e) => handleTemplateChange(Number(e.target.value))}
              className="w-full px-3 py-2 bg-surfaceHighlight border border-surfaceBorder rounded-xl text-xs text-textPrimary focus:outline-none focus:border-accent"
            >
              {SUPPORT_TEMPLATES.map((tmpl, idx) => (
                <option key={idx} value={idx}>
                  {tmpl.name}
                </option>
              ))}
            </select>
          </div>

          {/* Title input */}
          <div>
            <label className="block text-xs font-semibold text-textSecondary uppercase tracking-wider mb-1.5">
              Notification Title
            </label>
            <input
              type="text"
              value={title}
              maxLength={200}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Welfare Follow-up Requested"
              className="w-full px-3.5 py-2.5 bg-surfaceHighlight border border-surfaceBorder rounded-xl text-xs text-textPrimary focus:outline-none focus:border-accent"
              required
            />
          </div>

          {/* Message input */}
          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="text-xs font-semibold text-textSecondary uppercase tracking-wider">
                Support Message Content
              </label>
              <span className="text-[11px] font-mono text-textSecondary">
                {message.length} / 1000
              </span>
            </div>
            <textarea
              rows={3}
              value={message}
              maxLength={1000}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Enter non-punitive, supportive welfare guidance for the jawan..."
              className="w-full p-3 bg-surfaceHighlight border border-surfaceBorder rounded-xl text-xs text-textPrimary focus:outline-none focus:border-accent resize-none leading-relaxed"
              required
            />
            <p className="text-[11px] text-textSecondary mt-1 flex items-center gap-1">
              <Info className="w-3 h-3 text-accent shrink-0" />
              Keep wording welfare-focused. Do not include internal ML risk scores or disciplinary remarks.
            </p>
          </div>

          {/* Priority & Action Link grid */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-textSecondary uppercase tracking-wider mb-1.5">
                Priority
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="w-full px-3 py-2 bg-surfaceHighlight border border-surfaceBorder rounded-xl text-xs text-textPrimary focus:outline-none focus:border-accent"
              >
                <option value="STANDARD">Standard</option>
                <option value="PRIORITY">Priority</option>
                <option value="URGENT">Urgent Review</option>
                <option value="INFO">Informational</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-textSecondary uppercase tracking-wider mb-1.5">
                Action Deep Link
              </label>
              <select
                value={actionUrl}
                onChange={(e) => setActionUrl(e.target.value)}
                className="w-full px-3 py-2 bg-surfaceHighlight border border-surfaceBorder rounded-xl text-xs text-textPrimary focus:outline-none focus:border-accent"
              >
                <option value="/check-in">Daily Check-in (/check-in)</option>
                <option value="/assessment">Assessment (/assessment)</option>
                <option value="/trends">Wellness Trends (/trends)</option>
                <option value="">None (Notice only)</option>
              </select>
            </div>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="p-3 rounded-xl bg-danger/10 border border-danger/30 text-danger text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Success Banner */}
          {sentSuccess && (
            <div className="p-3 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>Notification successfully delivered to Jawan application!</span>
            </div>
          )}

          {/* Submit Actions */}
          <div className="flex items-center justify-end space-x-3 pt-3 border-t border-surfaceBorder">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-textSecondary hover:text-textPrimary hover:bg-surfaceHighlight transition"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={loading || sentSuccess}
              className="px-5 py-2 rounded-xl text-xs font-semibold bg-accent text-white hover:bg-accent/90 disabled:opacity-50 transition flex items-center gap-2 shadow-sm"
            >
              {loading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Sending...
                </>
              ) : sentSuccess ? (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5 text-white" />
                  Delivered
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  Send Welfare Notification
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
