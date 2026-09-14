import { UnitAggregates } from '@/types/dashboard';
import { PersonnelAlert } from '@/types/alerts';

export const mockUnitAggregates: UnitAggregates[] = [
  {
    unitId: 'UNIT-07B',
    unitName: '7th Battalion, Bravo Company',
    personnelStrength: 214,
    avgDutyHoursPerWeek: 52.4,
    avgConsecutiveDutyDays: 9,
    avgNightShiftsPerMonth: 6,
    avgLeaveGapDays: 143,
    annualLeaveUtilizationPct: 41,
    operationalExposureIndex: 'High',
    riskDistribution: { low: 138, moderate: 51, high: 19, critical: 6 },
    trend: [
      { date: '2026-08-03', avgWorkloadScore: 6.1, avgStressIndex: 44 },
      { date: '2026-08-10', avgWorkloadScore: 6.5, avgStressIndex: 47 },
      { date: '2026-08-17', avgWorkloadScore: 7.0, avgStressIndex: 52 },
      { date: '2026-08-24', avgWorkloadScore: 6.8, avgStressIndex: 50 },
    ],
    lastSyncedAt: '2026-09-14T06:00:00Z',
  },
  {
    unitId: 'UNIT-12A',
    unitName: '12th Battalion, Alpha Company',
    personnelStrength: 189,
    avgDutyHoursPerWeek: 46.1,
    avgConsecutiveDutyDays: 5,
    avgNightShiftsPerMonth: 3,
    avgLeaveGapDays: 88,
    annualLeaveUtilizationPct: 67,
    operationalExposureIndex: 'Medium',
    riskDistribution: { low: 151, moderate: 29, high: 7, critical: 2 },
    trend: [
      { date: '2026-08-03', avgWorkloadScore: 4.8, avgStressIndex: 31 },
      { date: '2026-08-10', avgWorkloadScore: 4.9, avgStressIndex: 32 },
      { date: '2026-08-17', avgWorkloadScore: 5.1, avgStressIndex: 33 },
      { date: '2026-08-24', avgWorkloadScore: 4.7, avgStressIndex: 30 },
    ],
    lastSyncedAt: '2026-09-14T06:00:00Z',
  },
];

export const mockPersonnelAlerts: PersonnelAlert[] = [
  {
    alertId: 'ALT-10492',
    serviceId: 'CRPF-77213-B',
    unitId: 'UNIT-07B',
    role: 'Section Commander',
    stressRiskLevel: 'Critical',
    riskScore: 91,
    riskExplanation: [
      { factor: 'Consecutive duty days 40% above unit average', contribution: 0.34 },
      { factor: 'Leave gap of 187 days since last sanctioned leave', contribution: 0.29 },
      { factor: 'Average sleep 4.6 hrs/night over trailing 4 weeks', contribution: 0.22 },
      { factor: 'Three night shifts in the last 7 days', contribution: 0.15 },
    ],
    welfareRecommendation: [
      'Schedule welfare interview within 48 hours',
      'Recommend sanctioned leave block (5+ days) within 2 weeks',
      'Flag for rotation out of night-shift roster next cycle',
    ],
    contributingMetrics: {
      dutyHoursPerWeek: 61,
      consecutiveDutyDays: 14,
      nightShiftsPerMonth: 9,
      leaveGapDays: 187,
      sleepHours: 4.6,
      workLifeBalanceScore: 1,
    },
    flaggedAt: '2026-09-13T21:15:00Z',
    status: 'New',
  },
  {
    alertId: 'ALT-10488',
    serviceId: 'CRPF-51042-C',
    unitId: 'UNIT-07B',
    role: 'Constable',
    stressRiskLevel: 'High',
    riskScore: 74,
    riskExplanation: [
      { factor: 'Duty hours 22% above unit average', contribution: 0.31 },
      { factor: 'Work-life balance self-report at lowest band', contribution: 0.27 },
      { factor: 'Two transfers in the last 12 months', contribution: 0.19 },
    ],
    welfareRecommendation: [
      'Peer-support check-in this week',
      'Review transfer cadence with unit HR',
    ],
    contributingMetrics: {
      dutyHoursPerWeek: 58,
      consecutiveDutyDays: 8,
      nightShiftsPerMonth: 5,
      leaveGapDays: 96,
      sleepHours: 5.4,
      workLifeBalanceScore: 2,
    },
    flaggedAt: '2026-09-12T09:40:00Z',
    status: 'Acknowledged',
  },
];

// Simulated async fetchers — swap the body for a real API call later.
// Component code should never import the arrays above directly.
export async function getUnitAggregates(): Promise<UnitAggregates[]> {
  await new Promise((r) => setTimeout(r, 400));
  return mockUnitAggregates;
}

export async function getPersonnelAlerts(): Promise<PersonnelAlert[]> {
  await new Promise((r) => setTimeout(r, 500));
  return mockPersonnelAlerts;
}
