'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { getWelfareAlerts } from '@/lib/alerts';
import { WelfareAlertOut } from '@/types/api';
import { AlertCircle, AlertTriangle, Info, Bell, CheckCircle, Clock } from 'lucide-react';
import Link from 'next/link';

export default function WelfareAlertsPanel() {
  const [alerts, setAlerts] = useState<WelfareAlertOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAlerts = useCallback(async () => {
    try {
      setError(null);
      const data = await getWelfareAlerts();
      setAlerts(data.filter(a => a.status !== 'RESOLVED' && a.status !== 'DISMISSED'));
    } catch (err: any) {
      console.error('Failed to load welfare alerts', err);
      setError(err?.message || 'Unable to load active welfare review signals.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAlerts();
  }, [loadAlerts]);

  if (loading) {
    return (
      <div className="bg-surface p-5 border-military animate-pulse">
        <div className="h-4 bg-surfaceHighlight w-1/3 mb-4 rounded"></div>
        <div className="space-y-3">
          <div className="h-10 bg-surfaceHighlight/50 rounded"></div>
          <div className="h-10 bg-surfaceHighlight/50 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-surface p-5 border-military">
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-xs uppercase tracking-widest font-semibold text-textSecondary flex items-center space-x-2">
            <Bell className="w-4 h-4 text-accent" />
            <span>Active Welfare Review Signals</span>
          </h3>
        </div>
        <div className="p-3 bg-red-950/20 border border-red-900/40 rounded text-center">
          <AlertCircle className="w-5 h-5 text-red-400 mx-auto mb-1" />
          <p className="text-xs text-red-300 font-mono">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-surface p-5 border-military">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-xs uppercase tracking-widest font-semibold text-textSecondary flex items-center space-x-2">
          <Bell className="w-4 h-4 text-accent" />
          <span>Active Welfare Review Signals</span>
        </h3>
        <span className="text-[10px] font-mono text-textSecondary bg-surfaceHighlight px-2 py-0.5 rounded">
          {alerts.length} signals
        </span>
      </div>

      {alerts.length === 0 ? (
        <div className="text-center py-6">
          <CheckCircle className="w-8 h-8 text-emerald-500/50 mx-auto mb-2" />
          <p className="text-xs text-textSecondary">No active welfare alerts requiring review.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <Link key={alert.id} href={`/personnel/${alert.personnel_id}`}>
              <div className="p-3 bg-surfaceHighlight/20 hover:bg-surfaceHighlight/40 transition-colors rounded border border-surfaceHighlight flex items-start space-x-3 cursor-pointer mb-2">
                <div className="mt-0.5">
                  {alert.severity === 'URGENT_REVIEW' ? (
                    <AlertCircle className="w-4 h-4 text-red-500" />
                  ) : alert.severity === 'HIGH_PRIORITY' ? (
                    <AlertTriangle className="w-4 h-4 text-amber-500" />
                  ) : alert.severity === 'ATTENTION' ? (
                    <AlertTriangle className="w-4 h-4 text-blue-400" />
                  ) : (
                    <Info className="w-4 h-4 text-emerald-400" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between items-start mb-1">
                    <span className="text-xs font-bold font-mono text-textPrimary">P-{alert.personnel_id}</span>
                    <span className={`text-[9px] uppercase font-bold px-1.5 py-0.5 rounded ${
                      alert.status === 'OPEN' ? 'bg-red-950/40 text-red-400' :
                      alert.status === 'ACKNOWLEDGED' ? 'bg-blue-950/40 text-blue-400' :
                      alert.status === 'UNDER_REVIEW' ? 'bg-amber-950/40 text-amber-400' :
                      alert.status === 'INTERVENTION_PLANNED' ? 'bg-purple-950/40 text-purple-400' :
                      'bg-emerald-950/40 text-emerald-400'
                    }`}>
                      {alert.status.replace('_', ' ')}
                    </span>
                  </div>
                  <p className="text-[11px] text-textSecondary font-semibold mb-0.5">
                    {alert.alert_type.replace(/_/g, ' ')}
                  </p>
                  <p className="text-[10px] text-textSecondary line-clamp-1">
                    {alert.trigger_reason}
                  </p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
