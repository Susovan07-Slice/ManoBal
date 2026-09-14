import React from 'react';
import { UnitAggregates } from '@/types/dashboard';

export default function UnitOverviewPanel({ aggregates }: { aggregates: UnitAggregates[] }) {
  return (
    <div className="h-full w-full bg-surface border-military p-4 flex flex-col">
      <h3 className="text-sm uppercase tracking-widest font-semibold text-textSecondary mb-4">Unit Risk Distribution</h3>
      <div className="flex-1 overflow-y-auto space-y-4 pr-2 custom-scrollbar">
        {aggregates.map(unit => {
          const total = unit.riskDistribution.low + unit.riskDistribution.moderate + unit.riskDistribution.high + unit.riskDistribution.critical;
          return (
            <div key={unit.unitId} className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="font-mono text-textPrimary">{unit.unitId}</span>
                <span className="text-textSecondary">{total} personnel</span>
              </div>
              <div className="h-2.5 w-full flex rounded-sm overflow-hidden bg-surfaceHighlight">
                {total > 0 && (
                  <>
                    <div style={{ width: `${(unit.riskDistribution.low / total) * 100}%` }} className="bg-risk-low hover:brightness-110 transition-all cursor-crosshair" title={`Low: ${unit.riskDistribution.low}`} />
                    <div style={{ width: `${(unit.riskDistribution.moderate / total) * 100}%` }} className="bg-risk-moderate hover:brightness-110 transition-all cursor-crosshair" title={`Moderate: ${unit.riskDistribution.moderate}`} />
                    <div style={{ width: `${(unit.riskDistribution.high / total) * 100}%` }} className="bg-risk-high hover:brightness-110 transition-all cursor-crosshair" title={`High: ${unit.riskDistribution.high}`} />
                    <div style={{ width: `${(unit.riskDistribution.critical / total) * 100}%` }} className="bg-risk-critical hover:brightness-110 transition-all cursor-crosshair" title={`Critical: ${unit.riskDistribution.critical}`} />
                  </>
                )}
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-4 pt-4 border-t border-surfaceHighlight flex gap-4 text-[11px] uppercase font-semibold tracking-wider text-textSecondary justify-center">
        <span className="flex items-center"><span className="w-2.5 h-2.5 rounded-sm bg-risk-low mr-1.5" /> Low</span>
        <span className="flex items-center"><span className="w-2.5 h-2.5 rounded-sm bg-risk-moderate mr-1.5" /> Mod</span>
        <span className="flex items-center"><span className="w-2.5 h-2.5 rounded-sm bg-risk-high mr-1.5" /> High</span>
        <span className="flex items-center"><span className="w-2.5 h-2.5 rounded-sm bg-risk-critical mr-1.5" /> Crit</span>
      </div>
    </div>
  );
}
