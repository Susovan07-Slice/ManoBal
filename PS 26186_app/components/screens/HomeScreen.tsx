"use client";

import { DailyCheckIn } from "@/types/checkin";
import { PersonalTrend } from "@/types/trends";
import { TrendSummaryCard } from "./TrendSummaryCard";
import Link from "next/link";
import { CheckSquare, ClipboardList } from "lucide-react";
import { Card } from "@/components/ui/Card";

export function HomeScreen({ checkIns, trend }: { checkIns: DailyCheckIn[]; trend: PersonalTrend }) {
  const today = new Date().toISOString().split('T')[0];
  const hasCheckedInToday = checkIns.some(c => c.date === today);

  return (
    <div className="flex flex-col gap-6 animate-in fade-in duration-500 pb-20">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-slate-100">Welcome Back</h2>
      </div>

      <TrendSummaryCard trend={trend} />

      <div className="flex flex-col gap-4 mt-2">
        <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wider">Quick Actions</h3>
        
        <Link href="/check-in" className="block">
          <Card className="flex items-center justify-between p-4 hover:bg-slate-800/50 transition-colors cursor-pointer border-l-4 border-l-teal-500">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-teal-500/10 rounded-full flex items-center justify-center">
                <CheckSquare className="w-5 h-5 text-teal-400" />
              </div>
              <div>
                <p className="font-medium text-slate-100">Daily Check-In</p>
                <p className="text-sm text-slate-400">
                  {hasCheckedInToday ? "Completed today" : "Log your status"}
                </p>
              </div>
            </div>
            {!hasCheckedInToday && (
              <span className="bg-teal-500 text-slate-900 text-xs font-bold px-2 py-1 rounded-md">Due</span>
            )}
          </Card>
        </Link>

        <Link href="/assessment" className="block">
          <Card className="flex items-center justify-between p-4 hover:bg-slate-800/50 transition-colors cursor-pointer border-l-4 border-l-transparent">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-slate-700/50 rounded-full flex items-center justify-center">
                <ClipboardList className="w-5 h-5 text-slate-300" />
              </div>
              <div>
                <p className="font-medium text-slate-100">Self-Assessment</p>
                <p className="text-sm text-slate-400">Take a short survey</p>
              </div>
            </div>
          </Card>
        </Link>
      </div>
    </div>
  );
}
