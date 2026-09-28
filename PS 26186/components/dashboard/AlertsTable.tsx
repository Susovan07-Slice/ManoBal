'use client';

import React, { useState } from 'react';
import { HighRiskPersonnelItem, WelfareRequestOut } from '@/types/api';
import JawanRequestDrawer from './JawanRequestDrawer';
import { useAuth } from '@/lib/AuthContext';
import {
  ShieldAlert,
  ChevronRight,
  ShieldCheck,
  LifeBuoy,
  Clock,
  User,
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
  const [selectedJawanRequest, setSelectedJawanRequest] = useState<WelfareRequestOut | null>(null);

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
            Voluntary Jawan welfare requests and active assistance inquiries
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <div className="px-3 py-1.5 bg-surfaceHighlight rounded-lg border border-surfaceBorder text-xs font-mono font-semibold text-textPrimary flex items-center space-x-1.5">
            <LifeBuoy className="w-3.5 h-3.5 text-accent" />
            <span>Welfare Requests ({welfareRequests.length})</span>
            {pendingJawanCount > 0 && (
              <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] bg-[#FDF6EE] text-[#8E5B23] border border-[#F3D2AE]">
                {pendingJawanCount} Pending
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Jawan Welfare Requests */}
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
