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
      <div className="h-full w-full bg-surface border border-surfaceBorder rounded-xl p-5 flex flex-col justify-center items-center min-h-[340px] shadow-card">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin mb-3" />
        <span className="text-xs font-mono text-textSecondary uppercase tracking-widest">
          Loading Stress Telemetry...
        </span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full w-full bg-surface border border-[#E8B4B4] rounded-xl p-5 flex flex-col justify-center items-center min-h-[340px] text-center shadow-card">
        <AlertCircle className="w-8 h-8 text-[#C26D6D] mb-2" />
        <p className="text-sm font-semibold text-[#964747]">Stress Telemetry Unavailable</p>
        <p className="text-xs text-textSecondary mt-1 max-w-xs">{error}</p>
      </div>
    );
  }

  const lowItem = distribution.find((d) => d.label === 'Low') || { label: 'Low', count: 0, percentage: 0 };
  const medItem = distribution.find((d) => d.label === 'Medium') || { label: 'Medium', count: 0, percentage: 0 };
  const highItem = distribution.find((d) => d.label === 'High') || { label: 'High', count: 0, percentage: 0 };

  const chartData = [
    { name: 'Low Stress', count: lowItem.count, percentage: lowItem.percentage, color: '#7BA083' },
    { name: 'Medium Stress', count: medItem.count, percentage: medItem.percentage, color: '#D99B5C' },
    { name: 'High Stress', count: highItem.count, percentage: highItem.percentage, color: '#C26D6D' },
  ];

  return (
    <div className="h-full w-full bg-surface border border-surfaceBorder rounded-xl p-5 flex flex-col justify-between shadow-card">
      <div>
        <div className="flex justify-between items-center mb-3">
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-accent" />
            <h3 className="text-sm uppercase tracking-wider font-semibold text-textPrimary">
              Operational Stress Distribution
            </h3>
          </div>
          <span className="text-xs font-mono text-accent bg-accent/10 border border-accent/25 px-2.5 py-0.5 rounded-md font-semibold">
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
                  <CartesianGrid strokeDasharray="3 3" stroke="#E8F0EC" vertical={false} />
                  <XAxis
                    dataKey="name"
                    stroke="#64748B"
                    fontSize={11}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    stroke="#64748B"
                    fontSize={11}
                    tickLine={false}
                    axisLine={false}
                    allowDecimals={false}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#FAFAFC',
                      borderColor: '#D5E2D9',
                      color: '#2D3748',
                      borderRadius: '8px',
                      fontSize: '12px',
                      boxShadow: '0 4px 12px rgba(45, 55, 72, 0.08)',
                    }}
                    formatter={(val: any, _name: any, item: any) => [
                      `${val} personnel (${item.payload.percentage}%)`,
                      'Count',
                    ]}
                  />
                  <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Metrics Breakdown Chips */}
            <div className="grid grid-cols-3 gap-2 mt-4 pt-3 border-t border-surfaceHighlight">
              <div className="p-2.5 bg-[#EEF6F2] border border-[#BBD9C7] rounded-lg text-center">
                <div className="flex items-center justify-center space-x-1 mb-0.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-[#2D6346]" />
                  <span className="text-[11px] font-semibold text-[#2D6346]">Low</span>
                </div>
                <div className="text-base font-bold font-mono text-textPrimary">{lowItem.count}</div>
                <div className="text-[10px] text-textSecondary font-mono">{lowItem.percentage}%</div>
              </div>

              <div className="p-2.5 bg-[#FDF6EE] border border-[#F3D2AE] rounded-lg text-center">
                <div className="flex items-center justify-center space-x-1 mb-0.5">
                  <AlertCircle className="w-3.5 h-3.5 text-[#8E5B23]" />
                  <span className="text-[11px] font-semibold text-[#8E5B23]">Medium</span>
                </div>
                <div className="text-base font-bold font-mono text-textPrimary">{medItem.count}</div>
                <div className="text-[10px] text-textSecondary font-mono">{medItem.percentage}%</div>
              </div>

              <div className="p-2.5 bg-[#FAF0F0] border border-[#E8B4B4] rounded-lg text-center">
                <div className="flex items-center justify-center space-x-1 mb-0.5">
                  <ShieldAlert className="w-3.5 h-3.5 text-[#964747]" />
                  <span className="text-[11px] font-semibold text-[#964747]">High</span>
                </div>
                <div className="text-base font-bold font-mono text-[#964747]">{highItem.count}</div>
                <div className="text-[10px] text-[#964747]/80 font-mono">{highItem.percentage}%</div>
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
