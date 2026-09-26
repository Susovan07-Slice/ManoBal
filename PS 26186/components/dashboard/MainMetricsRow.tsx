import React from 'react';
import MetricCard from './MetricCard';
import { Users, Activity, ShieldAlert, HeartPulse, ShieldCheck, AlertCircle } from 'lucide-react';
import { DashboardSummary } from '@/types/api';

interface MainMetricsRowProps {
  summary: DashboardSummary | null;
  isLoading?: boolean;
}

export default function MainMetricsRow({ summary, isLoading = false }: MainMetricsRowProps) {
  if (isLoading || !summary) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div
            key={i}
            className="bg-surface p-4 border border-surfaceHighlight rounded-lg flex items-center justify-between animate-pulse h-24"
          >
            <div className="space-y-2">
              <div className="h-3 w-20 bg-surfaceHighlight rounded" />
              <div className="h-6 w-10 bg-surfaceHighlight rounded" />
            </div>
            <div className="h-10 w-10 bg-surfaceHighlight rounded" />
          </div>
        ))}
      </div>
    );
  }

  const highRiskPct =
    summary.assessed_personnel > 0
      ? Math.round((summary.high_risk / summary.assessed_personnel) * 100)
      : 0;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      <MetricCard
        label="Total Force"
        value={summary.total_personnel}
        icon={Users}
        variant="default"
        subtext="Enlisted personnel"
      />
      <MetricCard
        label="Low Risk (Routine)"
        value={summary.low_risk}
        icon={ShieldCheck}
        variant="low"
        subtext="Nominal stress level"
      />
      <MetricCard
        label="Medium Risk"
        value={summary.medium_risk}
        icon={AlertCircle}
        variant="medium"
        subtext="Preventive fatigue tier"
      />
      <MetricCard
        label="High Risk (Priority)"
        value={summary.high_risk}
        delta={highRiskPct}
        icon={ShieldAlert}
        variant="high"
        subtext="Urgent intervention"
      />
      <MetricCard
        label="Assessed Force"
        value={summary.assessed_personnel}
        icon={Activity}
        variant="accent"
        subtext="AI telemetry active"
      />
      <MetricCard
        label="Pending Recs"
        value={summary.pending_recommendations}
        icon={HeartPulse}
        variant="medium"
        subtext="Supportive actions"
      />
    </div>
  );
}

