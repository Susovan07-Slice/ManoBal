export type StressRiskLevel = 'Low' | 'Moderate' | 'High' | 'Critical';

export interface RiskFactor {
  factor: string;         // human-readable, e.g. "Consecutive duty days 40% above unit average"
  contribution: number;   // relative weight 0-1, from model explainability output
}

export interface PersonnelAlert {
  alertId: string;
  serviceId: string;       // masked service identifier — see RBAC note in Phase 3
  unitId: string;
  role: string;            // duty role, e.g. "Section Commander", "Constable"
  stressRiskLevel: StressRiskLevel;
  riskScore: number;       // 0-100 model output
  riskExplanation: RiskFactor[];
  welfareRecommendation: string[];
  contributingMetrics: {
    dutyHoursPerWeek: number;
    consecutiveDutyDays: number;
    nightShiftsPerMonth: number;
    leaveGapDays: number;
    sleepHours: number;
    workLifeBalanceScore: number;   // 1-4 scale
  };
  flaggedAt: string;        // ISO timestamp
  status: 'New' | 'Acknowledged' | 'Under Review' | 'Resolved';
}
