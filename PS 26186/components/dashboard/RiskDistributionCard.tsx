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
      <div className="h-full w-full bg-surface border border-surfaceBorder rounded-xl p-5 flex flex-col justify-center items-center min-h-[340px] shadow-card">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin mb-3" />
        <span className="text-xs font-mono text-textSecondary uppercase tracking-widest">
          Loading Risk Telemetry...
        </span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full w-full bg-surface border border-[#E8B4B4] rounded-xl p-5 flex flex-col justify-center items-center min-h-[340px] text-center shadow-card">
        <AlertTriangle className="w-8 h-8 text-[#C26D6D] mb-2" />
        <p className="text-sm font-semibold text-[#964747]">Risk Telemetry Unavailable</p>
        <p className="text-xs text-textSecondary mt-1 max-w-xs">{error}</p>
      </div>
    );
  }

  const routineItem = distribution.find((d) => d.label === 'Routine') || { count: 0, percentage: 0 };
  const preventiveItem = distribution.find((d) => d.label === 'Preventive') || { count: 0, percentage: 0 };
  const priorityItem = distribution.find((d) => d.label === 'Priority') || { count: 0, percentage: 0 };

  return (
    <div className="h-full w-full bg-surface border border-surfaceBorder rounded-xl p-5 flex flex-col justify-between shadow-card">
      <div>
        <div className="flex justify-between items-center mb-3">
          <div className="flex items-center space-x-2">
            <Shield className="w-4 h-4 text-accent" />
            <h3 className="text-sm uppercase tracking-wider font-semibold text-textPrimary">
              Operational Welfare Priority Tiers
            </h3>
          </div>
          <span className="text-xs font-mono text-accent bg-accent/10 border border-accent/25 px-2.5 py-0.5 rounded-md font-semibold">
            Force Stance
          </span>
        </div>
        <p className="text-xs text-textSecondary mb-4">
          Hierarchical intervention readiness based on continuous fatigue risk indices.
        </p>

        {/* Stacked Force Capacity Bar */}
        <div className="mb-5 space-y-1.5">
          <div className="h-3.5 w-full flex rounded-full overflow-hidden bg-surfaceHighlight p-0.5 border border-surfaceBorder">
            {totalAssessed > 0 ? (
              <>
                <div
                  style={{ width: `${routineItem.percentage}%` }}
                  className="bg-[#7BA083] hover:opacity-90 transition-all cursor-pointer rounded-l-full"
                  title={`Routine: ${routineItem.count} (${routineItem.percentage}%)`}
                />
                <div
                  style={{ width: `${preventiveItem.percentage}%` }}
                  className="bg-[#D99B5C] hover:opacity-90 transition-all cursor-pointer"
                  title={`Preventive: ${preventiveItem.count} (${preventiveItem.percentage}%)`}
                />
                <div
                  style={{ width: `${priorityItem.percentage}%` }}
                  className="bg-[#C26D6D] hover:opacity-90 transition-all cursor-pointer rounded-r-full"
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
          <div className="p-3 bg-[#EEF6F2]/70 rounded-lg border border-[#BBD9C7] flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="w-2.5 h-2.5 rounded-full bg-[#7BA083] shrink-0" />
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

          <div className="p-3 bg-[#FDF6EE]/70 rounded-lg border border-[#F3D2AE] flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="w-2.5 h-2.5 rounded-full bg-[#D99B5C] shrink-0" />
              <div>
                <span className="text-xs font-semibold text-textPrimary block">Preventive Stance (40–69)</span>
                <span className="text-[11px] text-textSecondary">Night-shift rotation & leave gap monitoring</span>
              </div>
            </div>
            <div className="text-right">
              <span className="font-mono text-sm font-bold text-[#8E5B23]">{preventiveItem.count}</span>
              <span className="text-[10px] text-[#8E5B23]/80 font-mono block">({preventiveItem.percentage}%)</span>
            </div>
          </div>

          <div className="p-3 bg-[#FAF0F0] rounded-lg border border-[#E8B4B4] flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="w-2.5 h-2.5 rounded-full bg-[#C26D6D] shrink-0" />
              <div>
                <span className="text-xs font-semibold text-[#964747] block">Priority Intervention (≥70)</span>
                <span className="text-[11px] text-[#964747]/80">Welfare counselor & command roster review</span>
              </div>
            </div>
            <div className="text-right">
              <span className="font-mono text-sm font-bold text-[#964747]">{priorityItem.count}</span>
              <span className="text-[10px] text-[#964747]/80 font-mono block">({priorityItem.percentage}%)</span>
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
