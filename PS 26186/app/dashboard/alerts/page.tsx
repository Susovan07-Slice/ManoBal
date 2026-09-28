'use client';

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import DashboardLayout from '@/components/layout/DashboardLayout';
import AlertsTable from '@/components/dashboard/AlertsTable';
import WelfareAlertsPanel from '@/components/dashboard/WelfareAlertsPanel';
import { getHighRiskPersonnel } from '@/lib/dashboard';
import { getWelfareRequests } from '@/lib/welfare';
import { HighRiskPersonnelItem, WelfareRequestOut } from '@/types/api';
import { Bell, RefreshCw, AlertCircle, ArrowLeft } from 'lucide-react';

export default function AlertsPage() {
  const [highRiskPersonnel, setHighRiskPersonnel] = useState<HighRiskPersonnelItem[]>([]);
  const [welfareRequests, setWelfareRequests] = useState<WelfareRequestOut[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadAlertsData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [highRiskRes, welfareRes] = await Promise.all([
        getHighRiskPersonnel(),
        getWelfareRequests().catch((err) => {
          console.warn('Could not fetch welfare requests:', err);
          return [];
        }),
      ]);
      setHighRiskPersonnel(highRiskRes || []);
      setWelfareRequests(welfareRes || []);
    } catch (err: any) {
      console.error('Failed to load alerts data:', err);
      setError(err?.message || 'Unable to load alert telemetry.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAlertsData();
  }, [loadAlertsData]);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Navigation & Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center space-x-3">
            <Link
              href="/dashboard"
              className="p-2 bg-surfaceHighlight hover:bg-surfaceHighlight/80 rounded-xl text-textSecondary hover:text-textPrimary transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-xl font-bold tracking-tight text-textPrimary uppercase">
                  Welfare Alerts & Inquiries
                </h1>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-alert-roseBg text-alert-roseText border border-alert-roseBorder">
                  Active Triage
                </span>
              </div>
              <p className="text-xs text-textSecondary mt-0.5 font-mono">
                Personnel stress escalation flags, urgent assistance requests, and resolution tracking
              </p>
            </div>
          </div>

          <button
            onClick={loadAlertsData}
            disabled={loading}
            className="flex items-center space-x-2 px-3 py-1.5 bg-surface hover:bg-surfaceHighlight text-textPrimary rounded-lg text-xs font-mono font-medium transition-colors border border-surfaceBorder self-start sm:self-auto disabled:opacity-50 shadow-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Alerts</span>
          </button>
        </div>

        {error && (
          <div className="p-4 bg-alert-roseBg border border-alert-roseBorder rounded-xl flex items-center space-x-3 text-alert-roseText text-sm">
            <AlertCircle className="w-5 h-5 shrink-0 text-alert-rose" />
            <div>
              <p className="font-semibold">Alerts Service Notice</p>
              <p className="text-xs mt-0.5">{error}</p>
            </div>
          </div>
        )}

        {/* Welfare Alerts Overview Panel */}
        <WelfareAlertsPanel />

        {/* Detailed High-Risk Personnel & Jawan Request Processing Table */}
        <div className="min-h-[460px]">
          <AlertsTable
            alerts={highRiskPersonnel}
            welfareRequests={welfareRequests}
            isLoading={loading}
            onRefresh={loadAlertsData}
          />
        </div>
      </div>
    </DashboardLayout>
  );
}
