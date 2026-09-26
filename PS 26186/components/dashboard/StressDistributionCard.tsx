'use client';

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { DistributionItem } from '@/types/api';
import { Activity, ShieldCheck, AlertCircle, ShieldAlert } from 'lucide-react';

interface StressDistributionCardProps {
  distribution: DistributionItem[];
  totalAssessed: number;
  isLoading?: boolean;
  error?: string | null;
}

export default function StressDistributionCard({
  distribution,
  totalAssessed,
  isLoading = false,
  error = null,
}: StressDistributionCardProps) {
  if (isLoading) {
    return (
      <div className="h-full w-full bg-surface border border-surfaceHighlight rounded-lg p-5 flex flex-col justify-center items-center min-h-[340px]">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin mb-3" />
        <span className="text-xs font-mono text-textSecondary uppercase tracking-widest">
          Loading Stress Telemetry...
        </span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full w-full bg-surface border border-red-900/40 rounded-lg p-5 flex flex-col justify-center items-center min-h-[340px] text-center">
        <AlertCircle className="w-8 h-8 text-rose-400 mb-2" />
        <p className="text-sm font-semibold text-rose-300">Stress Telemetry Unavailable</p>
        <p className="text-xs text-textSecondary mt-1 max-w-xs">{error}</p>
      </div>
    );
  }

  const lowItem = distribution.find((d) => d.label === 'Low') || { label: 'Low', count: 0, percentage: 0 };
  const medItem = distribution.find((d) => d.label === 'Medium') || { label: 'Medium', count: 0, percentage: 0 };
  const highItem = distribution.find((d) => d.label === 'High') || { label: 'High', count: 0, percentage: 0 };

  const chartData = [
    { name: 'Low Stress', count: lowItem.count, percentage: lowItem.percentage, color: '#10B981' },
    { name: 'Medium Stress', count: medItem.count, percentage: medItem.percentage, color: '#F59E0B' },
    { name: 'High Stress', count: highItem.count, percentage: highItem.percentage, color: '#F43F5E' },
  ];

  return (
    <div className="h-full w-full bg-surface border border-surfaceHighlight rounded-lg p-5 flex flex-col justify-between">
      <div>
        <div className="flex justify-between items-center mb-3">
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-accent" />
            <h3 className="text-sm uppercase tracking-wider font-semibold text-textPrimary">
              Operational Stress Distribution
            </h3>
          </div>
          <span className="text-xs font-mono text-accent bg-surfaceHighlight px-2.5 py-0.5 rounded">
            {totalAssessed} Assessed
          </span>
        </div>
        <p className="text-xs text-textSecondary mb-4">
          Real-time AI classified stress tiers across assessed active personnel.
        </p>

        {totalAssessed === 0 ? (
          <div className="h-48 flex flex-col items-center justify-center text-center text-textSecondary text-xs">
            <Activity className="w-8 h-8 text-surfaceHighlight mb-2" />
            <p>No stress assessments recorded in database.</p>
          </div>
        ) : (
          <>
            {/* Visual Recharts Bar Visualization */}
            <div className="h-44 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1A1F26" vertical={false} />
                  <XAxis
                    dataKey="name"
                    stroke="#9AA0A6"
                    fontSize={11}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    stroke="#9AA0A6"
                    fontSize={11}
                    tickLine={false}
                    axisLine={false}
                    allowDecimals={false}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0B0E11',
                      borderColor: '#1A1F26',
                      color: '#E8EAED',
                      borderRadius: '6px',
                      fontSize: '12px',
                    }}
                    formatter={(val: any, _name: any, item: any) => [
                      `${val} personnel (${item.payload.percentage}%)`,
                      'Count',
                    ]}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Metrics Breakdown Chips */}
            <div className="grid grid-cols-3 gap-2 mt-4 pt-3 border-t border-surfaceHighlight">
              <div className="p-2.5 bg-emerald-950/20 border border-emerald-900/30 rounded text-center">
                <div className="flex items-center justify-center space-x-1 mb-0.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-[11px] font-semibold text-emerald-400">Low</span>
                </div>
                <div className="text-base font-bold font-mono text-textPrimary">{lowItem.count}</div>
                <div className="text-[10px] text-textSecondary font-mono">{lowItem.percentage}%</div>
              </div>

              <div className="p-2.5 bg-amber-950/20 border border-amber-900/30 rounded text-center">
                <div className="flex items-center justify-center space-x-1 mb-0.5">
                  <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
                  <span className="text-[11px] font-semibold text-amber-400">Medium</span>
                </div>
                <div className="text-base font-bold font-mono text-textPrimary">{medItem.count}</div>
                <div className="text-[10px] text-textSecondary font-mono">{medItem.percentage}%</div>
              </div>

              <div className="p-2.5 bg-rose-950/20 border border-rose-900/30 rounded text-center">
                <div className="flex items-center justify-center space-x-1 mb-0.5">
                  <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                  <span className="text-[11px] font-semibold text-rose-400">High</span>
                </div>
                <div className="text-base font-bold font-mono text-rose-400">{highItem.count}</div>
                <div className="text-[10px] text-rose-300/80 font-mono">{highItem.percentage}%</div>
              </div>
            </div>
          </>
        )}
      </div>

      <div className="mt-4 pt-3 border-t border-surfaceHighlight text-[11px] text-textSecondary font-mono flex items-center justify-between">
        <span>Model: LightGBM Multiclass</span>
        <span>Decision-Support Metric</span>
      </div>
    </div>
  );
}
