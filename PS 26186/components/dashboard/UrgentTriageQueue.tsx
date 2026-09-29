'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { HighRiskPersonnelItem, WelfareRequestOut } from '@/types/api';
import { useAuth } from '@/lib/AuthContext';
import AlertDetailDrawer from './AlertDetailDrawer';
import JawanRequestDrawer from './JawanRequestDrawer';
import { AlertCircle, LifeBuoy, ArrowRight, ShieldCheck, Clock, Activity } from 'lucide-react';

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
  const [localRequests, setLocalRequests] = useState<WelfareRequestOut[]>(welfareRequests);

  React.useEffect(() => {
    setLocalRequests(welfareRequests);
  }, [welfareRequests]);

  // Active / unresolved requests: only unresolved items remain in the queue
  const activeRequests = localRequests.filter((r) => r.status !== 'resolved');
  const criticalAlerts = highRiskAlerts.filter((a) => (a.risk_score ?? a.latest_risk_score ?? 0) >= 70);

  // Prioritize active requests by urgency (High > Medium > Routine), then review stage, then recency
  const urgencyWeight: Record<string, number> = { High: 3, Medium: 2, Routine: 1 };
  const stageWeight: Record<string, number> = { pending: 3, acknowledged: 2, in_progress: 1 };
  const sortedActiveRequests = [...activeRequests].sort((a, b) => {
    const uDiff = (urgencyWeight[b.urgency] || 0) - (urgencyWeight[a.urgency] || 0);
    if (uDiff !== 0) return uDiff;
    const sDiff = (stageWeight[b.status] || 0) - (stageWeight[a.status] || 0);
    if (sDiff !== 0) return sDiff;
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });

  const totalUrgent = activeRequests.length + criticalAlerts.length;

  const handleRequestStatusUpdated = (updated: WelfareRequestOut) => {
    if (updated.status === 'resolved') {
      // Instantly remove resolved request from queue tab
      setLocalRequests((prev) => prev.filter((r) => r.id !== updated.id));
      if (selectedRequest?.id === updated.id) {
        setSelectedRequest(null);
      }
    } else {
      // Immediately reflect current review status in the queue tab (e.g. acknowledged or in_progress)
      setLocalRequests((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
      if (selectedRequest?.id === updated.id) {
        setSelectedRequest(updated);
      }
    }
  };

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
            {/* Show top active (unresolved) Jawan welfare requests */}
            {sortedActiveRequests.slice(0, 2).map((req) => (
              <div
                key={`req-${req.id}`}
                className="p-3 bg-surfaceHighlight/40 hover:bg-surfaceHighlight/70 border border-surfaceBorder rounded-xl flex items-center justify-between transition-colors"
              >
                <div className="flex items-center space-x-3 min-w-0">
                  <div className={`w-8 h-8 rounded-lg border flex items-center justify-center shrink-0 ${
                    req.status === 'acknowledged'
                      ? 'bg-sky-500/10 border-sky-500/25 text-sky-400'
                      : req.status === 'in_progress'
                      ? 'bg-purple-500/10 border-purple-500/25 text-purple-400'
                      : 'bg-amber-500/10 border-amber-500/25 text-amber-500'
                  }`}>
                    {req.status === 'acknowledged' ? (
                      <Clock className="w-4 h-4 text-sky-400" />
                    ) : req.status === 'in_progress' ? (
                      <Activity className="w-4 h-4 text-purple-400" />
                    ) : (
                      <LifeBuoy className="w-4 h-4 text-amber-500" />
                    )}
                  </div>
                  <div className="truncate">
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-xs text-textPrimary truncate">{req.personnel_name}</span>
                      <span className="font-mono text-[10px] text-textSecondary px-1.5 py-0.5 rounded bg-surface border border-surfaceBorder">
                        {req.personnel_code}
                      </span>
                      {/* Urgency Badge */}
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
                      {/* Review Status Badge */}
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider border flex items-center gap-1 ${
                          req.status === 'acknowledged'
                            ? 'bg-sky-500/15 text-sky-400 border-sky-500/30'
                            : req.status === 'in_progress'
                            ? 'bg-purple-500/15 text-purple-400 border-purple-500/30'
                            : 'bg-amber-500/15 text-amber-500 border-amber-500/30'
                        }`}
                      >
                        {req.status === 'acknowledged' ? (
                          <>
                            <Clock className="w-3 h-3 text-sky-400" />
                            <span>Acknowledged</span>
                          </>
                        ) : req.status === 'in_progress' ? (
                          <>
                            <Activity className="w-3 h-3 text-purple-400" />
                            <span>In Progress</span>
                          </>
                        ) : (
                          <>
                            <AlertCircle className="w-3 h-3 text-amber-500" />
                            <span>Pending Review</span>
                          </>
                        )}
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
                  className={`px-3 py-1 border rounded-lg text-xs font-semibold transition-colors shrink-0 ml-3 shadow-sm ${
                    req.status === 'acknowledged'
                      ? 'bg-sky-500/10 text-sky-400 border-sky-500/30 hover:bg-sky-500 hover:text-white'
                      : req.status === 'in_progress'
                      ? 'bg-purple-500/10 text-purple-400 border-purple-500/30 hover:bg-purple-500 hover:text-white'
                      : 'bg-surface hover:bg-accent hover:text-white border-surfaceBorder text-textPrimary'
                  }`}
                >
                  {req.status === 'acknowledged' ? 'Action' : req.status === 'in_progress' ? 'Resolve' : 'Review'}
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
                        Score {alert.risk_score ?? alert.latest_risk_score ?? 0}/100
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
          onStatusUpdated={handleRequestStatusUpdated}
        />
      )}
    </div>
  );
}
