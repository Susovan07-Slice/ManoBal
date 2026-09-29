"use client";

import { TrendDay } from "@/types/trends";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, Legend } from "recharts";

export function TrendChart({ data }: { data: TrendDay[] }) {
  const formattedData = data.map(d => ({
    ...d,
    displayDate: d.date.split('-').slice(1).join('/')
  }));

  return (
    <div className="w-full h-full relative min-w-0">
      <ResponsiveContainer width="100%" height="100%" minWidth={0}>
        <LineChart data={formattedData} margin={{ top: 15, right: 10, left: -25, bottom: 5 }}>
          <defs>
            <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#2A9BC8" stopOpacity={0.12} />
              <stop offset="100%" stopColor="#2A9BC8" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid 
            strokeDasharray="4 4"
            stroke="#C9DCE5"
            vertical={false}
          />
          <XAxis 
            dataKey="displayDate" 
            stroke="#8AA1AF" 
            fontSize={11}
            fontWeight={500}
            tickLine={false} 
            axisLine={false} 
            dy={15}
          />
          <YAxis 
            yAxisId="left" 
            stroke="#8AA1AF" 
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
            stroke="#8AA1AF" 
            fontSize={11}
            fontWeight={500}
            tickLine={false} 
            axisLine={false}
            domain={[0, 12]}
            dx={10}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#ffffff', 
              backdropFilter: 'blur(16px)', 
              border: '1px solid rgba(191,227,240,0.6)', 
              borderRadius: '16px', 
              color: '#14232E', 
              fontSize: '12px', 
              fontWeight: '500', 
              boxShadow: '0 10px 30px rgba(31,110,140,0.12)',
              padding: '10px 14px',
            }}
            itemStyle={{ color: '#4B6272' }}
            cursor={{ stroke: '#BFE3F0', strokeWidth: 2 }}
          />
          <Legend 
            iconType="circle"
            iconSize={8}
            wrapperStyle={{ fontSize: '11px', color: '#4B6272', paddingTop: '8px' }}
          />
          <Area
            yAxisId="left"
            type="monotone"
            dataKey="stressIndex"
            fill="url(#areaGradient)"
            stroke="none"
          />
          <Line 
            yAxisId="left"
            type="monotone" 
            dataKey="stressIndex" 
            stroke="#2A9BC8" 
            strokeWidth={3}
            dot={{ r: 5, fill: "#2A9BC8", strokeWidth: 0, filter: "drop-shadow(0 0 4px rgba(42,155,200,0.3))" }}
            activeDot={{ r: 7, fill: "#2A9BC8", strokeWidth: 3, stroke: "#fff", filter: "drop-shadow(0 0 8px rgba(42,155,200,0.4))" }}
            name="Risk Score" 
          />
          <Line 
            yAxisId="right"
            type="monotone" 
            dataKey="sleepHours" 
            stroke="#F0508C" 
            strokeWidth={3}
            dot={{ r: 5, fill: "#F0508C", strokeWidth: 0, filter: "drop-shadow(0 0 4px rgba(240,80,140,0.3))" }}
            activeDot={{ r: 7, fill: "#F0508C", strokeWidth: 3, stroke: "#fff", filter: "drop-shadow(0 0 8px rgba(240,80,140,0.4))" }}
            name="Sleep (hrs)" 
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
