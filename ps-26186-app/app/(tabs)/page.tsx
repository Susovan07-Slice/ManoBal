"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { HomeScreen } from "@/components/screens/HomeScreen";
import { useAuth } from "@/lib/AuthContext";
import { getAssessmentHistory, getAssessmentScheduleStatus } from "@/lib/assessment";
import { getMyWelfareRequests } from "@/lib/welfare";
import { computePersonalTrend } from "@/lib/trends";
import { PersonalTrend } from "@/types/trends";
import { StressAssessmentOut, AssessmentScheduleStatus, WelfareRequestOut } from "@/types/api";
import { ShieldAlert, RefreshCw } from "lucide-react";
import { useRouter } from "next/navigation";

export default function HomeRoute() {
  const { user } = useAuth();
  const router = useRouter();
  const personnelId = user?.personnel_id ?? null;

  const [trend, setTrend] = useState<PersonalTrend | null>(null);
  const [latestAssessment, setLatestAssessment] = useState<StressAssessmentOut | null>(null);
  const [scheduleStatus, setScheduleStatus] = useState<AssessmentScheduleStatus | null>(null);
  const [welfareRequests, setWelfareRequests] = useState<WelfareRequestOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const autoRedirectedRef = useRef(false);

  const loadHomeData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      if (personnelId) {
        // Fetch server-authoritative 24-hour schedule status, assessment history & welfare requests
        const [statusRes, historyRes, welfareRes] = await Promise.all([
          getAssessmentScheduleStatus(personnelId).catch((err) => {
            console.warn("Could not retrieve schedule status:", err);
            return null;
          }),
          getAssessmentHistory(personnelId).catch((err) => {
            console.warn("Could not retrieve assessment history:", err);
            return [];
          }),
          getMyWelfareRequests().catch((err) => {
            console.warn("Could not retrieve welfare requests:", err);
            return [];
          }),
        ]);

        setScheduleStatus(statusRes);
        setWelfareRequests(welfareRes || []);

        const assessments = historyRes || [];
        if (assessments.length > 0) {
          setLatestAssessment(assessments[0]);
        } else {
          setLatestAssessment(null);
        }

        const computed = computePersonalTrend(assessments);
        setTrend(computed);

        // Server-backed 24-hour assessment rule (Sections 6, 7, 8, 9, 10)
        if (statusRes && statusRes.assessment_due && !autoRedirectedRef.current) {
          const sessionDismissed = sessionStorage.getItem(`assessment_dismissed_${personnelId}`);
          if (!sessionDismissed) {
            autoRedirectedRef.current = true;
            sessionStorage.setItem(`assessment_dismissed_${personnelId}`, 'true');
            router.push(
              !statusRes.has_assessment
                ? "/assessment?reason=initial"
                : "/assessment?reason=due_24h"
            );
            return;
          }
        }
      } else {
        setLatestAssessment(null);
        setScheduleStatus(null);
        setTrend({
          last7Days: [],
          averageStressIndex: 0,
          averageSleepHours: 0,
          trendDirection: "stable",
        });
      }
    } catch (err: any) {
      console.error("Failed to load home dashboard telemetry:", err);
      setError(err?.message || "Failed to load dashboard data");
      setTrend({
        last7Days: [],
        averageStressIndex: 0,
        averageSleepHours: 0,
        trendDirection: "stable",
      });
    } finally {
      setLoading(false);
    }
  }, [personnelId, router]);

  useEffect(() => {
    loadHomeData();

    const handleRefresh = () => {
      loadHomeData();
    };

    if (typeof window !== 'undefined') {
      window.addEventListener('manobal:welfare_created', handleRefresh);
      window.addEventListener('manobal:assessment_completed', handleRefresh);
      window.addEventListener('focus', handleRefresh);
    }
    return () => {
      if (typeof window !== 'undefined') {
        window.removeEventListener('manobal:welfare_created', handleRefresh);
        window.removeEventListener('manobal:assessment_completed', handleRefresh);
        window.removeEventListener('focus', handleRefresh);
      }
    };
  }, [loadHomeData]);

  if (loading) {
    return (
      <div className="flex flex-col gap-6 pb-32 px-4 max-w-[420px] mx-auto w-full pt-6 animate-pulse">
        {/* Skeleton greeting */}
        <div className="h-8 w-48 bg-white/15 rounded-xl" />
        {/* Skeleton hero card */}
        <div className="h-56 bg-white/10 rounded-3xl" />
        {/* Skeleton metrics row */}
        <div className="grid grid-cols-3 gap-2.5">
          <div className="h-20 bg-white/10 rounded-2xl" />
          <div className="h-20 bg-white/10 rounded-2xl" />
          <div className="h-20 bg-white/10 rounded-2xl" />
        </div>
        {/* Skeleton chart */}
        <div className="h-[220px] bg-white/10 rounded-2xl" />
        {/* Skeleton assessment card */}
        <div className="h-32 bg-white/10 rounded-2xl" />
      </div>
    );
  }

  if (error && !trend) {
    return (
      <div className="flex flex-col h-full items-center justify-center text-mb-text-secondary p-6 text-center">
        <p className="text-sm text-mb-text-secondary mb-2">Could not synchronize dashboard telemetry.</p>
        <button
          onClick={loadHomeData}
          className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 text-mb-accent text-xs rounded-lg hover:bg-slate-700 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Retry
        </button>
      </div>
    );
  }

  return (
    <div className="p-4 h-full flex flex-col justify-between">
      <div>
        <HomeScreen
          username={user?.username}
          latestAssessment={latestAssessment}
          scheduleStatus={scheduleStatus}
          trend={
            trend || {
              last7Days: [],
              averageStressIndex: 0,
              averageSleepHours: 0,
              trendDirection: "stable",
            }
          }
          welfareRequests={welfareRequests}
          onRefresh={loadHomeData}
        />
      </div>

    </div>
  );
}


