export interface TrendPoint {
  date: string;               // ISO date, weekly granularity
  avgWorkloadScore: number;   // 0-10
  avgStressIndex: number;     // 0-100
}

export interface RiskDistribution {
  low: number;
  moderate: number;
  high: number;
  critical: number;
}

export interface UnitAggregates {
  unitId: string;
  unitName: string;
  personnelStrength: number;
  avgDutyHoursPerWeek: number;
  avgConsecutiveDutyDays: number;
  avgNightShiftsPerMonth: number;
  avgLeaveGapDays: number;
  annualLeaveUtilizationPct: number;              // derived: leaves taken / entitled
  operationalExposureIndex: 'Low' | 'Medium' | 'High';
  riskDistribution: RiskDistribution;
  trend: TrendPoint[];
  lastSyncedAt: string;                            // ISO timestamp
}
