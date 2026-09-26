'use client';

import React from 'react';
import { DistributionItem } from '@/types/api';
import { Shield, ShieldAlert, AlertTriangle, ShieldCheck } from 'lucide-react';

interface RiskDistributionCardProps {
  distribution: DistributionItem[];
  totalAssessed: number;
  isLoading?: boolean;
  error?: string | null;
}

export default function RiskDistributionCard({
  distribution,
  totalAssessed,
  isLoading = false,
  error = null,
}: RiskDistributionCardProps) {
  if (isLoading) {
    return (
      <div className="h-full w-full bg-surface border border-surfaceHighlight rounded-lg p-5 flex flex-col justify-center items-center min-h-[340px]">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin mb-3" />
        <span className="text-xs font-mono text-textSecondary uppercase tracking-widest">
          Loading Risk Telemetry...
        </span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full w-full bg-surface border border-red-900/40 rounded-lg p-5 flex flex-col justify-center items-center min-h-[340px] text-center">
        <AlertTriangle className="w-8 h-8 text-rose-400 mb-2" />
        <p className="text-sm font-semibold text-rose-300">Risk Telemetry Unavailable</p>
        <p className="text-xs text-textSecondary mt-1 max-w-xs">{error}</p>
      </div>
    );
  }

  const routineItem = distribution.find((d) => d.label === 'Routine') || { count: 0, percentage: 0 };
  const preventiveItem = distribution.find((d) => d.label === 'Preventive') || { count: 0, percentage: 0 };
  const priorityItem = distribution.find((d) => d.label === 'Priority') || { count: 0, percentage: 0 };

  return (
    <div className="h-full w-full bg-surface border border-surfaceHighlight rounded-lg p-5 flex flex-col justify-between">
      <div>
        <div className="flex justify-between items-center mb-3">
          <div className="flex items-center space-x-2">
            <Shield className="w-4 h-4 text-accent" />
            <h3 className="text-sm uppercase tracking-wider font-semibold text-textPrimary">
              Operational Welfare Priority Tiers
            </h3>
          </div>
          <span className="text-xs font-mono text-accent bg-surfaceHighlight px-2.5 py-0.5 rounded">
            Force Stance
          </span>
        </div>
        <p className="text-xs text-textSecondary mb-4">
          Hierarchical intervention readiness based on continuous fatigue risk indices.
        </p>

        {/* Stacked Force Capacity Bar */}
        <div className="mb-5 space-y-1.5">
          <div className="h-4 w-full flex rounded-lg overflow-hidden bg-surfaceHighlight">
            {totalAssessed > 0 ? (
              <>
                <div
                  style={{ width: `${routineItem.percentage}%` }}
                  className="bg-emerald-500 hover:brightness-110 transition-all cursor-pointer"
                  title={`Routine: ${routineItem.count} (${routineItem.percentage}%)`}
                />
                <div
                  style={{ width: `${preventiveItem.percentage}%` }}
                  className="bg-amber-500 hover:brightness-110 transition-all cursor-pointer"
                  title={`Preventive: ${preventiveItem.count} (${preventiveItem.percentage}%)`}
                />
                <div
                  style={{ width: `${priorityItem.percentage}%` }}
                  className="bg-rose-500 hover:brightness-110 transition-all cursor-pointer"
                  title={`Priority: ${priorityItem.count} (${priorityItem.percentage}%)`}
                />
              </>
            ) : (
              <div className="w-full bg-surfaceHighlight flex items-center justify-center text-[10px] text-textSecondary">
                Awaiting Assessments
              </div>
            )}
          </div>
          <div className="flex justify-between text-[10px] font-mono text-textSecondary px-1">
            <span>Routine ({routineItem.percentage}%)</span>
            <span>Preventive ({preventiveItem.percentage}%)</span>
            <span>Priority ({priorityItem.percentage}%)</span>
          </div>
        </div>

        {/* Tier Cards with Operational Context */}
        <div className="space-y-2.5">
          <div className="p-3 bg-surfaceHighlight/30 rounded-lg border border-surfaceHighlight flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 shrink-0" />
              <div>
                <span className="text-xs font-semibold text-textPrimary block">Routine Stance (&lt;40)</span>
                <span className="text-[11px] text-textSecondary">Standard duty cycle & nominal rest periods</span>
              </div>
            </div>
            <div className="text-right">
              <span className="font-mono text-sm font-bold text-textPrimary">{routineItem.count}</span>
              <span className="text-[10px] text-textSecondary font-mono block">({routineItem.percentage}%)</span>
            </div>
          </div>

          <div className="p-3 bg-surfaceHighlight/30 rounded-lg border border-surfaceHighlight flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="w-2.5 h-2.5 rounded-full bg-amber-500 shrink-0" />
              <div>
                <span className="text-xs font-semibold text-textPrimary block">Preventive Stance (40–69)</span>
                <span className="text-[11px] text-textSecondary">Night-shift rotation & leave gap monitoring</span>
              </div>
            </div>
            <div className="text-right">
              <span className="font-mono text-sm font-bold text-amber-400">{preventiveItem.count}</span>
              <span className="text-[10px] text-amber-400/80 font-mono block">({preventiveItem.percentage}%)</span>
            </div>
          </div>

          <div className="p-3 bg-rose-950/20 rounded-lg border border-rose-900/30 flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="w-2.5 h-2.5 rounded-full bg-rose-500 shrink-0" />
              <div>
                <span className="text-xs font-semibold text-rose-300 block">Priority Intervention (≥70)</span>
                <span className="text-[11px] text-rose-300/70">Welfare counselor & command roster review</span>
              </div>
            </div>
            <div className="text-right">
              <span className="font-mono text-sm font-bold text-rose-400">{priorityItem.count}</span>
              <span className="text-[10px] text-rose-300 font-mono block">({priorityItem.percentage}%)</span>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-surfaceHighlight text-[11px] text-textSecondary font-mono flex items-center justify-between">
        <span>Risk Index: [0–100] Continuous</span>
        <span>Non-Punitive Support</span>
      </div>
    </div>
  );
}
