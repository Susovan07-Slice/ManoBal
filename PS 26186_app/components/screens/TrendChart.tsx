"use client";

import { TrendDay } from "@/types/trends";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export function TrendChart({ data }: { data: TrendDay[] }) {
  const formattedData = data.map(d => ({
    ...d,
    displayDate: d.date.split('-').slice(1).join('/')
  }));

  return (
    <div className="w-full h-[280px] bg-mb-glass-strong backdrop-blur-xl p-4 rounded-3xl shadow-[0_8px_30px_rgba(0,0,0,0.12)] border border-mb-glass-border relative overflow-hidden">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={formattedData} margin={{ top: 10, right: 5, left: -20, bottom: 5 }}>
          <XAxis 
            dataKey="displayDate" 
            stroke="#94a3b8" 
            fontSize={10}
            fontWeight={600}
            tickLine={false} 
            axisLine={false} 
            dy={10}
          />
          <YAxis 
            yAxisId="left" 
            stroke="#94a3b8" 
            fontSize={10} 
            tickLine={false} 
            axisLine={false}
            domain={[0, 100]}
            dx={-10}
          />
          <YAxis 
            yAxisId="right" 
            orientation="right" 
            stroke="#94a3b8" 
            fontSize={10} 
            tickLine={false} 
            axisLine={false}
            domain={[0, 12]}
            dx={10}
          />
          <Tooltip 
            contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.8)', backdropFilter: 'blur(12px)', border: '1px solid var(--color-glass-border)', borderRadius: '16px', color: '#fff', fontSize: '12px', fontWeight: '500' }}
            itemStyle={{ color: '#F1F5F9' }}
            cursor={{ stroke: 'rgba(255,255,255,0.1)', strokeWidth: 2 }}
          />
          <Line 
            yAxisId="left"
            type="monotone" 
            dataKey="stressIndex" 
            stroke="var(--color-saffron)" 
            strokeWidth={4}
            dot={false}
            activeDot={{ r: 6, fill: "var(--color-saffron)", strokeWidth: 0 }}
            name="Risk Score" 
          />
          <Line 
            yAxisId="right"
            type="monotone" 
            dataKey="sleepHours" 
            stroke="#2dd4bf" 
            strokeWidth={4}
            dot={false}
            activeDot={{ r: 6, fill: "#2dd4bf", strokeWidth: 0 }}
            name="Sleep (hrs)" 
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}


