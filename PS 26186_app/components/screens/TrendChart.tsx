"use client";

import { TrendDay } from "@/types/trends";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export function TrendChart({ data }: { data: TrendDay[] }) {
  const formattedData = data.map(d => ({
    ...d,
    displayDate: d.date.split('-').slice(1).join('/')
  }));

  return (
    <div className="w-full h-[240px] bg-[#1C2530] p-4 rounded-2xl shadow-lg border border-slate-800/50">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={formattedData} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
          <XAxis 
            dataKey="displayDate" 
            stroke="#94a3b8" 
            fontSize={12} 
            tickLine={false} 
            axisLine={false} 
          />
          <YAxis 
            yAxisId="left" 
            stroke="#94a3b8" 
            fontSize={12} 
            tickLine={false} 
            axisLine={false}
            domain={[0, 100]}
          />
          <YAxis 
            yAxisId="right" 
            orientation="right" 
            stroke="#94a3b8" 
            fontSize={12} 
            tickLine={false} 
            axisLine={false}
            domain={[0, 12]}
          />
          <Tooltip 
            contentStyle={{ backgroundColor: '#0F172A', border: '1px solid #1E293B', borderRadius: '8px' }}
            itemStyle={{ color: '#F1F5F9' }}
          />
          <Line 
            yAxisId="left"
            type="monotone" 
            dataKey="stressIndex" 
            stroke="#F43F5E" 
            strokeWidth={3}
            dot={{ r: 4, fill: "#F43F5E", strokeWidth: 0 }}
            name="Stress" 
          />
          <Line 
            yAxisId="right"
            type="monotone" 
            dataKey="sleepHours" 
            stroke="#0EA5E9" 
            strokeWidth={3}
            dot={{ r: 4, fill: "#0EA5E9", strokeWidth: 0 }}
            name="Sleep (hrs)" 
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
