'use client';

import React, { useEffect, useState, useCallback } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import MainMetricsRow from '@/components/dashboard/MainMetricsRow';
import StressDistributionCard from '@/components/dashboard/StressDistributionCard';
import RiskDistributionCard from '@/components/dashboard/RiskDistributionCard';
import UrgentTriageQueue from '@/components/dashboard/UrgentTriageQueue';
import QuickActionHub from '@/components/dashboard/QuickActionHub';
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
  WelfareRequestOut,
} from '@/types/api';
import { getWelfareRequests } from '@/lib/welfare';
import { RefreshCw, AlertCircle, Info, ShieldCheck, Activity } from 'lucide-react';

export default function DashboardOverviewPage() {
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
      console.error('Overview telemetry load failure:', err);
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
    }, 20000);
    return () => clearInterval(interval);
  }, [loadDashboardData]);

  const criticalCount = highRiskPersonnel.filter((p) => p.latest_risk_score >= 70).length;
  const pendingWelfareCount = welfareRequests.filter((r) => r.status === 'pending').length;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Executive Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2.5">
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-textPrimary uppercase">
                Force Wellness & Readiness Overview
              </h1>
              <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-alert-sageBg text-alert-sageText border border-alert-sageBorder">
                <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
                <span>ACTIVE MONITORING</span>
              </span>
            </div>
            <p className="text-xs text-textSecondary mt-1 font-mono">
              High-level operational strain overview and immediate welfare action triage
            </p>
          </div>

          <div className="flex items-center space-x-2 self-start sm:self-auto">
            <button
              onClick={loadDashboardData}
              disabled={loading}
              className="flex items-center space-x-2 px-3 py-1.5 bg-surface hover:bg-surfaceHighlight text-textPrimary rounded-lg text-xs font-mono font-medium transition-colors border border-surfaceBorder disabled:opacity-50 shadow-xs"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>Sync Telemetry</span>
            </button>
          </div>
        </div>

        {/* Prototype Ethical Notice Banner */}
        <div className="p-3 bg-surface border border-surfaceBorder rounded-xl text-xs text-textSecondary flex items-start space-x-2.5 shadow-card">
          <Info className="w-4 h-4 text-accent shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            <strong className="text-textPrimary">Command Summary Cockpit:</strong> Synthetically augmented prototype data. AI stress classifications are non-punitive decision-support indicators designed to protect troop well-being and identify operational fatigue early.
          </p>
        </div>

        {error && (
          <div className="p-4 bg-alert-roseBg border border-alert-roseBorder rounded-xl flex items-center space-x-3 text-alert-roseText text-sm">
            <AlertCircle className="w-5 h-5 shrink-0 text-alert-rose" />
            <div>
              <p className="font-semibold">Backend Telemetry Notice</p>
              <p className="text-xs mt-0.5">{error}</p>
            </div>
          </div>
        )}

        {/* 1. Core Force KPI Metric Row */}
        <MainMetricsRow summary={summary} isLoading={loading} />

        {/* 2. Split Row: Urgent Action Queue (60%) + Stress Stance (40%) */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          <div className="lg:col-span-3">
            <UrgentTriageQueue
              highRiskAlerts={highRiskPersonnel}
              welfareRequests={welfareRequests}
              isLoading={loading}
              onRefresh={loadDashboardData}
            />
          </div>

          <div className="lg:col-span-2">
            <StressDistributionCard
              distribution={stressDist}
              totalAssessed={totalAssessed}
              isLoading={loading}
              error={error}
            />
          </div>
        </div>

        {/* 3. Operational Hubs & Deep Analytics Access */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          <div className="lg:col-span-3">
            <QuickActionHub
              urgentAlertsCount={criticalCount + pendingWelfareCount}
              recommendationsCount={summary?.active_recommendations_count || 4}
              signalsCount={criticalCount}
            />
          </div>

          <div className="lg:col-span-2">
            <RiskDistributionCard
              distribution={riskDist}
              totalAssessed={totalAssessed}
              isLoading={loading}
              error={error}
            />
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
