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
    default: 'text-accent border-surfaceHighlight bg-surfaceHighlight/50',
    low: 'text-emerald-400 border-emerald-900/30 bg-emerald-950/20',
    medium: 'text-amber-400 border-amber-900/30 bg-amber-950/20',
    high: 'text-rose-400 border-rose-900/30 bg-rose-950/20',
    accent: 'text-teal-400 border-teal-900/30 bg-teal-950/20',
  };

  return (
    <div className="bg-surface p-4 border border-surfaceHighlight rounded-lg flex items-center justify-between transition-colors hover:border-surfaceHighlight/80">
      <div>
        <p className="text-xs font-semibold text-textSecondary uppercase tracking-wider">{label}</p>
        <div className="mt-1.5 flex items-baseline space-x-2">
          <span className="text-2xl font-bold text-textPrimary font-mono">{value}</span>
          {delta !== undefined && (
            <span
              className={cn(
                'text-xs font-semibold px-1.5 py-0.5 rounded font-mono',
                delta > 0
                  ? 'bg-rose-950/60 text-rose-300 border border-rose-800/40'
                  : 'bg-emerald-950/60 text-emerald-300 border border-emerald-800/40'
              )}
            >
              {delta > 0 ? '+' : ''}
              {delta}%
            </span>
          )}
        </div>
        {subtext && <p className="text-[10px] text-textSecondary font-mono mt-1">{subtext}</p>}
      </div>
      <div className={cn('p-3 rounded border', variantStyles[variant])}>
        <Icon className="w-5 h-5" />
      </div>
    </div>
  );
}

