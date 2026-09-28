'use client';

import React, { useState } from 'react';
import { HighRiskPersonnelItem, WelfareRequestOut } from '@/types/api';
import RiskBadge from './RiskBadge';
import AlertDetailDrawer from './AlertDetailDrawer';
import JawanRequestDrawer from './JawanRequestDrawer';
import { useAuth } from '@/lib/AuthContext';
import {
  ShieldAlert,
  ChevronRight,
  ShieldCheck,
  AlertTriangle,
  LifeBuoy,
  Sparkles,
  ExternalLink,
  Clock,
  User,
  CheckCircle,
} from 'lucide-react';
import EmptyState from '@/components/ui/EmptyState';

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
  const [selectedAlert, setSelectedAlert] = useState<HighRiskPersonnelItem | null>(null);
  const [selectedJawanRequest, setSelectedJawanRequest] = useState<WelfareRequestOut | null>(null);
  const [activeTab, setActiveTab] = useState<'jawan_requests' | 'ai_recommendations'>('jawan_requests');

  if (isLoading) {
    return (
      <div className="bg-surface border border-surfaceBorder rounded-xl p-5 shadow-card">
        <div className="h-5 w-48 bg-surfaceHighlight rounded mb-4 animate-pulse" />
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-12 bg-surfaceHighlight/50 rounded-lg animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  const pendingJawanCount = welfareRequests.filter((r) => r.status === 'pending').length;

  return (
    <div className="bg-surface border border-surfaceBorder rounded-xl overflow-hidden flex flex-col shadow-card">
      {/* Header & Tabs */}
      <div className="p-4 border-b border-surfaceBorder flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-surface">
        <div>
          <div className="flex items-center space-x-2">
            <h3 className="text-sm uppercase tracking-wider font-semibold text-textPrimary">
              Operational Welfare Inflow & Interventions
            </h3>
          </div>
          <p className="text-xs text-textSecondary mt-0.5">
            Voluntary Jawan welfare requests and AI-flagged stress priorities
          </p>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex items-center space-x-1 bg-surfaceHighlight p-1 rounded-lg border border-surfaceBorder self-start sm:self-auto text-xs">
          <button
            onClick={() => setActiveTab('jawan_requests')}
            className={`px-3 py-1.5 rounded-md font-mono font-semibold transition-colors flex items-center space-x-1.5 ${
              activeTab === 'jawan_requests'
                ? 'bg-accent text-[#FAFAFC] shadow-sm'
                : 'text-textSecondary hover:text-textPrimary hover:bg-surface'
            }`}
          >
            <LifeBuoy className="w-3.5 h-3.5" />
            <span>Jawan Requests</span>
            <span
              className={`px-1.5 py-0.2 rounded-full text-[10px] ${
                activeTab === 'jawan_requests'
                  ? 'bg-[#FAFAFC]/25 text-[#FAFAFC]'
                  : pendingJawanCount > 0
                  ? 'bg-[#FDF6EE] text-[#8E5B23] border border-[#F3D2AE] font-bold'
                  : 'bg-surface border border-surfaceBorder text-textSecondary'
              }`}
            >
              {welfareRequests.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('ai_recommendations')}
            className={`px-3 py-1.5 rounded-md font-mono font-semibold transition-colors flex items-center space-x-1.5 ${
              activeTab === 'ai_recommendations'
                ? 'bg-accent text-[#FAFAFC] shadow-sm'
                : 'text-textSecondary hover:text-textPrimary hover:bg-surface'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI Risk Interventions</span>
            <span
              className={`px-1.5 py-0.2 rounded-full text-[10px] ${
                activeTab === 'ai_recommendations'
                  ? 'bg-[#FAFAFC]/25 text-[#FAFAFC]'
                  : 'bg-surface border border-surfaceBorder text-textSecondary'
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
              <thead className="bg-surfaceHighlight/60 text-textSecondary uppercase tracking-widest text-xs sticky top-0 z-10 border-b border-surfaceBorder">
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
              <tbody className="divide-y divide-surfaceBorder bg-surface">
                {welfareRequests.map((req) => (
                  <tr
                    key={req.id}
                    onClick={() => setSelectedJawanRequest(req)}
                    className="hover:bg-surfaceHighlight/40 cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-accent/15 text-accent border border-accent/30">
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
                            ? 'bg-[#FAF0F0] text-[#964747] border border-[#E8B4B4]'
                            : req.urgency === 'Medium'
                            ? 'bg-[#FDF6EE] text-[#8E5B23] border border-[#F3D2AE]'
                            : 'bg-[#EEF6F2] text-[#2D6346] border border-[#BBD9C7]'
                        }`}
                      >
                        {req.urgency}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono">
                      {req.current_risk_score !== null ? (
                        <span className="font-bold text-[#8E5B23]">
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
                            ? 'bg-[#EEF6F2] text-[#2D6346] border border-[#BBD9C7]'
                            : req.status === 'in_progress'
                            ? 'bg-[#F4EFF8] text-[#69428E] border border-[#DCCBEA]'
                            : req.status === 'acknowledged'
                            ? 'bg-[#EEF4F8] text-[#3E6580] border border-[#BCD3E3]'
                            : 'bg-[#FDF6EE] text-[#8E5B23] border border-[#F3D2AE]'
                        }`}
                      >
                        {currentReqStatus(req.status)}
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
              <thead className="bg-surfaceHighlight/60 text-textSecondary uppercase tracking-widest text-xs sticky top-0 z-10 border-b border-surfaceBorder">
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
              <tbody className="divide-y divide-surfaceBorder bg-surface">
                {alerts.map((alert) => (
                  <tr
                    key={alert.id}
                    onClick={() => setSelectedAlert(alert)}
                    className="hover:bg-surfaceHighlight/40 cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-[#F4EFF8] text-[#69428E] border border-[#DCCBEA]">
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
                    <td className="px-4 py-3 font-mono text-[#964747] font-bold">
                      {alert.risk_score}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-mono font-semibold ${
                          alert.risk_priority === 'Priority'
                            ? 'bg-[#FAF0F0] text-[#964747] border border-[#E8B4B4]'
                            : alert.risk_priority === 'Preventive'
                            ? 'bg-[#FDF6EE] text-[#8E5B23] border border-[#F3D2AE]'
                            : 'bg-[#EEF6F2] text-[#2D6346] border border-[#BBD9C7]'
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
                        <span className="text-[#8E5B23] font-bold">
                          {alert.pending_recommendations_count} Pending
                        </span>
                      ) : (
                        <span className="text-[#2D6346]">All Cleared</span>
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

function currentReqStatus(status: string) {
  if (status === 'in_progress') return 'In Progress';
  return status;
}
