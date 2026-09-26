'use client';

import React, { useEffect, useState, useCallback } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import MainMetricsRow from '@/components/dashboard/MainMetricsRow';
import StressDistributionCard from '@/components/dashboard/StressDistributionCard';
import RiskDistributionCard from '@/components/dashboard/RiskDistributionCard';
import AlertsTable from '@/components/dashboard/AlertsTable';
import {
  getDashboardSummary,
  getStressDistribution,
  getRiskDistribution,
  getHighRiskPersonnel,
} from '@/lib/dashboard';
import {
  DashboardSummary,
  DistributionItem,
  HighRiskPersonnelItem,
} from '@/types/api';
import { WelfareRequestOut } from '@/types/api';
import { getWelfareRequests } from '@/lib/welfare';
import { RefreshCw, AlertCircle, ShieldAlert, Info } from 'lucide-react';

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [stressDist, setStressDist] = useState<DistributionItem[]>([]);
  const [riskDist, setRiskDist] = useState<DistributionItem[]>([]);
  const [totalAssessed, setTotalAssessed] = useState<number>(0);
  const [highRiskPersonnel, setHighRiskPersonnel] = useState<HighRiskPersonnelItem[]>([]);
  const [welfareRequests, setWelfareRequests] = useState<WelfareRequestOut[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboardData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [sumRes, stressRes, riskRes, highRiskRes, welfareRes] = await Promise.all([
        getDashboardSummary(),
        getStressDistribution(),
        getRiskDistribution(),
        getHighRiskPersonnel(),
        getWelfareRequests().catch((err) => {
          console.warn('Could not fetch welfare requests:', err);
          return [];
        }),
      ]);

      setSummary(sumRes);
      setStressDist(stressRes.distribution || []);
      setRiskDist(riskRes.distribution || []);
      setTotalAssessed(stressRes.total_assessed || 0);
      setHighRiskPersonnel(highRiskRes || []);
      setWelfareRequests(welfareRes || []);
    } catch (err: any) {
      console.error('Dashboard load failure:', err);
      setError(err?.message || 'Unable to load telemetry from backend.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(() => {
      Promise.all([
        getDashboardSummary(),
        getStressDistribution(),
        getRiskDistribution(),
        getHighRiskPersonnel(),
        getWelfareRequests().catch(() => []),
      ])
        .then(([sumRes, stressRes, riskRes, highRiskRes, welfareRes]) => {
          setSummary(sumRes);
          setStressDist(stressRes.distribution || []);
          setRiskDist(riskRes.distribution || []);
          setTotalAssessed(stressRes.total_assessed || 0);
          setHighRiskPersonnel(highRiskRes || []);
          setWelfareRequests(welfareRes || []);
        })
        .catch((err) => {
          console.warn('Background telemetry sync failure:', err);
        });
    }, 15000);
    return () => clearInterval(interval);
  }, [loadDashboardData]);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-2xl font-bold tracking-tight text-textPrimary uppercase">
                Operational Stress & Welfare Dashboard
              </h1>
              <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-emerald-950/60 text-emerald-400 border border-emerald-800/40">
                LIVE TELEMETRY
              </span>
            </div>
            <p className="text-xs text-textSecondary mt-1 font-mono">
              Live AI-driven predictive health & strain telemetry overview
            </p>
          </div>

          <button
            onClick={loadDashboardData}
            disabled={loading}
            className="flex items-center space-x-2 px-3 py-1.5 bg-surfaceHighlight hover:bg-surfaceHighlight/80 text-textPrimary rounded-lg text-xs font-mono font-medium transition-colors border border-surfaceHighlight self-start sm:self-auto disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Telemetry</span>
          </button>
        </div>

        {/* Prototype Ethical Notice Banner */}
        <div className="p-3 bg-surfaceHighlight/40 border border-surfaceHighlight rounded-lg text-xs text-textSecondary flex items-start space-x-2.5">
          <Info className="w-4 h-4 text-accent shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            <strong className="text-textPrimary">Research & Demonstration Notice:</strong> Synthetically augmented prototype data; not actual CRPF personnel data. AI-generated stress classifications and risk scores are non-punitive decision-support indicators and are not medical diagnoses.
          </p>
        </div>

        {error && (
          <div className="p-4 bg-red-950/40 border border-red-800/60 rounded-lg flex items-center space-x-3 text-red-200 text-sm">
            <AlertCircle className="w-5 h-5 shrink-0 text-red-400" />
            <div>
              <p className="font-semibold">Backend Communication Error</p>
              <p className="text-xs text-red-300 mt-0.5">{error}</p>
            </div>
          </div>
        )}

        {/* Real KPI metric cards (Section 3) */}
        <MainMetricsRow summary={summary} isLoading={loading} />

        {/* Dedicated Visualizations for Stress & Risk Distribution (Sections 4 & 5) */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6" id="telemetry-distributions">
          <div className="min-h-[350px]">
            <StressDistributionCard
              distribution={stressDist}
              totalAssessed={totalAssessed}
              isLoading={loading}
              error={error}
            />
          </div>

          <div className="min-h-[350px]">
            <RiskDistributionCard
              distribution={riskDist}
              totalAssessed={totalAssessed}
              isLoading={loading}
              error={error}
            />
          </div>
        </div>

        {/* High-Risk Personnel Intervention & Alerts Table (Section 6) */}
        <div className="min-h-[420px]" id="risk-alerts-table">
          <AlertsTable
            alerts={highRiskPersonnel}
            welfareRequests={welfareRequests}
            isLoading={loading}
            onRefresh={loadDashboardData}
          />
        </div>
      </div>
    </DashboardLayout>
  );
}
