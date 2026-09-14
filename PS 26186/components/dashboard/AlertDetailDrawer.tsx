'use client';

import React from 'react';
import { PersonnelAlert } from '@/types/alerts';
import { ROLE_CONFIG } from '@/lib/rbac';
import { UserRole } from '@/types/rbac';
import RiskBadge from './RiskBadge';
import { X } from 'lucide-react';

export default function AlertDetailDrawer({
  alert,
  role,
  onClose,
  onStatusChange
}: {
  alert: PersonnelAlert;
  role: UserRole;
  onClose: () => void;
  onStatusChange: (id: string, status: PersonnelAlert['status']) => void;
}) {
  const config = ROLE_CONFIG[role];

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-surface border-l border-military shadow-2xl flex flex-col z-50 overflow-hidden transform transition-transform translate-x-0">
      <div className="flex items-center justify-between p-4 border-b border-surfaceHighlight bg-surfaceHighlight/30">
        <h2 className="text-lg font-semibold text-textPrimary">Alert Details</h2>
        <button onClick={onClose} className="p-1 hover:bg-surfaceHighlight rounded text-textSecondary hover:text-textPrimary transition-colors">
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        <div>
          <div className="flex justify-between items-start mb-2">
            <div>
              <div className="font-mono text-sm text-textSecondary">{alert.unitId}</div>
              <div className="text-textPrimary font-medium">{alert.role}</div>
            </div>
            <RiskBadge level={alert.stressRiskLevel} />
          </div>
          {config.canViewServiceIdentity && (
            <div className="mt-2 p-2 bg-surfaceHighlight/50 rounded text-sm font-mono text-textPrimary border border-surfaceHighlight">
              Service ID: {alert.serviceId}
            </div>
          )}
        </div>

        <div className="space-y-3">
          <h3 className="text-sm uppercase tracking-widest text-textSecondary font-semibold">Contributing Metrics</h3>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="bg-surfaceHighlight/30 p-2 rounded border border-surfaceHighlight">
              <span className="text-textSecondary block text-xs">Duty Hrs/Wk</span>
              <span className="font-mono text-textPrimary">{alert.contributingMetrics.dutyHoursPerWeek}</span>
            </div>
            <div className="bg-surfaceHighlight/30 p-2 rounded border border-surfaceHighlight">
              <span className="text-textSecondary block text-xs">Cons. Duty Days</span>
              <span className="font-mono text-textPrimary">{alert.contributingMetrics.consecutiveDutyDays}</span>
            </div>
            <div className="bg-surfaceHighlight/30 p-2 rounded border border-surfaceHighlight">
              <span className="text-textSecondary block text-xs">Night Shifts</span>
              <span className="font-mono text-textPrimary">{alert.contributingMetrics.nightShiftsPerMonth}</span>
            </div>
            <div className="bg-surfaceHighlight/30 p-2 rounded border border-surfaceHighlight">
              <span className="text-textSecondary block text-xs">Leave Gap</span>
              <span className="font-mono text-textPrimary">{alert.contributingMetrics.leaveGapDays} d</span>
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-sm uppercase tracking-widest text-textSecondary font-semibold mb-3">AI Risk Explanation</h3>
          {config.canViewFullExplanation ? (
            <ul className="space-y-2">
              {alert.riskExplanation.map((exp, i) => (
                <li key={i} className="text-sm text-textPrimary bg-surfaceHighlight/20 p-2 rounded border-l-2 border-accent">
                  {exp.factor} <span className="text-xs text-textSecondary font-mono ml-2">({(exp.contribution * 100).toFixed(0)}%)</span>
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-sm text-textSecondary p-3 bg-surfaceHighlight/30 rounded border border-surfaceHighlight italic">
              Detailed explanation factors restricted to Welfare Officer role.
            </div>
          )}
        </div>

        <div>
          <h3 className="text-sm uppercase tracking-widest text-textSecondary font-semibold mb-3">Welfare Recommendations</h3>
          {config.canViewFullExplanation ? (
            <ul className="space-y-2">
              {alert.welfareRecommendation.map((rec, i) => (
                <li key={i} className="text-sm text-textPrimary flex items-start">
                  <span className="text-accent mr-2">•</span>
                  {rec}
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-sm text-textPrimary p-3 bg-surfaceHighlight/30 rounded border border-surfaceHighlight">
              <span className="font-bold text-accent">{alert.welfareRecommendation.length}</span> welfare actions recommended.
            </div>
          )}
        </div>
      </div>

      {config.canEditStatus && (
        <div className="p-4 border-t border-surfaceHighlight bg-surfaceHighlight/20 flex gap-2">
          {/* Note: In a real app, this would trigger an API call. For now, it updates local state in AlertsTable. */}
          <select 
            value={alert.status}
            onChange={(e) => onStatusChange(alert.alertId, e.target.value as PersonnelAlert['status'])}
            className="flex-1 bg-surface border border-surfaceHighlight text-sm rounded px-3 py-2 text-textPrimary outline-none focus:border-accent font-medium"
          >
            <option value="New">New</option>
            <option value="Acknowledged">Acknowledged</option>
            <option value="Under Review">Under Review</option>
            <option value="Resolved">Resolved</option>
          </select>
        </div>
      )}
    </div>
  );
}
