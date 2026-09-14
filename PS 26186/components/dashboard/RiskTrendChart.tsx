'use client';

import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendPoint } from '@/types/dashboard';

export default function RiskTrendChart({ trend, unitName }: { trend: TrendPoint[], unitName: string }) {
  return (
    <div className="h-full w-full bg-surface border-military p-4 flex flex-col">
      <h3 className="text-sm uppercase tracking-widest font-semibold text-textSecondary mb-4">Risk Trend — {unitName}</h3>
      <div className="flex-1 min-h-[250px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={trend} margin={{ top: 5, right: 20, left: -20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1A1F26" vertical={false} />
            <XAxis dataKey="date" stroke="#9AA0A6" fontSize={12} tickLine={false} axisLine={false} tickMargin={10} />
            <YAxis yAxisId="left" stroke="#9AA0A6" fontSize={12} tickLine={false} axisLine={false} tickMargin={10} />
            <YAxis yAxisId="right" orientation="right" stroke="#9AA0A6" fontSize={12} tickLine={false} axisLine={false} tickMargin={10} />
            <Tooltip 
              contentStyle={{ backgroundColor: '#0B0E11', borderColor: '#1A1F26', color: '#E8EAED', borderRadius: '4px' }}
              itemStyle={{ color: '#E8EAED', fontSize: '14px' }}
              labelStyle={{ color: '#9AA0A6', marginBottom: '4px' }}
            />
            <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
            <Line yAxisId="left" type="monotone" dataKey="avgWorkloadScore" name="Avg Workload (0-10)" stroke="#4A6D8C" strokeWidth={2} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} />
            <Line yAxisId="right" type="monotone" dataKey="avgStressIndex" name="Avg Stress Index (0-100)" stroke="#F59E0B" strokeWidth={2} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
