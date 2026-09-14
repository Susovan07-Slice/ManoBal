'use client';

import React, { useState } from 'react';
import { PersonnelAlert } from '@/types/alerts';
import { ROLE_CONFIG } from '@/lib/rbac';
import { useRole } from '@/lib/RoleContext';
import RiskBadge from './RiskBadge';
import AlertDetailDrawer from './AlertDetailDrawer';
import EmptyState from '@/components/ui/EmptyState';
import { ShieldCheck } from 'lucide-react';

export default function AlertsTable({ alerts: initialAlerts }: { alerts: PersonnelAlert[] }) {
  const { role } = useRole();
  const config = ROLE_CONFIG[role];
  
  // Note: Status changes are local component state for demo purposes as specified in Phase 1.3
  const [alerts, setAlerts] = useState(initialAlerts);
  const [selectedAlert, setSelectedAlert] = useState<PersonnelAlert | null>(null);

  const handleStatusChange = (id: string, status: PersonnelAlert['status']) => {
    setAlerts(prev => prev.map(a => a.alertId === id ? { ...a, status } : a));
    if (selectedAlert?.alertId === id) {
      setSelectedAlert({ ...selectedAlert, status });
    }
  };

  return (
    <div className="bg-surface border-military flex flex-col h-full w-full overflow-hidden">
      <div className="p-4 border-b border-surfaceHighlight flex justify-between items-center bg-surfaceHighlight/20">
        <h3 className="text-base font-semibold text-textPrimary uppercase tracking-widest">Personnel Risk Alerts</h3>
      </div>
      <div className="flex-1 overflow-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-surfaceHighlight/50 text-textSecondary uppercase tracking-widest text-xs sticky top-0 z-10 border-b border-surfaceHighlight">
            <tr>
              <th className="px-4 py-3 font-medium">Unit / Role</th>
              {config.canViewServiceIdentity && <th className="px-4 py-3 font-medium">Service ID</th>}
              <th className="px-4 py-3 font-medium">Risk Level</th>
              <th className="px-4 py-3 font-medium">Score</th>
              <th className="px-4 py-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surfaceHighlight bg-surface">
            {alerts.map(alert => (
              <tr 
                key={alert.alertId} 
                onClick={() => setSelectedAlert(alert)}
                className="hover:bg-surfaceHighlight/30 cursor-pointer transition-colors"
              >
                <td className="px-4 py-3">
                  <div className="font-mono text-textPrimary">{alert.unitId}</div>
                  <div className="text-textSecondary text-xs mt-0.5">{alert.role}</div>
                </td>
                {config.canViewServiceIdentity && (
                  <td className="px-4 py-3 font-mono text-textSecondary">
                    {alert.serviceId}
                  </td>
                )}
                <td className="px-4 py-3">
                  <RiskBadge level={alert.stressRiskLevel} />
                </td>
                <td className="px-4 py-3 font-mono text-textSecondary">
                  {alert.riskScore}
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${
                    alert.status === 'New' ? 'bg-accent/20 text-accent' : 
                    alert.status === 'Resolved' ? 'bg-risk-low/10 text-risk-low' : 
                    'bg-surfaceHighlight text-textSecondary'
                  }`}>
                    {alert.status}
                  </span>
                </td>
              </tr>
            ))}
            {alerts.length === 0 && (
              <tr>
                <td colSpan={config.canViewServiceIdentity ? 5 : 4} className="p-0 border-none">
                  <div className="h-64">
                    <EmptyState 
                      icon={ShieldCheck} 
                      title="No Active Alerts" 
                      description="All personnel are currently below the critical stress threshold." 
                    />
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      
      {selectedAlert && (
        <AlertDetailDrawer 
          alert={selectedAlert} 
          role={role} 
          onClose={() => setSelectedAlert(null)} 
          onStatusChange={handleStatusChange} 
        />
      )}
    </div>
  );
}
