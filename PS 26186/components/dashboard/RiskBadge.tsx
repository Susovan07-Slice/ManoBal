import React from 'react';
import { StressRiskLevel } from '@/types/alerts';
import { ShieldCheck, AlertTriangle, AlertOctagon, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

const badgeStyles: Record<StressRiskLevel, { bg: string; text: string; icon: any }> = {
  Low: { bg: 'bg-[#EEF6F2] border border-[#BBD9C7]', text: 'text-[#2D6346]', icon: ShieldCheck },
  Medium: { bg: 'bg-[#FDF6EE] border border-[#F3D2AE]', text: 'text-[#8E5B23]', icon: AlertCircle },
  Moderate: { bg: 'bg-[#FDF6EE] border border-[#F3D2AE]', text: 'text-[#8E5B23]', icon: AlertCircle },
  High: { bg: 'bg-[#FDF2EC] border border-[#F1C5B3]', text: 'text-[#8F4B33]', icon: AlertTriangle },
  Critical: { bg: 'bg-[#FAF0F0] border border-[#E8B4B4]', text: 'text-[#964747]', icon: AlertOctagon },
};

export default function RiskBadge({ level }: { level?: string | StressRiskLevel | null }) {
  const normLevel: StressRiskLevel = 
    level === 'Medium' || level === 'Moderate'
      ? 'Medium'
      : level === 'High'
      ? 'High'
      : level === 'Critical'
      ? 'Critical'
      : 'Low';

  const style = badgeStyles[normLevel] || badgeStyles.Low;
  const Icon = style.icon;

  return (
    <span className={cn('inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold font-mono', style.bg, style.text)}>
      <Icon className="w-3.5 h-3.5 mr-1" />
      {level || 'Low'}
    </span>
  );
}
