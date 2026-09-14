import React from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import MainMetricsRow from '@/components/dashboard/MainMetricsRow';
import RiskTrendChart from '@/components/dashboard/RiskTrendChart';
import AlertsTable from '@/components/dashboard/AlertsTable';
import UnitOverviewPanel from '@/components/dashboard/UnitOverviewPanel';
import { getUnitAggregates, getPersonnelAlerts } from '@/lib/mock-data';

export default async function DashboardPage() {
  const [aggregates, alerts] = await Promise.all([
    getUnitAggregates(),
    getPersonnelAlerts()
  ]);

  const chartTrend = aggregates.length > 0 ? aggregates[0].trend : [];
  const chartUnitName = aggregates.length > 0 ? aggregates[0].unitName : 'N/A';

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-textPrimary uppercase">Dashboard Overview</h1>
          <p className="text-sm text-textSecondary mt-1 font-mono">Personnel Stress & Welfare Monitoring</p>
        </div>

        <MainMetricsRow aggregates={aggregates} />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 h-[350px]">
            <RiskTrendChart trend={chartTrend} unitName={chartUnitName} />
          </div>

          <div className="h-[350px]">
            <UnitOverviewPanel aggregates={aggregates} />
          </div>
        </div>

        <div className="h-[450px]">
          <AlertsTable alerts={alerts} />
        </div>
      </div>
    </DashboardLayout>
  );
}
