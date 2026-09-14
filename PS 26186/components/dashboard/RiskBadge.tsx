import React from 'react';
import { StressRiskLevel } from '@/types/alerts';
import { ShieldCheck, AlertTriangle, AlertOctagon, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

const badgeStyles: Record<StressRiskLevel, { bg: string, text: string, icon: any }> = {
  Low: { bg: 'bg-risk-low/10', text: 'text-risk-low', icon: ShieldCheck },
  Moderate: { bg: 'bg-risk-moderate/10', text: 'text-risk-moderate', icon: AlertCircle },
  High: { bg: 'bg-risk-high/10', text: 'text-risk-high', icon: AlertTriangle },
  Critical: { bg: 'bg-risk-critical/10', text: 'text-risk-critical', icon: AlertOctagon },
};

export default function RiskBadge({ level }: { level: StressRiskLevel }) {
  const { bg, text, icon: Icon } = badgeStyles[level];
  return (
    <span className={cn('inline-flex items-center px-2 py-1 rounded text-xs font-semibold', bg, text)}>
      <Icon className="w-3.5 h-3.5 mr-1" />
      {level}
    </span>
  );
}
