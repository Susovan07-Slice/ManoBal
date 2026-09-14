"use client";

import { useEffect, useState } from "react";
import { HomeScreen } from "@/components/screens/HomeScreen";
import { getRecentCheckIns, getPersonalTrend } from "@/lib/mock-data";
import { DailyCheckIn } from "@/types/checkin";
import { PersonalTrend } from "@/types/trends";

export default function HomeRoute() {
  const [data, setData] = useState<{ checkIns: DailyCheckIn[], trend: PersonalTrend } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getRecentCheckIns(), getPersonalTrend()]).then(([checkIns, trend]) => {
      setData({ checkIns, trend });
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col h-full items-center justify-center text-slate-400 p-4">
        <div className="w-8 h-8 border-2 border-teal-500 border-t-transparent rounded-full animate-spin mb-4" />
        <p>Loading dashboard...</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex flex-col h-full items-center justify-center text-slate-400 p-4 text-center">
        <p>Could not load data.</p>
      </div>
    );
  }

  return (
    <div className="p-4 h-full">
      <HomeScreen checkIns={data.checkIns} trend={data.trend} />
    </div>
  );
}
