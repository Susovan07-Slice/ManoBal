'use client';

import React, { useState } from 'react';
import { HighRiskPersonnelItem, WelfareRequestOut } from '@/types/api';
import { ROLE_CONFIG } from '@/lib/rbac';
import { useAuth } from '@/lib/AuthContext';
import RiskBadge from './RiskBadge';
import AlertDetailDrawer from './AlertDetailDrawer';
import JawanRequestDrawer from './JawanRequestDrawer';
import EmptyState from '@/components/ui/EmptyState';
import { ShieldCheck, AlertTriangle, LifeBuoy, HeartPulse, Clock, Sparkles } from 'lucide-react';

interface AlertsTableProps {
  alerts: HighRiskPersonnelItem[];
  welfareRequests?: WelfareRequestOut[];
  isLoading?: boolean;
  onRefresh?: () => void;
}

export default function AlertsTable({
  alerts,
  welfareRequests = [],
  isLoading = false,
  onRefresh,
}: AlertsTableProps) {
  const { role } = useAuth();
  const config = ROLE_CONFIG[role] || ROLE_CONFIG.officer;

  const [activeTab, setActiveTab] = useState<'jawan_requests' | 'ai_recommendations'>('jawan_requests');
  const [selectedAlert, setSelectedAlert] = useState<HighRiskPersonnelItem | null>(null);
  const [selectedJawanRequest, setSelectedJawanRequest] = useState<WelfareRequestOut | null>(null);

  const pendingJawanCount = welfareRequests.filter((r) => r.status === 'pending').length;

  if (isLoading) {
    return (
      <div className="bg-surface border-military flex flex-col h-full w-full overflow-hidden p-6 justify-center items-center">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin mb-2" />
        <span className="text-xs font-mono text-textSecondary uppercase tracking-widest">
          Polling Welfare Alerts & Requests...
        </span>
      </div>
    );
  }

  return (
    <div className="bg-surface border-military flex flex-col h-full w-full overflow-hidden rounded-lg">
      {/* Top Header & Tab Navigation (Section 7 & 8) */}
      <div className="p-4 border-b border-surfaceHighlight bg-surfaceHighlight/20 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-2">
          <HeartPulse className="w-5 h-5 text-rose-400" />
          <div>
            <h3 className="text-base font-semibold text-textPrimary uppercase tracking-wider">
              Operational Welfare Alerts & Support Requests
            </h3>
            <p className="text-xs text-textSecondary font-mono">
              Distinguishing Jawan-initiated support from AI-generated predictive interventions
            </p>
          </div>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex items-center space-x-1 bg-surfaceHighlight/60 p-1 rounded-lg border border-surfaceHighlight self-start sm:self-auto text-xs">
          <button
            onClick={() => setActiveTab('jawan_requests')}
            className={`px-3 py-1.5 rounded-md font-mono font-semibold transition-colors flex items-center space-x-1.5 ${
              activeTab === 'jawan_requests'
                ? 'bg-accent text-white shadow-sm'
                : 'text-textSecondary hover:text-textPrimary hover:bg-surfaceHighlight'
            }`}
          >
            <LifeBuoy className="w-3.5 h-3.5" />
            <span>Jawan Requests</span>
            <span
              className={`px-1.5 py-0.2 rounded-full text-[10px] ${
                activeTab === 'jawan_requests'
                  ? 'bg-white/20 text-white'
                  : pendingJawanCount > 0
                  ? 'bg-amber-500/20 text-amber-300 font-bold'
                  : 'bg-surfaceHighlight text-textSecondary'
              }`}
            >
              {welfareRequests.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('ai_recommendations')}
            className={`px-3 py-1.5 rounded-md font-mono font-semibold transition-colors flex items-center space-x-1.5 ${
              activeTab === 'ai_recommendations'
                ? 'bg-accent text-white shadow-sm'
                : 'text-textSecondary hover:text-textPrimary hover:bg-surfaceHighlight'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI Risk Interventions</span>
            <span
              className={`px-1.5 py-0.2 rounded-full text-[10px] ${
                activeTab === 'ai_recommendations'
                  ? 'bg-white/20 text-white'
                  : 'bg-surfaceHighlight text-textSecondary'
              }`}
            >
              {alerts.length}
            </span>
          </button>
        </div>
      </div>

      {/* TAB 1: Jawan Welfare Requests */}
      {activeTab === 'jawan_requests' && (
        <div className="flex-1 overflow-auto">
          {welfareRequests.length === 0 ? (
            <EmptyState
              icon={ShieldCheck}
              title="No Active Jawan Requests"
              description="No personnel have submitted welfare support requests. Any voluntary welfare requests will appear here immediately."
            />
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="bg-surfaceHighlight/50 text-textSecondary uppercase tracking-widest text-xs sticky top-0 z-10 border-b border-surfaceHighlight">
                <tr>
                  <th className="px-4 py-3 font-medium">Source</th>
                  <th className="px-4 py-3 font-medium">Personnel Code</th>
                  <th className="px-4 py-3 font-medium">Name & Role</th>
                  <th className="px-4 py-3 font-medium">Department</th>
                  <th className="px-4 py-3 font-medium">Concern Category</th>
                  <th className="px-4 py-3 font-medium">Urgency</th>
                  <th className="px-4 py-3 font-medium">Current Risk</th>
                  <th className="px-4 py-3 font-medium">Submitted</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surfaceHighlight bg-surface">
                {welfareRequests.map((req) => (
                  <tr
                    key={req.id}
                    onClick={() => setSelectedJawanRequest(req)}
                    className="hover:bg-surfaceHighlight/30 cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-teal-950/60 text-teal-300 border border-teal-800/60">
                        Jawan Request
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono font-medium text-accent">
                      {req.personnel_code || `ID-${req.personnel_id}`}
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-textPrimary font-medium">{req.personnel_name || 'Enlisted Personnel'}</div>
                      <div className="text-textSecondary text-xs">{req.job_role || 'Field Service'}</div>
                    </td>
                    <td className="px-4 py-3 text-textSecondary text-xs">
                      <div className="font-mono text-textPrimary text-[11px]">{req.battalion || '7th Battalion'}</div>
                      <div className="text-[10px] text-textSecondary">{req.department || 'Operations'} • {req.location || 'Active Base'}</div>
                    </td>
                    <td className="px-4 py-3 font-medium text-textPrimary text-xs">
                      {req.category}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-mono font-semibold ${
                          req.urgency === 'High'
                            ? 'bg-rose-950/60 text-rose-300 border border-rose-800/50'
                            : req.urgency === 'Medium'
                            ? 'bg-amber-950/60 text-amber-300 border border-amber-800/50'
                            : 'bg-emerald-950/60 text-emerald-300 border border-emerald-800/50'
                        }`}
                      >
                        {req.urgency}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono">
                      {req.current_risk_score !== null ? (
                        <span className="font-bold text-amber-400">
                          {req.current_risk_score}
                          <span className="text-xs text-textSecondary font-normal">/100</span>
                        </span>
                      ) : (
                        <span className="text-textSecondary text-xs">Unassessed</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-textSecondary text-xs font-mono">
                      {new Date(req.created_at).toLocaleDateString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-mono font-bold uppercase ${
                          req.status === 'resolved'
                            ? 'bg-emerald-950/60 text-emerald-300 border border-emerald-800/50'
                            : req.status === 'in_progress'
                            ? 'bg-purple-950/60 text-purple-300 border border-purple-800/50'
                            : req.status === 'acknowledged'
                            ? 'bg-blue-950/60 text-blue-300 border border-blue-800/50'
                            : 'bg-amber-950/60 text-amber-300 border border-amber-800/50'
                        }`}
                      >
                        {req.status === 'in_progress' ? 'In Progress' : req.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* TAB 2: AI Risk Interventions & Flags */}
      {activeTab === 'ai_recommendations' && (
        <div className="flex-1 overflow-auto">
          {alerts.length === 0 ? (
            <EmptyState
              icon={ShieldCheck}
              title="No High-Risk Personnel Flags"
              description="No personnel are currently classified in the high-risk operational stress tier. All recent assessments within normal fatigue parameters."
            />
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="bg-surfaceHighlight/50 text-textSecondary uppercase tracking-widest text-xs sticky top-0 z-10 border-b border-surfaceHighlight">
                <tr>
                  <th className="px-4 py-3 font-medium">Source</th>
                  <th className="px-4 py-3 font-medium">Personnel Code</th>
                  <th className="px-4 py-3 font-medium">Name & Role</th>
                  <th className="px-4 py-3 font-medium">Department</th>
                  <th className="px-4 py-3 font-medium">Stress Tier</th>
                  <th className="px-4 py-3 font-medium">Risk Score</th>
                  <th className="px-4 py-3 font-medium">Welfare Priority</th>
                  <th className="px-4 py-3 font-medium">Assessment Date</th>
                  <th className="px-4 py-3 font-medium">Pending Recs</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surfaceHighlight bg-surface">
                {alerts.map((alert) => (
                  <tr
                    key={alert.id}
                    onClick={() => setSelectedAlert(alert)}
                    className="hover:bg-surfaceHighlight/30 cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-purple-950/60 text-purple-300 border border-purple-800/60">
                        AI Recommendation
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono font-medium text-accent">
                      {alert.personnel_code}
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-textPrimary font-medium">{alert.personnel_name}</div>
                      <div className="text-textSecondary text-xs">{alert.job_role}</div>
                    </td>
                    <td className="px-4 py-3 text-textSecondary text-xs">
                      {alert.department} • {alert.location}
                    </td>
                    <td className="px-4 py-3">
                      <RiskBadge level={alert.stress_level} />
                    </td>
                    <td className="px-4 py-3 font-mono text-rose-400 font-bold">
                      {alert.risk_score}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-mono font-semibold ${
                          alert.risk_priority === 'Priority'
                            ? 'bg-rose-950/60 text-rose-300 border border-rose-800/50'
                            : alert.risk_priority === 'Preventive'
                            ? 'bg-amber-950/60 text-amber-300 border border-amber-800/50'
                            : 'bg-emerald-950/60 text-emerald-300 border border-emerald-800/50'
                        }`}
                      >
                        {alert.risk_priority}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-textSecondary text-xs font-mono">
                      {new Date(alert.latest_assessment_date).toLocaleDateString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                      })}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-textSecondary">
                      {alert.pending_recommendations_count > 0 ? (
                        <span className="text-amber-400 font-bold">
                          {alert.pending_recommendations_count} Pending
                        </span>
                      ) : (
                        <span className="text-emerald-400">All Cleared</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Drawer for AI Alert Detail */}
      {selectedAlert && (
        <AlertDetailDrawer
          alert={selectedAlert}
          role={role}
          onClose={() => setSelectedAlert(null)}
          onRefresh={onRefresh}
        />
      )}

      {/* Drawer for Jawan Welfare Request Detail */}
      {selectedJawanRequest && (
        <JawanRequestDrawer
          request={selectedJawanRequest}
          onClose={() => setSelectedJawanRequest(null)}
          onRefresh={onRefresh}
        />
      )}
    </div>
  );
}
