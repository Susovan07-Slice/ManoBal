'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { HighRiskPersonnelItem, WelfareRequestOut } from '@/types/api';
import { useAuth } from '@/lib/AuthContext';
import AlertDetailDrawer from './AlertDetailDrawer';
import JawanRequestDrawer from './JawanRequestDrawer';
import { AlertCircle, LifeBuoy, ArrowRight, ShieldCheck, Clock } from 'lucide-react';

interface UrgentTriageQueueProps {
  highRiskAlerts: HighRiskPersonnelItem[];
  welfareRequests: WelfareRequestOut[];
  isLoading?: boolean;
  onRefresh?: () => void;
}

export default function UrgentTriageQueue({
  highRiskAlerts,
  welfareRequests,
  isLoading,
  onRefresh,
}: UrgentTriageQueueProps) {
  const { role } = useAuth();
  const [selectedAlert, setSelectedAlert] = useState<HighRiskPersonnelItem | null>(null);
  const [selectedRequest, setSelectedRequest] = useState<WelfareRequestOut | null>(null);

  const pendingRequests = welfareRequests.filter((r) => r.status === 'pending');
  const criticalAlerts = highRiskAlerts.filter((a) => a.latest_risk_score >= 70);

  // Prioritize pending requests by urgency (High > Medium > Routine) then recency
  const urgencyWeight: Record<string, number> = { High: 3, Medium: 2, Routine: 1 };
  const sortedPendingRequests = [...pendingRequests].sort((a, b) => {
    const diff = (urgencyWeight[b.urgency] || 0) - (urgencyWeight[a.urgency] || 0);
    if (diff !== 0) return diff;
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });

  // Combine top urgent items (up to 4 total)
  const totalUrgent = pendingRequests.length + criticalAlerts.length;

  return (
    <div className="bg-surface border border-surfaceBorder rounded-2xl p-5 shadow-card flex flex-col justify-between h-full">
      <div>
        <div className="flex items-center justify-between pb-3 mb-4 border-b border-surfaceBorder">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-alert-roseBg border border-alert-roseBorder flex items-center justify-center">
              <AlertCircle className="w-4 h-4 text-alert-rose" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-textPrimary tracking-tight">
                Urgent Action Queue
              </h3>
              <p className="text-[11px] text-textSecondary font-mono">
                Personnel & requests requiring immediate command review
              </p>
            </div>
          </div>
          <span className={`px-2.5 py-1 rounded-full text-xs font-mono font-bold ${
            totalUrgent > 0 
              ? 'bg-alert-roseBg text-alert-roseText border border-alert-roseBorder' 
              : 'bg-alert-sageBg text-alert-sageText border border-alert-sageBorder'
          }`}>
            {totalUrgent > 0 ? `${totalUrgent} Pending Review` : 'All Clear'}
          </span>
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-16 rounded-xl bg-surfaceHighlight/50 animate-pulse" />
            ))}
          </div>
        ) : totalUrgent === 0 ? (
          <div className="py-8 text-center flex flex-col items-center justify-center space-y-2">
            <div className="w-10 h-10 rounded-full bg-alert-sageBg border border-alert-sageBorder flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-accent" />
            </div>
            <p className="text-xs font-medium text-textPrimary">No critical stress alerts or pending welfare requests.</p>
            <p className="text-[11px] text-textSecondary">Unit psychological telemetry is currently within nominal thresholds.</p>
          </div>
        ) : (
          <div className="space-y-2.5">
            {/* Show top pending Jawan welfare requests */}
            {sortedPendingRequests.slice(0, 2).map((req) => (
              <div
                key={`req-${req.id}`}
                className="p-3 bg-surfaceHighlight/40 hover:bg-surfaceHighlight/70 border border-surfaceBorder rounded-xl flex items-center justify-between transition-colors"
              >
                <div className="flex items-center space-x-3 min-w-0">
                  <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center shrink-0">
                    <LifeBuoy className="w-4 h-4 text-amber-500" />
                  </div>
                  <div className="truncate">
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-xs text-textPrimary truncate">{req.personnel_name}</span>
                      <span className="font-mono text-[10px] text-textSecondary px-1.5 py-0.5 rounded bg-surface border border-surfaceBorder">
                        {req.personnel_code}
                      </span>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider border ${
                          req.urgency === 'High'
                            ? 'bg-rose-500/15 text-rose-500 border-rose-500/30'
                            : req.urgency === 'Medium'
                            ? 'bg-amber-500/15 text-amber-500 border-amber-500/30'
                            : 'bg-blue-500/15 text-blue-500 border-blue-500/30'
                        }`}
                      >
                        {req.urgency}
                      </span>
                    </div>
                    <p className="text-[11px] text-textSecondary truncate mt-0.5">
                      <span className="font-medium text-textPrimary/90">{req.category}</span>
                      {req.message ? ` — "${req.message}"` : ''}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedRequest(req)}
                  className="px-3 py-1 bg-surface hover:bg-accent hover:text-white border border-surfaceBorder rounded-lg text-xs font-semibold text-textPrimary transition-colors shrink-0 ml-3 shadow-sm"
                >
                  Review
                </button>
              </div>
            ))}

            {/* Show top critical AI risk alerts */}
            {criticalAlerts.slice(0, 2).map((alert) => (
              <div
                key={`alert-${alert.personnel_id}`}
                className="p-3 bg-alert-roseBg/40 hover:bg-alert-roseBg/60 border border-alert-roseBorder/60 rounded-xl flex items-center justify-between transition-colors"
              >
                <div className="flex items-center space-x-3 min-w-0">
                  <div className="w-8 h-8 rounded-lg bg-alert-roseBg border border-alert-roseBorder flex items-center justify-center shrink-0">
                    <Clock className="w-4 h-4 text-alert-rose" />
                  </div>
                  <div className="truncate">
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-xs text-textPrimary truncate">{alert.personnel_name}</span>
                      <span className="font-mono text-[10px] text-textSecondary px-1.5 py-0.5 rounded bg-surface border border-surfaceBorder">
                        {alert.personnel_code}
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-rose-500/15 text-rose-500 border border-rose-500/30 font-bold uppercase tracking-wider">
                        Score {alert.latest_risk_score}/100
                      </span>
                    </div>
                    <p className="text-[11px] text-textSecondary truncate mt-0.5">
                      {alert.primary_risk_driver || 'Elevated cumulative duty load'}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedAlert(alert)}
                  className="px-3 py-1 bg-surface hover:bg-alert-rose hover:text-white border border-surfaceBorder rounded-lg text-xs font-semibold text-textPrimary transition-colors shrink-0 ml-3 shadow-sm"
                >
                  Inspect
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="pt-3 mt-3 border-t border-surfaceBorder flex items-center justify-between text-xs">
        <span className="text-[11px] text-textSecondary font-mono">
          Priority Response Svc
        </span>
        <Link
          href="/dashboard/alerts"
          className="inline-flex items-center space-x-1 font-semibold text-accent hover:text-accent-hover transition-colors"
        >
          <span>View All Alerts & Telemetry</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Drawers */}
      {selectedAlert && (
        <AlertDetailDrawer
          alert={selectedAlert}
          role={role || 'officer'}
          onClose={() => setSelectedAlert(null)}
          onRefresh={onRefresh}
        />
      )}

      {selectedRequest && (
        <JawanRequestDrawer
          request={selectedRequest}
          role={role || 'officer'}
          onClose={() => setSelectedRequest(null)}
          onRefresh={onRefresh}
        />
      )}
    </div>
  );
}
