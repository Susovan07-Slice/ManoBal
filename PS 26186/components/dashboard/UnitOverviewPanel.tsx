import React from 'react';
import { DistributionItem } from '@/types/api';

interface UnitOverviewPanelProps {
  distribution: DistributionItem[];
  totalAssessed: number;
  isLoading?: boolean;
}

export default function UnitOverviewPanel({
  distribution,
  totalAssessed,
  isLoading = false
}: UnitOverviewPanelProps) {
  if (isLoading) {
    return (
      <div className="h-full w-full bg-surface border border-surfaceBorder rounded-xl p-4 flex flex-col justify-center items-center shadow-card">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin mb-2" />
        <span className="text-xs font-mono text-textSecondary uppercase tracking-widest">
          Loading Risk Breakdown...
        </span>
      </div>
    );
  }

  const routineItem = distribution.find(d => d.label === 'Routine') || { count: 0, percentage: 0 };
  const preventiveItem = distribution.find(d => d.label === 'Preventive') || { count: 0, percentage: 0 };
  const priorityItem = distribution.find(d => d.label === 'Priority') || { count: 0, percentage: 0 };

  return (
    <div className="h-full w-full bg-surface border border-surfaceBorder rounded-xl p-4 flex flex-col justify-between shadow-card">
      <div>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-sm uppercase tracking-widest font-semibold text-textSecondary">
            Welfare Intervention Tiers
          </h3>
          <span className="font-mono text-xs text-textSecondary">{totalAssessed} Assessed</span>
        </div>

        {/* Stacked bar representing the entire force */}
        <div className="mb-6 space-y-1.5">
          <div className="h-3.5 w-full flex rounded-full overflow-hidden bg-surfaceHighlight p-0.5 border border-surfaceBorder">
            {totalAssessed > 0 ? (
              <>
                <div 
                  style={{ width: `${routineItem.percentage}%` }} 
                  className="bg-risk-low hover:opacity-90 transition-all cursor-pointer rounded-l-full" 
                  title={`Routine: ${routineItem.count} (${routineItem.percentage}%)`} 
                />
                <div 
                  style={{ width: `${preventiveItem.percentage}%` }} 
                  className="bg-risk-moderate hover:opacity-90 transition-all cursor-pointer" 
                  title={`Preventive: ${preventiveItem.count} (${preventiveItem.percentage}%)`} 
                />
                <div 
                  style={{ width: `${priorityItem.percentage}%` }} 
                  className="bg-risk-critical hover:opacity-90 transition-all cursor-pointer rounded-r-full" 
                  title={`Priority: ${priorityItem.count} (${priorityItem.percentage}%)`} 
                />
              </>
            ) : (
              <div className="w-full bg-surfaceHighlight" />
            )}
          </div>
        </div>

        {/* Tier list with counts & percentages */}
        <div className="space-y-3">
          <div className="p-2.5 bg-[#EEF6F2]/70 rounded-lg border border-[#BBD9C7] flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-risk-low" />
              <div>
                <span className="text-xs font-semibold text-textPrimary block">Routine Tier</span>
                <span className="text-[10px] text-textSecondary">Standard readiness & wellness</span>
              </div>
            </div>
            <div className="text-right">
              <span className="font-mono text-sm font-bold text-textPrimary">{routineItem.count}</span>
              <span className="text-[10px] text-textSecondary font-mono block">({routineItem.percentage}%)</span>
            </div>
          </div>

          <div className="p-2.5 bg-[#FDF6EE]/70 rounded-lg border border-[#F3D2AE] flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-risk-moderate" />
              <div>
                <span className="text-xs font-semibold text-textPrimary block">Preventive Tier</span>
                <span className="text-[10px] text-textSecondary">Active fatigue & roster monitoring</span>
              </div>
            </div>
            <div className="text-right">
              <span className="font-mono text-sm font-bold text-[#8E5B23]">{preventiveItem.count}</span>
              <span className="text-[10px] text-[#8E5B23]/80 font-mono block">({preventiveItem.percentage}%)</span>
            </div>
          </div>

          <div className="p-2.5 bg-[#FAF0F0] rounded-lg border border-[#E8B4B4] flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-risk-critical" />
              <div>
                <span className="text-xs font-semibold text-[#964747] block">Priority Tier</span>
                <span className="text-[10px] text-[#964747]/80">Urgent supportive welfare intervention</span>
              </div>
            </div>
            <div className="text-right">
              <span className="font-mono text-sm font-bold text-[#964747]">{priorityItem.count}</span>
              <span className="text-[10px] text-[#964747]/80 font-mono block">({priorityItem.percentage}%)</span>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-surfaceBorder text-[11px] text-textSecondary font-mono text-center">
        Thresholds: Routine (&lt;40) • Preventive (40-69) • Priority (≥70)
      </div>
    </div>
  );
}
