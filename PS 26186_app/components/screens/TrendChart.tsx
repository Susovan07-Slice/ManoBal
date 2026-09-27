"use client";

import { TrendDay } from "@/types/trends";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export function TrendChart({ data }: { data: TrendDay[] }) {
  const formattedData = data.map(d => ({
    ...d,
    displayDate: d.date.split('-').slice(1).join('/')
  }));

  return (
    <div className="w-full h-full relative">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={formattedData} margin={{ top: 15, right: 10, left: -25, bottom: 5 }}>
          <XAxis 
            dataKey="displayDate" 
            stroke="rgba(255,255,255,0.4)" 
            fontSize={11}
            fontWeight={500}
            tickLine={false} 
            axisLine={false} 
            dy={15}
          />
          <YAxis 
            yAxisId="left" 
            stroke="rgba(255,255,255,0.4)" 
            fontSize={11}
            fontWeight={500}
            tickLine={false} 
            axisLine={false}
            domain={[0, 100]}
            dx={-10}
          />
          <YAxis 
            yAxisId="right" 
            orientation="right" 
            stroke="rgba(255,255,255,0.4)" 
            fontSize={11}
            fontWeight={500}
            tickLine={false} 
            axisLine={false}
            domain={[0, 12]}
            dx={10}
          />
          <Tooltip 
            contentStyle={{ backgroundColor: 'rgba(10, 17, 14, 0.85)', backdropFilter: 'blur(16px)', border: '1px solid rgba(255,255,255,0.15)', borderRadius: '16px', color: '#fff', fontSize: '12px', fontWeight: '500', boxShadow: '0 8px 32px rgba(0,0,0,0.4)' }}
            itemStyle={{ color: '#F5F5F0' }}
            cursor={{ stroke: 'rgba(255,255,255,0.15)', strokeWidth: 2 }}
          />
          <Line 
            yAxisId="left"
            type="monotone" 
            dataKey="stressIndex" 
            stroke="#D98A2B" 
            strokeWidth={3}
            dot={false}
            activeDot={{ r: 6, fill: "#D98A2B", strokeWidth: 0, shadow: '0 0 10px #D98A2B' }}
            name="Risk Score" 
          />
          <Line 
            yAxisId="right"
            type="monotone" 
            dataKey="sleepHours" 
            stroke="#00A896" 
            strokeWidth={3}
            dot={false}
            activeDot={{ r: 6, fill: "#00A896", strokeWidth: 0, shadow: '0 0 10px #00A896' }}
            name="Sleep (hrs)" 
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}


