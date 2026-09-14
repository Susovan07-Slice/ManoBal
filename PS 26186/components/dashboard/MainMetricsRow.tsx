import React from 'react';
import MetricCard from './MetricCard';
import { UnitAggregates } from '@/types/dashboard';
import { Users, Activity, TrendingUp, ShieldAlert } from 'lucide-react';

export default function MainMetricsRow({ aggregates }: { aggregates: UnitAggregates[] }) {
  const totalPersonnel = aggregates.reduce((sum, unit) => sum + unit.personnelStrength, 0);
  
  // Sum high and critical risk personnel across units
  const activeAlerts = aggregates.reduce((sum, unit) => sum + unit.riskDistribution.high + unit.riskDistribution.critical, 0);
  
  // Calculate average stress index from latest trend points
  let currentStress = 0;
  let prevStress = 0;
  aggregates.forEach(unit => {
    if (unit.trend.length >= 2) {
      currentStress += unit.trend[unit.trend.length - 1].avgStressIndex;
      prevStress += unit.trend[unit.trend.length - 2].avgStressIndex;
    }
  });
  
  const unitCount = aggregates.length || 1;
  const avgStressValue = Math.round(currentStress / unitCount);
  const avgDelta = Math.round(((currentStress - prevStress) / unitCount) * 10) / 10;
  
  // Operational exposure: if any unit is high, mark overall as High
  const highExposure = aggregates.some(u => u.operationalExposureIndex === 'High');

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <MetricCard label="Total Strength" value={totalPersonnel} icon={Users} />
      <MetricCard label="Active Alerts" value={activeAlerts} icon={ShieldAlert} />
      <MetricCard label="Avg Stress Idx" value={avgStressValue} delta={avgDelta} icon={Activity} />
      <MetricCard label="Op Exposure" value={highExposure ? 'HIGH' : 'MODERATE'} icon={TrendingUp} />
    </div>
  );
}
