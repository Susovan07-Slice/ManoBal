'use client';

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell
} from 'recharts';
import { DistributionItem } from '@/types/api';

interface RiskTrendChartProps {
  stressDistribution: DistributionItem[];
  riskDistribution: DistributionItem[];
  isLoading?: boolean;
}

export default function RiskTrendChart({
  stressDistribution,
  riskDistribution,
  isLoading = false
}: RiskTrendChartProps) {
  if (isLoading) {
    return (
      <div className="h-full w-full bg-surface border border-surfaceHighlight rounded p-4 flex flex-col justify-center items-center">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin mb-2" />
        <span className="text-xs font-mono text-textSecondary uppercase tracking-widest">
          Loading Stress Telemetry...
        </span>
      </div>
    );
  }

  // Combine distributions for comparative visualization
  const data = [
    {
      category: 'Low / Routine',
      stressCount: stressDistribution.find(d => d.label === 'Low')?.count || 0,
      riskCount: riskDistribution.find(d => d.label === 'Routine')?.count || 0,
      stressPct: stressDistribution.find(d => d.label === 'Low')?.percentage || 0,
    },
    {
      category: 'Medium / Preventive',
      stressCount: stressDistribution.find(d => d.label === 'Medium')?.count || 0,
      riskCount: riskDistribution.find(d => d.label === 'Preventive')?.count || 0,
      stressPct: stressDistribution.find(d => d.label === 'Medium')?.percentage || 0,
    },
    {
      category: 'High / Priority',
      stressCount: stressDistribution.find(d => d.label === 'High')?.count || 0,
      riskCount: riskDistribution.find(d => d.label === 'Priority')?.count || 0,
      stressPct: stressDistribution.find(d => d.label === 'High')?.percentage || 0,
    },
  ];

  return (
    <div className="h-full w-full bg-surface border-military p-4 flex flex-col">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-sm uppercase tracking-widest font-semibold text-textSecondary">
          Force Stress & Intervention Distribution
        </h3>
        <span className="text-xs font-mono text-accent bg-surfaceHighlight px-2 py-0.5 rounded">
          Live Backend Telemetry
        </span>
      </div>
      
      <div className="flex-1 min-h-[250px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 20, left: -10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1A1F26" vertical={false} />
            <XAxis dataKey="category" stroke="#9AA0A6" fontSize={12} tickLine={false} axisLine={false} tickMargin={10} />
            <YAxis stroke="#9AA0A6" fontSize={12} tickLine={false} axisLine={false} tickMargin={10} allowDecimals={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0B0E11',
                borderColor: '#1A1F26',
                color: '#E8EAED',
                borderRadius: '4px',
                fontSize: '12px'
              }}
              formatter={(value: any, name: any) => [
                `${value} personnel`,
                name === 'stressCount' ? 'Stress Level Count' : 'Risk Priority Count'
              ]}
            />
            <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
            <Bar dataKey="stressCount" name="Predicted Stress Level" fill="#4A6D8C" radius={[4, 4, 0, 0]} />
            <Bar dataKey="riskCount" name="Operational Welfare Priority" fill="#F59E0B" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
