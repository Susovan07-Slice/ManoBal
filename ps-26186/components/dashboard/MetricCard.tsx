import React from 'react';
import { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function MetricCard({
  label,
  value,
  delta,
  icon: Icon,
  variant = 'default',
  subtext,
}: {
  label: string;
  value: string | number;
  delta?: number;
  icon: LucideIcon;
  variant?: 'default' | 'low' | 'medium' | 'high' | 'accent';
  subtext?: string;
}) {
  const variantStyles = {
    default: 'text-accent border-surfaceBorder bg-accent/10',
    low: 'text-[#2D6346] border-[#BBD9C7] bg-[#EEF6F2]',
    medium: 'text-[#8E5B23] border-[#F3D2AE] bg-[#FDF6EE]',
    high: 'text-[#964747] border-[#E8B4B4] bg-[#FAF0F0]',
    accent: 'text-[#4F6E56] border-[#D0E1D4] bg-[#E6EFE8]',
  };

  return (
    <div className="bg-surface p-4 border border-surfaceBorder rounded-xl flex items-center justify-between transition-all hover:border-accent/50 shadow-card">
      <div>
        <p className="text-xs font-semibold text-textSecondary uppercase tracking-wider">{label}</p>
        <div className="mt-1.5 flex items-baseline space-x-2">
          <span className="text-2xl font-bold text-textPrimary font-mono">{value}</span>
          {delta !== undefined && (
            <span
              className={cn(
                'text-xs font-semibold px-1.5 py-0.5 rounded font-mono',
                delta > 0
                  ? 'bg-[#FAF0F0] text-[#964747] border border-[#E8B4B4]'
                  : 'bg-[#EEF6F2] text-[#2D6346] border border-[#BBD9C7]'
              )}
            >
              {delta > 0 ? '+' : ''}
              {delta}%
            </span>
          )}
        </div>
        {subtext && <p className="text-[10px] text-textSecondary font-mono mt-1">{subtext}</p>}
      </div>
      <div className={cn('p-3 rounded-lg border', variantStyles[variant])}>
        <Icon className="w-5 h-5" />
      </div>
    </div>
  );
}
