import React from 'react';
import { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function MetricCard({
  label,
  value,
  delta,
  icon: Icon
}: {
  label: string;
  value: string | number;
  delta?: number;
  icon: LucideIcon;
}) {
  return (
    <div className="bg-surface p-4 border-military flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-textSecondary uppercase tracking-wider">{label}</p>
        <div className="mt-1 flex items-baseline space-x-2">
          <span className="text-2xl font-bold text-textPrimary font-mono">{value}</span>
          {delta !== undefined && (
            <span className={cn(
              "text-xs font-semibold px-1.5 py-0.5 rounded",
              delta > 0 ? "bg-risk-critical/10 text-risk-critical" : delta < 0 ? "bg-risk-low/10 text-risk-low" : "text-textSecondary"
            )}>
              {delta > 0 ? '+' : ''}{delta}%
            </span>
          )}
        </div>
      </div>
      <div className="p-3 bg-surfaceHighlight rounded">
        <Icon className="w-5 h-5 text-accent" />
      </div>
    </div>
  );
}
